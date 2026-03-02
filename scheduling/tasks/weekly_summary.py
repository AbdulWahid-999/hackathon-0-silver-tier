"""
Weekly Summary Task

Generates weekly summary reports for the Silver Tier functional assistant
"""

import os
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path


class WeeklySummaryGenerator:
    """Weekly summary report generator"""

    def __init__(self, config: dict = None):
        self.config = config or self.get_default_config()
        self.logger = self.setup_logger()
        self.data_dir = Path(self.config.get("data_dir", "data"))
        self.reports_dir = Path(self.config.get("reports_dir", "reports/weekly"))
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def setup_logger(self):
        """Setup logger for weekly summary generator"""
        logger = logging.getLogger('weekly_summary')
        logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.reports_dir / "weekly_summary.log")
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

    def get_default_config(self) -> dict:
        """Get default configuration for weekly summary generator"""
        return {
            "data_dir": "data",
            "reports_dir": "reports/weekly",
            "include_business_metrics": True,
            "include_system_metrics": True,
            "include_user_activity": True,
            "include_performance_trends": True,
            "email_recipients": ["admin@silver-tier.com"],
            "week_start": "Monday"
        }

    def collect_weekly_data(self) -> dict:
        """Collect data from the past week"""
        self.logger.info("Collecting weekly data")
        weekly_data = {}

        # Calculate date range
        today = datetime.now()
        days_in_week = 7

        if self.config.get("week_start") == "Monday":
            days_in_week = today.weekday() + 1  # Days since Monday

        start_date = today - timedelta(days=days_in_week)
        end_date = today

        self.logger.info(f"Collecting data from {start_date} to {end_date}")

        # Business metrics
        if self.config.get("include_business_metrics"):
            business_metrics = self._collect_business_metrics(start_date, end_date)
            weekly_data["business_metrics"] = business_metrics

        # System metrics
        if self.config.get("include_system_metrics"):
            system_metrics = self._collect_system_metrics(start_date, end_date)
            weekly_data["system_metrics"] = system_metrics

        # User activity
        if self.config.get("include_user_activity"):
            user_activity = self._collect_user_activity(start_date, end_date)
            weekly_data["user_activity"] = user_activity

        # Performance trends
        if self.config.get("include_performance_trends"):
            performance_trends = self._collect_performance_trends(start_date, end_date)
            weekly_data["performance_trends"] = performance_trends

        weekly_data["date_range"] = {
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "days_covered": days_in_week
        }

        self.logger.info(f"Weekly data collected: {list(weekly_data.keys())}")
        return weekly_data

    def _collect_business_metrics(self, start_date: datetime, end_date: datetime) -> dict:
        """Collect business metrics from the past week"""
        business_data = {}

        # Activity logs
        activity_files = list(self.data_dir.glob("activity_*.json"))
        weekly_activities = []
        weekly_counts = {}

        for file in activity_files:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                activities = data.get("activities", [])

                for activity in activities:
                    activity_date = datetime.fromisoformat(activity.get("timestamp", ""))
                    if start_date <= activity_date <= end_date:
                        weekly_activities.append(activity)
                        activity_type = activity.get("type", "unknown")
                        weekly_counts[activity_type] = weekly_counts.get(activity_type, 0) + 1

            except Exception as e:
                self.logger.error(f"Failed to read activity file {file}: {str(e)}")

        business_data["total_activities"] = len(weekly_activities)
        business_data["activity_breakdown"] = weekly_counts
        business_data["unique_users"] = len(set(a.get("user", "unknown") for a in weekly_activities))

        # Business transactions (if available)
        transaction_files = list(self.data_dir.glob("transactions_*.json"))
        total_transactions = 0
        transaction_values = []

        for file in transaction_files:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                transactions = data.get("transactions", [])

                for transaction in transactions:
                    transaction_date = datetime.fromisoformat(transaction.get("timestamp", ""))
                    if start_date <= transaction_date <= end_date:
                        total_transactions += 1
                        transaction_values.append(transaction.get("amount", 0))

            except Exception as e:
                self.logger.error(f"Failed to read transaction file {file}: {str(e)}")

        business_data["total_transactions"] = total_transactions
        if transaction_values:
            business_data["transaction_summary"] = {
                "total_value": sum(transaction_values),
                "average_value": sum(transaction_values) / len(transaction_values),
                "max_value": max(transaction_values),
                "min_value": min(transaction_values)
            }

        return business_data

    def _collect_system_metrics(self, start_date: datetime, end_date: datetime) -> dict:
        """Collect system metrics from the past week"""
        system_data = {}

        # CPU usage data
        cpu_files = list(self.data_dir.glob("cpu_*.log"))
        cpu_data = []

        for file in cpu_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp_str = parts[0] + " " + parts[1]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if start_date <= timestamp <= end_date:
                                cpu_usage = float(parts[2].replace("%", ""))
                                cpu_data.append({"timestamp": timestamp, "cpu_usage": cpu_usage})
            except Exception as e:
                self.logger.error(f"Failed to read CPU log {file}: {str(e)}")

        if cpu_data:
            cpu_df = pd.DataFrame(cpu_data)
            cpu_df = cpu_df.set_index('timestamp')
            system_data["cpu_usage"] = {
                "average": cpu_df["cpu_usage"].mean(),
                "max": cpu_df["cpu_usage"].max(),
                "min": cpu_df["cpu_usage"].min(),
                "peak_time": cpu_df["cpu_usage"].idxmax().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Memory usage data
        memory_files = list(self.data_dir.glob("memory_*.log"))
        memory_data = []

        for file in memory_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp_str = parts[0] + " " + parts[1]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if start_date <= timestamp <= end_date:
                                memory_usage = float(parts[2].replace("%", ""))
                                memory_data.append({"timestamp": timestamp, "memory_usage": memory_usage})
            except Exception as e:
                self.logger.error(f"Failed to read memory log {file}: {str(e)}")

        if memory_data:
            memory_df = pd.DataFrame(memory_data)
            memory_df = memory_df.set_index('timestamp')
            system_data["memory_usage"] = {
                "average": memory_df["memory_usage"].mean(),
                "max": memory_df["memory_usage"].max(),
                "min": memory_df["memory_usage"].min(),
                "peak_time": memory_df["memory_usage"].idxmax().strftime("%Y-%m-%d %H:%M:%S")
            }

        # Disk usage data
        disk_files = list(self.data_dir.glob("disk_*.log"))
        disk_data = []

        for file in disk_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp_str = parts[0] + " " + parts[1]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if start_date <= timestamp <= end_date:
                                disk_usage = float(parts[2].replace("%", ""))
                                disk_data.append({"timestamp": timestamp, "disk_usage": disk_usage})
            except Exception as e:
                self.logger.error(f"Failed to read disk log {file}: {str(e)}")

        if disk_data:
            disk_df = pd.DataFrame(disk_data)
            disk_df = disk_df.set_index('timestamp')
            system_data["disk_usage"] = {
                "average": disk_df["disk_usage"].mean(),
                "max": disk_df["disk_usage"].max(),
                "min": disk_df["disk_usage"].min(),
                "peak_time": disk_df["disk_usage"].idxmax().strftime("%Y-%m-%d %H:%M:%S")
            }

        return system_data

    def _collect_user_activity(self, start_date: datetime, end_date: datetime) -> dict:
        """Collect user activity data from the past week"""
        user_data = {}

        # Login activity
        login_files = list(self.data_dir.glob("login_*.log"))
        login_counts = {}
        unique_users = set()

        for file in login_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            timestamp_str = parts[0] + " " + parts[1]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if start_date <= timestamp <= end_date:
                                user = parts[2]
                                unique_users.add(user)
                                login_counts[user] = login_counts.get(user, 0) + 1
            except Exception as e:
                self.logger.error(f"Failed to read login log {file}: {str(e)}")

        user_data["total_logins"] = sum(login_counts.values())
        user_data["unique_users"] = len(unique_users)
        user_data["login_breakdown"] = login_counts

        # Feature usage
        feature_files = list(self.data_dir.glob("feature_usage_*.json"))
        feature_usage = {}

        for file in feature_files:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                features = data.get("features", [])

                for feature in features:
                    feature_date = datetime.fromisoformat(feature.get("timestamp", ""))
                    if start_date <= feature_date <= end_date:
                        feature_name = feature.get("name", "unknown")
                        feature_usage[feature_name] = feature_usage.get(feature_name, 0) + 1

            except Exception as e:
                self.logger.error(f"Failed to read feature usage file {file}: {str(e)}")

        user_data["feature_usage"] = feature_usage

        return user_data

    def _collect_performance_trends(self, start_date: datetime, end_date: datetime) -> dict:
        """Collect performance trends from the past week"""
        trend_data = {}

        # Response time trends
        response_files = list(self.data_dir.glob("response_*.log"))
        response_times = []
        response_counts = {}

        for file in response_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp_str = parts[0] + " " + parts[1]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if start_date <= timestamp <= end_date:
                                response_time = float(parts[2])  # in milliseconds
                                response_times.append(response_time)
                                hour = timestamp.strftime("%H:00")
                                response_counts[hour] = response_counts.get(hour, []) + [response_time]
            except Exception as e:
                self.logger.error(f"Failed to read response log {file}: {str(e)}")

        if response_times:
            trend_data["response_time"] = {
                "average": sum(response_times) / len(response_times),
                "max": max(response_times),
                "min": min(response_times),
                "total_requests": len(response_times)
            }

            # Hourly breakdown
            hourly_averages = {hour: sum(times)/len(times) for hour, times in response_counts.items()}
            trend_data["hourly_response_times"] = hourly_averages

        # Error rate trends
        error_files = list(self.data_dir.glob("error_*.log"))
        error_counts = {}
        total_requests = 0

        for file in error_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp_str = parts[0] + " " + parts[1]
                            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if start_date <= timestamp <= end_date:
                                error_count = int(parts[2])
                                hour = timestamp.strftime("%H:00")
                                error_counts[hour] = error_counts.get(hour, 0) + error_count
                                total_requests += 1
            except Exception as e:
                self.logger.error(f"Failed to read error log {file}: {str(e)}")

        if total_requests > 0:
            total_errors = sum(error_counts.values())
            trend_data["error_rate"] = {
                "total_errors": total_errors,
                "error_percentage": (total_errors / total_requests) * 100,
                "hourly_errors": error_counts
            }

        return trend_data

    def generate_summary_report(self, weekly_data: dict) -> dict:
        """Generate comprehensive weekly summary report"""
        self.logger.info("Generating weekly summary report")
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": "weekly_summary",
            "week_summary": weekly_data,
            "overall_insights": {}
        }

        # Generate insights
        insights = []
        week_summary = weekly_data.get("week_summary", {})

        # Business insights
        if "business_metrics" in week_summary:
            business = week_summary["business_metrics"]
            if business.get("total_activities", 0) > 0:
                insights.append(f"Total activities: {business['total_activities']}")
            if business.get("unique_users", 0) > 0:
                insights.append(f"Unique users: {business['unique_users']}")
            if "transaction_summary" in business:
                insights.append(f"Total transaction value: ${business['transaction_summary']['total_value']:,.2f}")

        # System insights
        if "system_metrics" in week_summary:
            system = week_summary["system_metrics"]
            for metric, values in system.items():
                if values:
                    insights.append(f"{metric.replace('_', ' ').title()}: Avg {values['average']:.2f}%, Peak {values['max']:.2f}% at {values['peak_time']}")

        # User insights
        if "user_activity" in week_summary:
            user = week_summary["user_activity"]
            insights.append(f"Total logins: {user['total_logins']}")
            if user.get("feature_usage"):
                top_features = sorted(user["feature_usage"].items(), key=lambda x: x[1], reverse=True)[:3]
                insights.append(f"Top features: {', '.join([f'{f} ({c} times)' for f, c in top_features])}")

        # Performance insights
        if "performance_trends" in week_summary:
            trends = week_summary["performance_trends"]
            if "response_time" in trends:
                rt = trends["response_time"]
                insights.append(f"Avg response time: {rt['average']:.2f}ms, Total requests: {rt['total_requests']}")
            if "error_rate" in trends:
                er = trends["error_rate"]
                insights.append(f"Error rate: {er['error_percentage']:.2f}%, Total errors: {er['total_errors']}")

        report["overall_insights"] = insights

        # Save report
        report_filename = f"weekly_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.reports_dir / report_filename

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Weekly summary report saved to {report_path}")

        # Send notification
        self.send_notification(report)

        return report

    def send_notification(self, report: dict):
        """Send notification about weekly summary report"""
        try:
            recipients = self.config.get("email_recipients", [])
            if recipients:
                self.logger.info(f"Sending weekly summary to {recipients}")
                # Here you would integrate with your email system
                # For now, just log the notification
                self.logger.info(f"Weekly summary report generated with {len(report['overall_insights'])} insights")
        except Exception as e:
            self.logger.error(f"Failed to send weekly summary notification: {str(e)}")

    def run(self):
        """Run the weekly summary task"""
        self.logger.info("Starting weekly summary task")
        try:
            # Collect weekly data
            weekly_data = self.collect_weekly_data()

            # Generate summary report
            report = self.generate_summary_report(weekly_data)

            self.logger.info("Weekly summary task completed successfully")
            return report
        except Exception as e:
            self.logger.error(f"Weekly summary task failed: {str(e)}")
            raise


def main():
    """Main entry point for weekly summary task"""
    config = {
        "data_dir": "data",
        "reports_dir": "reports/weekly",
        "include_business_metrics": True,
        "include_system_metrics": True,
        "include_user_activity": True,
        "include_performance_trends": True,
        "email_recipients": ["admin@silver-tier.com"],
        "week_start": "Monday"
    }

    generator = WeeklySummaryGenerator(config)
    result = generator.run()
    print(f"Weekly summary result: {result}")


if __name__ == "__main__":
    main()