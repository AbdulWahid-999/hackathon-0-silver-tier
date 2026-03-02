@echo off
echo ================================================
echo Cleaning up unnecessary files
echo ================================================
echo.

echo Deleting test files...
del /q linkedin_debug_watcher.py
del /q test_silver_tier.py
del /q simple-test.js
del /q test-ralph-wiggum.js
del /q test_ralph_wiggum.js
del /q test_email_composition.js
del /q test_request.json

echo.
echo Deleting Ralph Wiggum demo files...
del /q ralph-wiggum-demo.js
del /q ralph-wiggum-integration-example.js
del /q ralph-wiggum-loop.js
del /q enhanced-ralph-wiggum-loop.js

echo.
echo Deleting MCP Email Server files...
del /q mcp-email-server.js
del /q mcp-email-server-enhanced.js
del /q mcp-email-client-enhanced.js
del /q integration_example.js
del /q example_mcp_client.js

echo.
echo Deleting test reports...
del /q final_automated_test_report.md
del /q LinkedIn_Watcher_Test_Report.md
del /q simple_task_complete.txt

echo.
echo Deleting duplicate READMEs...
del /q README-enhanced-ralph-wiggum.md
del /q README-MCP-EMAIL.md
del /q README-RALPH-WIGGUM.md
del /q README_gmail_watcher.md
del /q README_MCP_EMAIL_SERVER.md
del /q README_RALPH_WIGGUM.md
del /q SILVER-TIER-README.md
del /q SUMMARY.md

echo.
echo Deleting unused shell scripts...
del /q deploy.sh
del /q maintenance.sh
del /q run_integration.sh
del /q update.sh

echo.
echo ================================================
echo Cleanup complete!
echo ================================================
echo.
echo Files kept (ESSENTIAL):
echo   - linkedin_watcher.py
echo   - whatsapp_watcher.py
echo   - orchestrator.py
echo   - file_watcher.py
echo   - gmail_watcher.py (if using)
echo   - scheduler.py
echo   - .env
echo   - requirements.txt
echo   - AI_Silver_Employee_Vault/ (all data)
echo.
pause
