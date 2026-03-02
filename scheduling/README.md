# Silver Tier Scheduling System

A comprehensive cron-style scheduling system for the Silver Tier functional assistant using Windows Task Scheduler.

## Overview

This scheduling system provides automated daily and weekly tasks including:
- Business Audit Reports
- Dashboard Updates with Visualizations
- System Health Checks
- Weekly Summary Reports

## Installation

1. Navigate to the scheduling directory:
```bash
cd scheduling
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create necessary directories:
```bash
mkdir logs
data
dashboard
reports
health_checks
```

## Configuration

The main configuration is in `config.json`:

```json
{
  "tasks": [
    {
      "name": "Business Audit Report",
      "script_path": "scheduling/tasks/business_audit.py",
      "schedule_time": "02:00",
      "frequency": "DAILY",
      "enabled": true
    }
    // More tasks...
  ],
  "log_level": "INFO",
  "notification_thresholds": {
    "cpu_alert": 80,
    "memory_alert": 85
  }
}
```

## Available Tasks

### 1. Business Audit Report
- **Schedule**: Daily at 02:00
- **Purpose**: Generates comprehensive business audit reports
- **Metrics**: System metrics, performance data, security analysis
- **Output**: JSON reports in `reports/business_audit/`

### 2. Dashboard Update
- **Schedule**: Daily at 03:00
- **Purpose**: Updates dashboard metrics and generates visualizations
- **Features**: Line charts, bar charts, heatmaps, correlation analysis
- **Output**: Visualizations in `dashboard/visualizations/`, HTML dashboard

### 3. System Health Check
- **Schedule**: Daily at 04:00
- **Purpose**: Performs comprehensive system health checks
- **Checks**: CPU, memory, disk, services, logs, temp files
- **Output**: Health reports in `reports/health/`

### 4. Weekly Summary Report
- **Schedule**: Weekly at 23:59
- **Purpose**: Generates comprehensive weekly summary reports
- **Metrics**: Business metrics, system metrics, user activity, trends
- **Output**: Summary reports in `reports/weekly/`

## Running the Scheduler

### Option 1: Run as Python Script
```bash
python scheduler.py
```

### Option 2: Install as Windows Service
1. Create a batch file to run the scheduler:
```batch
schedule.bat
@echo off
python C:\path\to\scheduling\scheduler.py
pause
```

2. Use `nssm` or similar tool to install as Windows service:
```bash
schedtasks /create /tn "SilverTierScheduler" /tr "C:\path\to\schedule.bat" /sc daily /st 01:00
```

## Task Management

### Adding New Tasks

1. Create your task script in `scheduling/tasks/`
2. Add task configuration to `config.json`:
```json
{
  "name": "New Task",
  "script_path": "scheduling/tasks/new_task.py",
  "schedule_time": "12:00",
  "frequency": "DAILY",
  "enabled": true
}
```

### Manual Task Execution

You can run any task manually:
```bash
python scheduling/tasks/business_audit.py
python scheduling/tasks/dashboard_update.py
```

## Data Management

- **Data Retention**: Logs and reports are retained for 30 days by default
- **Log Directory**: `logs/` - Scheduler logs
- **Data Directory**: `data/` - Raw metrics and activity logs
- **Reports Directory**: `reports/` - Generated reports by category

## Integration with Existing Workflow

### File Watcher Integration
The scheduling system can work alongside existing file watchers:
- The dashboard task can visualize file watcher metrics
- Health checks can monitor file watcher performance

### Email System Integration

The scheduling system includes email notification capabilities:
- Health alerts for critical system issues
- Report notifications
- Weekly summary delivery

## Monitoring and Maintenance

### Log Files
- **Scheduler Log**: `logs/scheduler.log`
- **Task Logs**: Each task generates its own log files
- **Health Reports**: `reports/health/health_check.log`

### Health Monitoring
- CPU usage thresholds
- Memory usage alerts
- Disk space monitoring
- Service availability checks

## Troubleshooting

### Common Issues

1. **Task Not Running**: Check scheduler log for errors
2. **Missing Dependencies**: Install requirements with `pip install -r requirements.txt`
3. **Permission Issues**: Ensure Windows Task Scheduler has proper permissions
4. **Time Zone Issues**: Verify system time zone settings

### Debug Mode

Run the scheduler in debug mode to see detailed output:
```bash
python scheduler.py --debug
```

## Dependencies

- Python 3.7+
- schedule (task scheduling)
- psutil (system monitoring)
- pandas (data analysis)
- matplotlib, seaborn (visualizations)
- requests (service checks)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your task or improvements
4. Test thoroughly
5. Submit a pull request