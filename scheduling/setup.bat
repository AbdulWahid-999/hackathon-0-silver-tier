@echo off
echo ========================================
echo Setting up Silver Tier Scheduling System
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher and add it to your PATH
    pause
    exit /b 1
)

echo Python detected: %python_version%
echo.

REM Create necessary directories
if not exist logs mkdir logs
if not exist data mkdir data
if not exist dashboard mkdir dashboard
if not exist reports mkdir reports
if not exist health_checks mkdir health_checks

if exist logs (
    echo Created logs directory
echo Created data directory
echo Created dashboard directory
echo Created reports directory
echo Created health_checks directory
) else (
    echo ERROR: Failed to create directories
    pause
    exit /b 1
)

echo.

REM Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% equ 0 (
    echo Dependencies installed successfully
) else (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.

REM Create sample data files
echo Creating sample data files...
if not exist data\sample.txt (
    echo Sample data file > data\sample.txt
)

echo Sample data files created
echo.

REM Create Windows Task Scheduler tasks
echo Creating Windows Task Scheduler tasks...
echo.

REM Task 1: Business Audit Report
schtasks /create /tn "SilverTier_BusinessAudit" /tr "python C:\\path\\to\\scheduling\\scheduler.py" /sc daily /st 02:00 /ru SYSTEM /rl HIGHEST /f /d "MON,TUE,WED,THU,FRI,SAT,SUN" /z /it
echo Created Business Audit task
echo.

REM Task 2: Dashboard Update
schtasks /create /tn "SilverTier_DashboardUpdate" /tr "python C:\\path\\to\\scheduling\\scheduler.py" /sc daily /st 03:00 /ru SYSTEM /rl HIGHEST /f /d "MON,TUE,WED,THU,FRI,SAT,SUN" /z /it
echo Created Dashboard Update task
echo.

REM Task 3: System Health Check
schtasks /create /tn "SilverTier_SystemHealth" /tr "python C:\\path\\to\\scheduling\\scheduler.py" /sc daily /st 04:00 /ru SYSTEM /rl HIGHEST /f /d "MON,TUE,WED,THU,FRI,SAT,SUN" /z /it
echo Created System Health task
echo.

REM Task 4: Weekly Summary Report (Sunday)
schtasks /create /tn "SilverTier_WeeklySummary" /tr "python C:\\path\\to\\scheduling\\scheduler.py" /sc weekly /st 23:59 /d SUN /ru SYSTEM /rl HIGHEST /f /z /it
echo Created Weekly Summary task
echo.

REM Verify tasks were created
echo Verifying tasks were created...
schtasks /query | findstr /i "SilverTier"

echo.

REM Test the scheduler
echo Testing the scheduler...
python scheduler.py --test 1
echo.

REM Show completion message
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Review the configuration in scheduling/config.json
echo 2. Customize task schedules as needed
echo 3. Monitor logs in logs/ directory
echo 4. Check generated reports in reports/ directory
echo.
echo To start the scheduler manually:
echo   python scheduler.py
echo.
echo To view scheduled tasks:
echo   schtasks /query | findstr SilverTier
echo.
echo To delete all Silver Tier tasks:
echo   schtasks /delete /tn "SilverTier_*" /f
echo.
pause