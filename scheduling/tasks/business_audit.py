"""
Business Audit Report Task

Generates comprehensive business audit reports for the Silver Tier functional assistant
"""

import os
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path


class BusinessAudit:
    """Business audit report generator"""

    def __init__(self, config: dict = None):
        self.config = config or self.get_default_config()
        self.logger = self.setup_logger()
        self.data_dir = Path(self.config.get("data_dir", "data"))
        self.reports_dir = Path(self.config.get("reports_dir", "reports/business_audit"))
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def setup_logger(self):
        """Setup logger for business audit"""
        logger = logging.getLogger('business_audit')
        logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.reports_dir / "business_audit.log")
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
        """Get default configuration for business audit"""
        return {
            "data_dir": "data",
            "reports_dir": "reports/business_audit",
            "include_system_metrics": True,
            "include_performance_data": True,
            "include_security_analysis": True,
            "email_recipients": ["admin@silver-tier.com"],
            "thresholds": {
                "cpu_alert": 80,
                "memory_alert": 85,
                "disk_alert": 90
            }
        }

    def collect_system_metrics(self) -> dict:
        """Collect system metrics for audit"""
        self.logger.info("Collecting system metrics")
        metrics = {}

        try:
            # System uptime
            with open("/proc/uptime", "r") as f:
                uptime = float(f.readline().split()[0])
            metrics["system_uptime_hours"] = uptime / 3600

            # CPU usage
            with open("/proc/stat", "r") as f:
                cpu_line = f.readline()
            cpu_times = list(map(int, cpu_line.split()[1:]))
            total = sum(cpu_times)
            idle = cpu_times[3]
            metrics["cpu_usage_percent"] = (1 - idle / total) * 100

            # Memory usage
            with open("/proc/meminfo", "r") as f:
                mem_total = int(f.readline().split()[1])
                mem_free = int(f.readline().split()[1])
            metrics["memory_usage_percent"] = ((mem_total - mem_free) / mem_total) * 100

            # Disk usage
            disk_usage = os.popen("df -h /").readlines()[1].split()
            metrics["disk_usage_percent"] = int(disk_usage[4].replace("%", ""))

            self.logger.info(f"System metrics collected: {metrics}")
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")
            metrics["error"] = str(e)

        return metrics

    def analyze_performance_data(self) -> dict:
        """Analyze performance data from logs and metrics"""
        self.logger.info("Analyzing performance data")
        analysis = {}

        # Analyze log files
        log_files = list(self.data_dir.glob("*.log"))
        total_lines = 0
        error_lines = 0

        for log_file in log_files:
            try:
                with open(log_file, "r") as f:
                    lines = f.readlines()
                total_lines += len(lines)
                error_lines += sum(1 for line in lines if "ERROR" in line)
            except Exception as e:
                self.logger.error(f"Failed to analyze log file {log_file}: {str(e)}")

        analysis["total_log_lines"] = total_lines
        analysis["error_lines"] = error_lines
        analysis["error_rate_percent"] = (error_lines / total_lines * 100) if total_lines > 0 else 0

        # Analyze recent activity
        recent_files = list(self.data_dir.glob("activity_*.json"))
        recent_activities = []

        for file in recent_files:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                recent_activities.extend(data.get("activities", []))
            except Exception as e:
                self.logger.error(f"Failed to analyze activity file {file}: {str(e)}")

        analysis["recent_activities_count"] = len(recent_activities)

        self.logger.info(f"Performance analysis completed: {analysis}")
        return analysis

    def generate_security_analysis(self) -> dict:
        """Generate security analysis report"""
        self.logger.info("Generating security analysis")
        analysis = {}

        # Check for unusual file access patterns
        access_logs = list(self.data_dir.glob("access_*.log"))
        suspicious_accesses = 0

        for log_file in access_logs:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        if "FAILED" in line or "UNAUTHORIZED" in line:
                            suspicious_accesses += 1
            except Exception as e:
                self.logger.error(f"Failed to analyze access log {log_file}: {str(e)}")

        analysis["suspicious_accesses"] = suspicious_accesses

        # Check for unusual network activity
        network_logs = list(self.data_dir.glob("network_*.log"))
        unusual_connections = 0

        for log_file in network_logs:
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        if "BLOCKED" in line or "SUSPICIOUS" in line:
                            unusual_connections += 1
            except Exception as e:
                self.logger.error(f"Failed to analyze network log {log_file}: {str(e)}")

        analysis["unusual_connections"] = unusual_connections

        self.logger.info(f"Security analysis completed: {analysis}")
        return analysis

    def generate_report(self) -> dict:
        """Generate comprehensive business audit report"""
        self.logger.info("Generating business audit report")
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": "business_audit",
            "summary": {}
        }

        if self.config["include_system_metrics"]:
            report["system_metrics"] = self.collect_system_metrics()

        if self.config["include_performance_data"]:
            report["performance_analysis"] = self.analyze_performance_data()

        if self.config["include_security_analysis"]:
            report["security_analysis"] = self.generate_security_analysis()

        # Generate summary
        summary = {}
        thresholds = self.config.get("thresholds", {})

        if "system_metrics" in report:
            metrics = report["system_metrics"]
            alerts = []

            if "cpu_usage_percent" in metrics and metrics["cpu_usage_percent"] > thresholds.get("cpu_alert", 80):
                alerts.append("High CPU usage detected")
            if "memory_usage_percent" in metrics and metrics["memory_usage_percent"] > thresholds.get("memory_alert", 85):
                alerts.append("High memory usage detected")
            if "disk_usage_percent" in metrics and metrics["disk_usage_percent"] > thresholds.get("disk_alert", 90):
                alerts.append("High disk usage detected")

            summary["alerts"] = alerts
            summary["overall_health"] = "WARNING" if alerts else "HEALTHY"

        report["summary"] = summary

        # Save report
        report_filename = f"business_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.reports_dir / report_filename

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Business audit report saved to {report_path}")

        # Send notification
        self.send_notification(report)

        return report

    def send_notification(self, report: dict):
        """Send notification about the audit report"""
        try:
            recipients = self.config.get("email_recipients", [])
            if recipients:
                self.logger.info(f"Sending notification to {recipients}")
                # Here you would integrate with your email system
                # For now, just log the notification
                self.logger.info(f"Business audit report generated: {len(report)} sections")
        except Exception as e:
            self.logger.error(f"Failed to send notification: {str(e)}")

    def run(self):
        """Run the business audit task"""
        self.logger.info("Starting business audit task")
        try:
            report = self.generate_report()
            self.logger.info(f"Business audit completed successfully")
            return report
        except Exception as e:
            self.logger.error(f"Business audit failed: {str(e)}")
            raise


def main():
    """Main entry point for business audit task"""
    config = {
        "data_dir": "data",
        "reports_dir": "reports/business_audit",
        "include_system_metrics": True,
        "include_performance_data": True,
        "include_security_analysis": True,
        "email_recipients": ["admin@silver-tier.com"],
        "thresholds": {
            "cpu_alert": 80,
            "memory_alert": 85,
            "disk_alert": 90
        }
    }

    audit = BusinessAudit(config)
    audit.run()


if __name__ == "__main__":
    main()