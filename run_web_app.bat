@echo off
chcp 65001 >nul
title Career Learning Vault — Cloud Web Server
cd /d "%~dp0"
echo ====================================================================
echo   Career Learning Vault — Cloud Web Server (Refero & Watermelon UI)
echo ====================================================================
echo.
echo [1/2] Checking Python environment...
python -c "import fastapi, uvicorn" 2>nul
if %errorlevel% neq 0 (
    echo [*] Installing dependencies (fastapi, uvicorn)...
    pip install -r requirements.txt
)
echo [2/2] Launching Uvicorn server on http://127.0.0.1:8000 ...
echo Press Ctrl+C in this terminal to stop the server.
echo.
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause
