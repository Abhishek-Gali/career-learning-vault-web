@echo off
title CLF-C02 Question Researcher — Research Pipeline
cd /d "%~dp0"

echo ============================================================
echo   Running AWS CLF-C02 Research & Discovery Pipeline
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Running initial setup first...
    powershell.exe -ExecutionPolicy Bypass -File ".\scripts\setup.ps1"
)

echo [INFO] Executing Research Pipeline (6 Months Window, Target 1,000 Questions)...
".venv\Scripts\python.exe" -m app.cli.main research --months 6 --recent-source-target 1000

echo.
echo ============================================================
echo   Research cycle complete!
echo ============================================================
echo.
pause
