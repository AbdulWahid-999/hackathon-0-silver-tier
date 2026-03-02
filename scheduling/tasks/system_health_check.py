"""
System Health Check Task

Performs comprehensive system health checks for the Silver Tier functional assistant
"""

import os
import json
import logging
from datetime import datetime, timedelta
import psutil
import requests
from pathlib import Path


class SystemHealthChecker:
    """System health check for Silver Tier functional assistant"""

    def __init__(self, config: dict = None):
        self.config = config or self.get_default_config()
        self.logger = self.setup_logger()
        self.checks_dir = Path(self.config.get("checks_dir", "health_checks"))
        self.reports_dir = Path(self.config.get("reports_dir", "reports/health"))
        self.checks_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def setup_logger(self):
        """Setup logger for system health checker"""
        logger = logging.getLogger('system_health_checker')
        logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.reports_dir / "health_check.log")
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
        """Get default configuration for system health checker"""
        return {
            "checks_dir": "health_checks",
            "reports_dir": "reports/health",
            "thresholds": {
                "cpu_critical": 90,
                "cpu_warning": 75,
                "memory_critical": 90,
                "memory_warning": 80,
                "disk_critical": 90,
                "disk_warning": 80,
                "network_critical": 1000,  # ms
                "network_warning": 500  # ms
            },
            "services": ["http://localhost:8080", "http://localhost:3000"],
            "email_recipients": ["admin@silver-tier.com"],
            "max_log_size_mb": 100,
            "max_temp_files": 1000
        }

    def check_system_resources(self) -> dict:
        """Check system resource usage"""
        self.logger.info("Checking system resources")
        resources = {}

        try:
            # CPU usage
            cpu_times = psutil.cpu_times_percent(interval=1)
            cpu_usage = psutil.cpu_percent(interval=1)
            resources["cpu_usage"] = cpu_usage
            resources["cpu_times"] = {
                "user": cpu_times.user,
                "system": cpu_times.system,
                "idle": cpu_times.idle,
                "iowait": cpu_times.iowait
            }

            # Memory usage
            memory = psutil.virtual_memory()
            resources["memory_usage"] = memory.percent
            resources["memory_details"] = {
                "total": memory.total,
                "available": memory.available,
                "used": memory.used,
                "free": memory.free
            }

            # Disk usage
            disk = psutil.disk_usage('/')
            resources["disk_usage"] = disk.percent
            resources["disk_details"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free
            }

            # Load average
            load = os.getloadavg()
            resources["load_average"] = {
                "1min": load[0],
                "5min": load[1],
                "15min": load[2]
            }

            self.logger.info(f"System resources checked: {resources}")
        except Exception as e:
            self.logger.error(f"Failed to check system resources: {str(e)}")
            resources["error"] = str(e)

        return resources

    def check_services(self) -> dict:
        """Check external services and dependencies"""
        self.logger.info("Checking external services")
        service_checks = {}

        for service_url in self.config.get("services", []):
            try:
                response = requests.get(service_url, timeout=10)
                service_checks[service_url] = {
                    "status": response.status_code,
                    "response_time": response.elapsed.total_seconds() * 1000,  # ms
                    "healthy": response.status_code == 200
                }
                self.logger.info(f"Service {service_url} checked: {response.status_code}")
            except Exception as e:
                service_checks[service_url] = {
                    "status": "error",
                    "error": str(e),
                    "healthy": False
                }
                self.logger.error(f"Service {service_url} check failed: {str(e)}")

        return service_checks

    def check_log_files(self) -> dict:
        """Check log files for issues"""
        self.logger.info("Checking log files")
        log_check = {}

        log_dir = Path("logs")
        if log_dir.exists():
            log_files = list(log_dir.glob("*.log"))
            large_logs = []
            error_counts = {}

            for log_file in log_files:
                try:
                    # Check file size
                    file_size = log_file.stat().st_size / (1024 * 1024)  # MB
                    if file_size > self.config.get("max_log_size_mb", 100):
                        large_logs.append({
                            "file": str(log_file),
                            "size_mb": round(file_size, 2)
                        })

                    # Count error lines
                    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                        error_count = sum(1 for line in f if "ERROR" in line.upper())
                        if error_count > 0:
                            error_counts[str(log_file)] = error_count

                except Exception as e:
                    self.logger.error(f"Failed to check log file {log_file}: {str(e)}")

            log_check["large_logs"] = large_logs
            log_check["error_counts"] = error_counts
            log_check["total_log_files"] = len(log_files)

        return log_check

    def check_temp_files(self) -> dict:
        """Check temporary files and clean up if needed"""
        self.logger.info("Checking temporary files")
        temp_check = {}

        temp_dir = Path("/tmp") if os.name != 'nt' else Path(os.environ.get('TEMP', 'C:\\Windows\\Temp'))
        if temp_dir.exists():
            temp_files = list(temp_dir.glob("**/*"))
            temp_check["total_temp_files"] = len(temp_files)

            # Check for large number of temp files
            if len(temp_files) > self.config.get("max_temp_files", 1000):
                temp_check["cleanup_required"] = True
                temp_check["files_to_clean"] = len(temp_files) - self.config.get("max_temp_files", 1000)

                # Clean up old files (optional)
                self._cleanup_temp_files(temp_files)

        return temp_check

    def _cleanup_temp_files(self, temp_files: list):
        """Clean up temporary files"""
        try:
            # Sort by modification time and remove oldest files
            temp_files.sort(key=lambda f: f.stat().st_mtime)
            files_to_remove = temp_files[:100]  # Remove 100 oldest files

            for file in files_to_remove:
                try:
                    if file.is_file():
                        file.unlink()
                        self.logger.info(f"Cleaned up temp file: {file}")
                except Exception as e:
                    self.logger.error(f"Failed to remove temp file {file}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Failed to clean up temp files: {str(e)}")

    def analyze_health_metrics(self, checks: dict) -> dict:
        """Analyze health check results and generate health score"""
        self.logger.info("Analyzing health metrics")
        analysis = {}
        health_score = 100
        issues = []

        thresholds = self.config.get("thresholds", {})

        # Analyze system resources
        if "system_resources" in checks:
            resources = checks["system_resources"]

            # CPU analysis
            cpu_usage = resources.get("cpu_usage", 0)
            if cpu_usage > thresholds.get("cpu_critical", 90):
                health_score -= 40
                issues.append(f"Critical CPU usage: {cpu_usage}%")
            elif cpu_usage > thresholds.get("cpu_warning", 75):
                health_score -= 20
                issues.append(f"High CPU usage: {cpu_usage}%")

            # Memory analysis
            memory_usage = resources.get("memory_usage", 0)
            if memory_usage > thresholds.get("memory_critical", 90):
                health_score -= 40
                issues.append(f"Critical memory usage: {memory_usage}%")
            elif memory_usage > thresholds.get("memory_warning", 80):
                health_score -= 20
                issues.append(f"High memory usage: {memory_usage}%")

            # Disk analysis
            disk_usage = resources.get("disk_usage", 0)
            if disk_usage > thresholds.get("disk_critical", 90):
                health_score -= 30
                issues.append(f"Critical disk usage: {disk_usage}%")
            elif disk_usage > thresholds.get("disk_warning", 80):
                health_score -= 15
                issues.append(f"High disk usage: {disk_usage}%")

        # Analyze services
        if "services" in checks:
            for service_url, result in checks["services"].items():
                if not result.get("healthy", False):
                    health_score -= 25
                    issues.append(f"Service {service_url} is down: {result.get('error', 'Unknown error')}")
                elif result.get("response_time", 0) > thresholds.get("network_critical", 1000):
                    health_score -= 20
                    issues.append(f"Service {service_url} slow: {result['response_time']}ms")
                elif result.get("response_time", 0) > thresholds.get("network_warning", 500):
                    health_score -= 10
                    issues.append(f"Service {service_url} response slow: {result['response_time']}ms")

        # Analyze logs
        if "log_files" in checks:
            if checks["log_files"].get("large_logs"):
                health_score -= 15
                issues.append(f"Large log files detected: {len(checks['log_files']['large_logs'])} files")

            if checks["log_files"].get("error_counts"):
                total_errors = sum(checks["log_files"]["error_counts"].values())
                health_score -= min(30, total_errors * 2)  # Reduce score based on error count
                issues.append(f"Log errors detected: {total_errors} errors")

        # Analyze temp files
        if "temp_files" in checks and checks["temp_files"].get("cleanup_required", False):
            health_score -= 10
            issues.append(f"Many temp files: {checks['temp_files']['total_temp_files']} files")

        analysis["health_score"] = max(0, health_score)
        analysis["health_status"] = "CRITICAL" if health_score < 40 else "WARNING" if health_score < 70 else "HEALTHY"
        analysis["issues"] = issues
        analysis["check_count"] = len(checks)

        self.logger.info(f"Health analysis completed: {analysis}")
        return analysis

    def generate_health_report(self, checks: dict, analysis: dict) -> dict:
        """Generate comprehensive health report"""
        self.logger.info("Generating health report")
        report = {
            "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": "system_health",
            "summary": analysis,
            "checks": checks
        }

        # Save report
        report_filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path = self.reports_dir / report_filename

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.logger.info(f"Health report saved to {report_path}")

        # Send notification if needed
        self.send_notification(report, analysis)

        return report

    def send_notification(self, report: dict, analysis: dict):
        """Send notification about health check results"""
        try:
            if analysis["health_status"] != "HEALTHY":
                recipients = self.config.get("email_recipients", [])
                if recipients:
                    self.logger.info(f"Sending health alert to {recipients}")
                    # Here you would integrate with your email system
                    # For now, just log the notification
                    self.logger.warning(f"Health alert: {analysis['health_status']} - {analysis['health_score']}%")
                    for issue in analysis["issues"]:
                        self.logger.warning(f"Issue: {issue}")
        except Exception as e:
            self.logger.error(f"Failed to send health notification: {str(e)}")

    def run(self):
        """Run the system health check task"""
        self.logger.info("Starting system health check")
        try:
            # Perform all checks
            checks = {
                "system_resources": self.check_system_resources(),
                "services": self.check_services(),
                "log_files": self.check_log_files(),
                "temp_files": self.check_temp_files()
            }

            # Analyze results
            analysis = self.analyze_health_metrics(checks)

            # Generate report
            report = self.generate_health_report(checks, analysis)

            self.logger.info("System health check completed successfully")
            return report
        except Exception as e:
            self.logger.error(f"System health check failed: {str(e)}")
            raise


def main():
    """Main entry point for system health check task"""
    config = {
        "checks_dir": "health_checks",
        "reports_dir": "reports/health",
        "thresholds": {
            "cpu_critical": 90,
            "cpu_warning": 75,
            "memory_critical": 90,
            "memory_warning": 80,
            "disk_critical": 90,
            "disk_warning": 80,
            "network_critical": 1000,
            "network_warning": 500
        },
        "services": ["http://localhost:8080", "http://localhost:3000"],
        "email_recipients": ["admin@silver-tier.com"],
        "max_log_size_mb": 100,
        "max_temp_files": 1000
    }

    checker = SystemHealthChecker(config)
    result = checker.run()
    print(f"System health check result: {result}")


if __name__ == "__main__":
    main()