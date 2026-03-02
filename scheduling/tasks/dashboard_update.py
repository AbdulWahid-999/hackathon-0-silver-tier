"""
Dashboard Update Task

Updates dashboard metrics and generates visualizations for the Silver Tier functional assistant
"""

import os
import json
import logging
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path


class DashboardUpdater:
    """Dashboard update task for Silver Tier functional assistant"""

    def __init__(self, config: dict = None):
        self.config = config or self.get_default_config()
        self.logger = self.setup_logger()
        self.data_dir = Path(self.config.get("data_dir", "data"))
        self.dashboard_dir = Path(self.config.get("dashboard_dir", "dashboard"))
        self.dashboard_dir.mkdir(parents=True, exist_ok=True)

    def setup_logger(self):
        """Setup logger for dashboard updater"""
        logger = logging.getLogger('dashboard_updater')
        logger.setLevel(logging.INFO)

        # File handler
        file_handler = logging.FileHandler(self.dashboard_dir / "dashboard_update.log")
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
        """Get default configuration for dashboard updater"""
        return {
            "data_dir": "data",
            "dashboard_dir": "dashboard",
            "metrics": ["cpu_usage", "memory_usage", "disk_usage", "response_time", "error_rate"],
            "time_window": "24h",
            "visualizations": ["line", "bar", "heatmap"],
            "output_formats": ["png", "json"]
        }

    def collect_metrics(self) -> dict:
        """Collect metrics from various sources"""
        self.logger.info("Collecting dashboard metrics")
        metrics = {}

        # System metrics
        try:
            # CPU usage
            cpu_data = self._collect_cpu_metrics()
            metrics["cpu_usage"] = cpu_data

            # Memory usage
            memory_data = self._collect_memory_metrics()
            metrics["memory_usage"] = memory_data

            # Disk usage
            disk_data = self._collect_disk_metrics()
            metrics["disk_usage"] = disk_data

            self.logger.info("System metrics collected")
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {str(e)}")

        # Application metrics
        try:
            # Response times
            response_data = self._collect_response_metrics()
            metrics["response_time"] = response_data

            # Error rates
            error_data = self._collect_error_metrics()
            metrics["error_rate"] = error_data

            self.logger.info("Application metrics collected")
        except Exception as e:
            self.logger.error(f"Failed to collect application metrics: {str(e)}")

        return metrics

    def _collect_cpu_metrics(self) -> pd.DataFrame:
        """Collect CPU usage metrics"""
        # Read CPU usage data from log files
        cpu_files = list(self.data_dir.glob("cpu_*.log"))
        data = []

        for file in cpu_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp = parts[0] + " " + parts[1]
                            cpu_usage = float(parts[2].replace("%", ""))
                            data.append({"timestamp": timestamp, "cpu_usage": cpu_usage})
            except Exception as e:
                self.logger.error(f"Failed to read CPU log {file}: {str(e)}")

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.resample('5T').mean().dropna()  # Resample to 5-minute intervals
        return df

    def _collect_memory_metrics(self) -> pd.DataFrame:
        """Collect memory usage metrics"""
        memory_files = list(self.data_dir.glob("memory_*.log"))
        data = []

        for file in memory_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp = parts[0] + " " + parts[1]
                            memory_usage = float(parts[2].replace("%", ""))
                            data.append({"timestamp": timestamp, "memory_usage": memory_usage})
            except Exception as e:
                self.logger.error(f"Failed to read memory log {file}: {str(e)}")

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.resample('5T').mean().dropna()
        return df

    def _collect_disk_metrics(self) -> pd.DataFrame:
        """Collect disk usage metrics"""
        disk_files = list(self.data_dir.glob("disk_*.log"))
        data = []

        for file in disk_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp = parts[0] + " " + parts[1]
                            disk_usage = float(parts[2].replace("%", ""))
                            data.append({"timestamp": timestamp, "disk_usage": disk_usage})
            except Exception as e:
                self.logger.error(f"Failed to read disk log {file}: {str(e)}")

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.resample('5T').mean().dropna()
        return df

    def _collect_response_metrics(self) -> pd.DataFrame:
        """Collect response time metrics"""
        response_files = list(self.data_dir.glob("response_*.log"))
        data = []

        for file in response_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp = parts[0] + " " + parts[1]
                            response_time = float(parts[2])  # in milliseconds
                            data.append({"timestamp": timestamp, "response_time": response_time})
            except Exception as e:
                self.logger.error(f"Failed to read response log {file}: {str(e)}")

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.resample('5T').mean().dropna()
        return df

    def _collect_error_metrics(self) -> pd.DataFrame:
        """Collect error rate metrics"""
        error_files = list(self.data_dir.glob("error_*.log"))
        data = []

        for file in error_files:
            try:
                with open(file, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            timestamp = parts[0] + " " + parts[1]
                            error_count = int(parts[2])
                            data.append({"timestamp": timestamp, "error_count": error_count})
            except Exception as e:
                self.logger.error(f"Failed to read error log {file}: {str(e)}")

        df = pd.DataFrame(data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        df = df.resample('5T').sum().dropna()
        return df

    def generate_visualizations(self, metrics: dict) -> dict:
        """Generate dashboard visualizations"""
        self.logger.info("Generating dashboard visualizations")
        visualizations = {}

        # Create output directory
        viz_dir = self.dashboard_dir / "visualizations"
        viz_dir.mkdir(exist_ok=True)

        # Line charts for time series data
        if "cpu_usage" in metrics:
            self._create_line_chart(metrics["cpu_usage"], "CPU Usage", "cpu_usage_line")
            visualizations["cpu_usage_line"] = "line chart created"

        if "memory_usage" in metrics:
            self._create_line_chart(metrics["memory_usage"], "Memory Usage", "memory_usage_line")
            visualizations["memory_usage_line"] = "line chart created"

        if "response_time" in metrics:
            self._create_line_chart(metrics["response_time"], "Response Time", "response_time_line")
            visualizations["response_time_line"] = "line chart created"

        # Bar charts for aggregated data
        if "disk_usage" in metrics:
            self._create_bar_chart(metrics["disk_usage"], "Disk Usage", "disk_usage_bar")
            visualizations["disk_usage_bar"] = "bar chart created"

        if "error_rate" in metrics:
            self._create_bar_chart(metrics["error_rate"], "Error Rate", "error_rate_bar")
            visualizations["error_rate_bar"] = "bar chart created"

        # Heatmap for correlation
        if len(metrics) > 1:
            self._create_heatmap(metrics, "system_correlation")
            visualizations["system_correlation"] = "heatmap created"

        self.logger.info(f"Visualizations generated: {list(visualizations.keys())}")
        return visualizations

    def _create_line_chart(self, data: pd.DataFrame, title: str, filename: str):
        """Create a line chart"""
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(data.index, data.iloc[:, 0], marker='o', linewidth=2)
            plt.title(f"{title} Over Time")
            plt.xlabel("Time")
            plt.ylabel(title)
            plt.grid(True)
            plt.tight_layout()

            # Save as PNG
            png_path = self.dashboard_dir / "visualizations" / f"{filename}.png"
            plt.savefig(png_path)
            plt.close()

            self.logger.info(f"Line chart saved to {png_path}")
        except Exception as e:
            self.logger.error(f"Failed to create line chart: {str(e)}")

    def _create_bar_chart(self, data: pd.DataFrame, title: str, filename: str):
        """Create a bar chart"""
        try:
            plt.figure(figsize=(12, 6))
            data.iloc[-10:].plot(kind='bar', legend=False)  # Show last 10 data points
            plt.title(f"{title} (Last 10 Intervals)")
            plt.xlabel("Interval")
            plt.ylabel(title)
            plt.grid(True)
            plt.tight_layout()

            # Save as PNG
            png_path = self.dashboard_dir / "visualizations" / f"{filename}.png"
            plt.savefig(png_path)
            plt.close()

            self.logger.info(f"Bar chart saved to {png_path}")
        except Exception as e:
            self.logger.error(f"Failed to create bar chart: {str(e)}")

    def _create_heatmap(self, metrics: dict, filename: str):
        """Create a correlation heatmap"""
        try:
            # Combine all metrics into one DataFrame
            dfs = []
            for name, df in metrics.items():
                if not df.empty:
                    dfs.append(df.rename(columns={df.columns[0]: name}))

            if len(dfs) > 1:
                combined_df = pd.concat(dfs, axis=1).dropna()
                correlation = combined_df.corr()

                plt.figure(figsize=(10, 8))
                sns.heatmap(correlation, annot=True, cmap='coolwarm', center=0)
                plt.title("System Metrics Correlation")
                plt.tight_layout()

                # Save as PNG
                png_path = self.dashboard_dir / "visualizations" / f"{filename}.png"
                plt.savefig(png_path)
                plt.close()

                self.logger.info(f"Heatmap saved to {png_path}")
        except Exception as e:
            self.logger.error(f"Failed to create heatmap: {str(e)}")

    def generate_summary(self, metrics: dict) -> dict:
        """Generate dashboard summary statistics"""
        self.logger.info("Generating dashboard summary")
        summary = {}

        # Calculate statistics for each metric
        for metric_name, data in metrics.items():
            if not data.empty:
                summary[metric_name] = {
                    "current_value": data.iloc[-1, 0],
                    "average": data.mean().iloc[0],
                    "max": data.max().iloc[0],
                    "min": data.min().iloc[0],
                    "std_dev": data.std().iloc[0]
                }

        # Overall system health
        health_score = 100

        # Check for critical metrics
        if "cpu_usage" in summary:
            cpu = summary["cpu_usage"]["current_value"]
            if cpu > 80:
                health_score -= 30
            elif cpu > 60:
                health_score -= 10

        if "memory_usage" in summary:
            memory = summary["memory_usage"]["current_value"]
            if memory > 85:
                health_score -= 30
            elif memory > 70:
                health_score -= 10

        if "error_rate" in summary:
            errors = summary["error_rate"]["current_value"]
            if errors > 10:
                health_score -= 20
            elif errors > 5:
                health_score -= 10

        summary["health_score"] = max(0, health_score)
        summary["health_status"] = "CRITICAL" if health_score < 40 else "WARNING" if health_score < 70 else "HEALTHY"

        self.logger.info(f"Dashboard summary generated: {summary}")
        return summary

    def save_dashboard_data(self, metrics: dict, visualizations: dict, summary: dict):
        """Save dashboard data to JSON file"""
        self.logger.info("Saving dashboard data")
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "metrics": {k: v.to_dict() for k, v in metrics.items()},
            "visualizations": visualizations,
            "summary": summary
        }

        # Save to JSON
        json_path = self.dashboard_dir / "dashboard_data.json"
        with open(json_path, "w") as f:
            json.dump(dashboard_data, f, indent=2, default=str)

        self.logger.info(f"Dashboard data saved to {json_path}")

    def generate_html_dashboard(self, metrics: dict, visualizations: dict, summary: dict):
        """Generate HTML dashboard"""
        self.logger.info("Generating HTML dashboard")
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Silver Tier Dashboard - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .metric-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; }}
                .health-good {{ color: green; }}
                .health-warning {{ color: orange; }}
                .health-critical {{ color: red; }}
                .chart {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Silver Tier Functional Assistant Dashboard</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

                <!-- System Health Summary -->
                <div class="metric-card">
                    <h2>System Health</h2>
                    <div class="metric-value {{"health-good" if summary[\"health_status\"] == \"HEALTHY\" else (\"health-warning\" if summary[\"health_status\"] == \"WARNING\" else \"health-critical\")}}">
                        {summary[\"health_status\"]} ({summary[\"health_score\"]}%)</div>
                    <p>Current system health status and score.</p>
                </div>

                <!-- Key Metrics -->
                <div class="metric-card">
                    <h2>Key Metrics</h2>
                    <div class="row">
                        <div class="col">
                            <strong>CPU Usage:</strong> {summary.get(\"cpu_usage\", {}).get(\"current_value\", \"N/A\")}%
                        </div>
                        <div class="col">
                            <strong>Memory Usage:</strong> {summary.get(\"memory_usage\", {}).get(\"current_value\", \"N/A\")}%
                        </div>
                        <div class="col">
                            <strong>Response Time:</strong> {summary.get(\"response_time\", {}).get(\"current_value\", \"N/A\")}ms
                        </div>
                    </div>
                </div>

                <!-- Visualizations -->
                <h2>System Visualizations</h2>
        """

        # Add visualizations
        for viz_name, _ in visualizations.items():
            if viz_name.endswith("_line"):
                html_content += f'<div class="chart"><h3>{viz_name.replace("_", " ").title()}</h3><img src="visualizations/{viz_name}.png" alt="{viz_name}" width="100%"></div>'

        html_content += f"""
            </div>
        </body>
        </html>
        """

        # Save HTML file
        html_path = self.dashboard_dir / "dashboard.html"
        with open(html_path, "w") as f:
            f.write(html_content)

        self.logger.info(f"HTML dashboard saved to {html_path}")

    def run(self):
        """Run the dashboard update task"""
        self.logger.info("Starting dashboard update task")
        try:
            # Collect metrics
            metrics = self.collect_metrics()

            # Generate visualizations
            visualizations = self.generate_visualizations(metrics)

            # Generate summary
            summary = self.generate_summary(metrics)

            # Save dashboard data
            self.save_dashboard_data(metrics, visualizations, summary)

            # Generate HTML dashboard
            self.generate_html_dashboard(metrics, visualizations, summary)

            self.logger.info("Dashboard update completed successfully")
            return {
                "status": "success",
                "metrics_count": len(metrics),
                "visualizations_count": len(visualizations),
                "summary": summary
            }
        except Exception as e:
            self.logger.error(f"Dashboard update failed: {str(e)}")
            raise


def main():
    """Main entry point for dashboard update task"""
    config = {
        "data_dir": "data",
        "dashboard_dir": "dashboard",
        "metrics": ["cpu_usage", "memory_usage", "disk_usage", "response_time", "error_rate"],
        "time_window": "24h",
        "visualizations": ["line", "bar", "heatmap"],
        "output_formats": ["png", "json"]
    }

    updater = DashboardUpdater(config)
    result = updater.run()
    print(f"Dashboard update result: {result}")


if __name__ == "__main__":
    main()