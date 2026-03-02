"""
Scheduling System for Silver Tier Functional Assistant

Provides cron-style scheduling using Windows Task Scheduler
"""

import json
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any
import schedule
import time
import logging
from pathlib import Path


class WindowsTaskScheduler:
    """Windows Task Scheduler wrapper for Python scheduling"""

    def __init__(self, task_name: str, description: str = "Silver Tier Scheduling Task"):
        self.task_name = task_name
        self.description = description
        self.task_path = f'\\{self.task_name}'

    def create_task(self, script_path: str, schedule_time: str, frequency: str = "DAILY"):
        """
        Create a Windows Task Scheduler task

        Args:
            script_path: Path to the Python script to execute
            schedule_time: Time in HH:MM format (24-hour)
            frequency: DAILY, WEEKLY, MONTHLY
        """
        # Build the command to create a task
        command = [
            'schtasks',
            '/CREATE',
            '/TN', self.task_path,
            '/TR', f'"python {script_path}"',
            '/SC', frequency,
            '/ST', schedule_time,
            '/RU', 'SYSTEM',
            '/RL', 'HIGHEST',
            '/F',
            '/DESCRIPTION', f'"{self.description}"'
        ]

        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info(f"Task {self.task_name} created successfully")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to create task {self.task_name}: {e.stderr}")
            return False

    def delete_task(self):
        """Delete the task from Windows Task Scheduler"""
        command = ['schtasks', '/DELETE', '/TN', self.task_path, '/F']
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info(f"Task {self.task_name} deleted successfully")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to delete task {self.task_name}: {e.stderr}")
            return False

    def run_task(self):
        """Run the task immediately"""
        command = ['schtasks', '/RUN', '/TN', self.task_path]
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            logging.info(f"Task {self.task_name} started successfully")
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to start task {self.task_name}: {e.stderr}")
            return False

    def query_task(self):
        """Query task status"""
        command = ['schtasks', '/QUERY', '/TN', self.task_path, '/FO', 'LIST']
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to query task {self.task_name}: {e.stderr}")
            return None


class SchedulingSystem:
    """Main scheduling system for Silver Tier functional assistant"""

    def __init__(self, config_path: str = "scheduling/config.json"):
        self.config_path = config_path
        self.tasks = []
        self.load_config()
        self.logger = self.setup_logger()
        self._init_schedule()

    def setup_logger(self):
        """Setup logging for the scheduling system"""
        logger = logging.getLogger('silver_tier_scheduler')
        logger.setLevel(logging.INFO)

        # Create log directory if it doesn't exist
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        # File handler
        file_handler = logging.FileHandler(log_dir / 'scheduler.log')
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def load_config(self):
        """Load scheduling configuration"""
        if not os.path.exists(self.config_path):
            self.logger.warning(f"Configuration file {self.config_path} not found, using defaults")
            self.config = self.get_default_config()
        else:
            with open(self.config_path, 'r') as f:
                self.config = json.load(f)
            self.logger.info(f"Configuration loaded from {self.config_path}")

    def get_default_config(self) -> Dict[str, Any]:
        """Get default scheduling configuration"""
        return {
            "tasks": [],
            "log_level": "INFO",
            "log_file": "logs/scheduler.log",
            "retry_attempts": 3,
            "retry_delay": 60  # seconds
        }

    def add_task(self, task_name: str, script_path: str, schedule_time: str,
                 frequency: str = "DAILY", enabled: bool = True):
        """Add a new task to the scheduling system"""
        task = {
            "name": task_name,
            "script_path": script_path,
            "schedule_time": schedule_time,
            "frequency": frequency,
            "enabled": enabled,
            "last_run": None,
            "next_run": None
        }
        self.tasks.append(task)
        self.logger.info(f"Added task: {task_name}")
        return task

    def remove_task(self, task_name: str):
        """Remove a task from the scheduling system"""
        self.tasks = [task for task in self.tasks if task['name'] != task_name]
        self.logger.info(f"Removed task: {task_name}")

    def _init_schedule(self):
        """Initialize the schedule library with tasks"""
        for task in self.tasks:
            if task['enabled']:
                self._schedule_task(task)

    def _schedule_task(self, task: Dict):
        """Schedule a single task"""
        try:
            # Parse the schedule time
            schedule_time = datetime.strptime(task['schedule_time'], '%H:%M')
            now = datetime.now()

            # Calculate next run time
            next_run = datetime(now.year, now.month, now.day, schedule_time.hour, schedule_time.minute)
            if next_run < now:
                next_run += timedelta(days=1)

            task['next_run'] = next_run.strftime('%Y-%m-%d %H:%M:%S')

            # Schedule the task
            if task['frequency'] == 'DAILY':
                schedule.every().day.at(task['schedule_time']).do(self._run_task, task)
            elif task['frequency'] == 'WEEKLY':
                schedule.every().week.at(task['schedule_time']).do(self._run_task, task)
            elif task['frequency'] == 'MONTHLY':
                schedule.every().month.at(task['schedule_time']).do(self._run_task, task)

            self.logger.info(f"Task {task['name']} scheduled for {task['next_run']}")
        except Exception as e:
            self.logger.error(f"Failed to schedule task {task['name']}: {str(e)}")

    def _run_task(self, task: Dict):
        """Execute a scheduled task"""
        self.logger.info(f"Running task: {task['name']}")
        task['last_run'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Update next run time
        next_run = datetime.strptime(task['next_run'], '%Y-%m-%d %H:%M:%S')
        if task['frequency'] == 'DAILY':
            next_run += timedelta(days=1)
        elif task['frequency'] == 'WEEKLY':
            next_run += timedelta(weeks=1)
        elif task['frequency'] == 'MONTHLY':
            next_run += timedelta(days=30)  # Approximate monthly

        task['next_run'] = next_run.strftime('%Y-%m-%d %H:%M:%S')

        # Execute the task
        try:
            if os.path.exists(task['script_path']):
                result = subprocess.run(["python", task['script_path']],
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    self.logger.info(f"Task {task['name']} completed successfully")
                else:
                    self.logger.error(f"Task {task['name']} failed: {result.stderr}")
            else:
                self.logger.error(f"Task script not found: {task['script_path']}")
        except Exception as e:
            self.logger.error(f"Error running task {task['name']}: {str(e)}")

    def run(self):
        """Start the scheduling system"""
        self.logger.info("Starting Silver Tier Scheduling System")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Scheduling system stopped")
        except Exception as e:
            self.logger.error(f"Scheduling system error: {str(e)}")
            raise


def main():
    """Main entry point for the scheduling system"""
    # Create scheduler instance
    scheduler = SchedulingSystem()

    # Add some example tasks
    scheduler.add_task(
        "Business Audit Report",
        "scheduling/tasks/business_audit.py",
        "02:00",
        "DAILY"
    )

    scheduler.add_task(
        "Dashboard Update",
        "scheduling/tasks/dashboard_update.py",
        "03:00",
        "DAILY"
    )

    scheduler.add_task(
        "System Health Check",
        "scheduling/tasks/system_health_check.py",
        "04:00",
        "DAILY"
    )

    scheduler.add_task(
        "Weekly Summary Report",
        "scheduling/tasks/weekly_summary.py",
        "23:59",
        "WEEKLY"
    )

    # Save the configuration
    with open("scheduling/config.json", "w") as f:
        json.dump(scheduler.config, f, indent=2)

    # Start the scheduler
    scheduler.run()


if __name__ == "__main__":
    main()