@echo off
echo ========================================
echo Starting Silver Tier Scheduling System
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

echo Starting scheduler...
python scheduler.py

echo Scheduler started
echo.
pause