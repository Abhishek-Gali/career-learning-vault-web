@echo off
title CLF-C02 Question Researcher — Setup
cd /d "%~dp0"

echo ============================================================
echo   Installing Self-Contained Dependencies (Project Root on E:\)
echo ============================================================
echo.

powershell.exe -ExecutionPolicy Bypass -File ".\scripts\setup.ps1"

echo.
pause
