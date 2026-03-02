@echo off
echo ========================================
echo Managing Windows Tasks for Silver Tier
echo ========================================
echo.

echo Available options:
echo 1. View all Silver Tier tasks
echo 2. Create all tasks
echo 3. Delete all tasks
echo 4. Run a specific task
echo 5. Exit
echo.
set /p choice="Enter your choice: "

if "%choice%"=="1" (
    schtasks /query | findstr /i "SilverTier"
    pause
    exit /b 0
)

if "%choice%"=="2" (
    echo Creating all Silver Tier tasks...
    schtasks /create /tn "SilverTier_BusinessAudit" /tr "python C:\\path\\to\\scheduling\\scheduler.py" /sc daily /st 02:00 /ru SYSTEM /rl HIGHEST /f /d "MON,TUE,WED,THU,FRI,SAT,SUN" /z /it
    schtasks /create /tn "SilverTier_DashboardUpdate" /tr "python C:\\path\\to\\scheduling\\scheduler.py" /sc daily /st 03:00 /ru SYSTEM /rl HIGHEST /f /d "MON,TUE,WED,THU,FRI,SAT,SUN" /z /it
    schtasks /create /tn "SilverTier_SystemHealth" /tr "python C:\\path\\to\\scheduling\\scheduler.py" /sc daily /st 04:00 /ru SYSTEM /rl HIGHEST /f /d "MON,TUE,WED,THU,FRI,SAT,SUN" /z /it
    schtasks /create /tn "SilverTier_WeeklySummary" /tr "python C:\\path\\to\\scheduling\\scheduler.py" /sc weekly /st 23:59 /d SUN /ru SYSTEM /rl HIGHEST /f /z /it
    echo Tasks created successfully
    pause
    exit /b 0
)

if "%choice%"=="3" (
    echo Deleting all Silver Tier tasks...
    schtasks /delete /tn "SilverTier_BusinessAudit" /f
    schtasks /delete /tn "SilverTier_DashboardUpdate" /f
    schtasks /delete /tn "SilverTier_SystemHealth" /f
    schtasks /delete /tn "SilverTier_WeeklySummary" /f
    echo Tasks deleted successfully
    pause
    exit /b 0
)

if "%choice%"=="4" (
    echo Available tasks:
echo 1. Business Audit Report
echo 2. Dashboard Update
echo 3. System Health Check
echo 4. Weekly Summary Report
set /p task_choice="Enter task number: "

    if "%task_choice%"=="1" (
        echo Running Business Audit Report...
        python scheduling\tasks\business_audit.py
    )

    if "%task_choice%"=="2" (
        echo Running Dashboard Update...
        python scheduling\tasks\dashboard_update.py
    )

    if "%task_choice%"=="3" (
        echo Running System Health Check...
        python scheduling\tasks\system_health_check.py
    )

    if "%task_choice%"=="4" (
        echo Running Weekly Summary Report...
        python scheduling\tasks\weekly_summary.py
    )

    pause
    exit /b 0
)

if "%choice%"=="5" (
    exit /b 0
)

echo Invalid choice
echo.
pause