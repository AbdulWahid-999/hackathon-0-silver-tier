@echo off
echo ========================================
echo Stopping Silver Tier Scheduling System
echo ========================================
echo.

REM Stop the scheduler process
echo Stopping scheduler processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq Silver Tier Scheduling System"
taskkill /f /im python.exe /fi "WINDOWTITLE eq scheduler.py"

echo Processes stopped
echo.
pause