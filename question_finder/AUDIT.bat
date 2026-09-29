@echo off
title CLF-C02 Question Researcher — Dataset Audit
cd /d "%~dp0"

echo ============================================================
echo   CLF-C02 Dataset Integrity & Provenance Audit
echo ============================================================
echo.

".venv\Scripts\python.exe" -m app.cli.main audit
echo.
".venv\Scripts\python.exe" -m app.cli.main stats

echo.
pause
