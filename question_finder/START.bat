@echo off
title CLF-C02 Question Researcher — Web App
cd /d "%~dp0"

echo ============================================================
echo   AWS CLF-C02 Recent Practice Question Researcher
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual environment not found. Running initial setup...
    powershell.exe -ExecutionPolicy Bypass -File ".\scripts\setup.ps1"
    if %errorlevel% neq 0 (
        echo [ERROR] Setup failed.
        pause
        exit /b %errorlevel%
    )
)

echo [INFO] Starting Web Server on http://127.0.0.1:8000 ...
echo [INFO] Press Ctrl+C in this window to stop the server.
echo.

:: Open default browser in 2 seconds
start "" "http://127.0.0.1:8000"

:: Start Uvicorn web server
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000

pause
