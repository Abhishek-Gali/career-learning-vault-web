@echo off
title CLF-C02 Question Researcher — Export Datasets
cd /d "%~dp0"

echo ============================================================
echo   Exporting CLF-C02 Datasets
echo ============================================================
echo.

echo [1/3] Exporting JSON to data\exports\questions.json...
".venv\Scripts\python.exe" -m app.cli.main export --format json --output data/exports/questions.json

echo.
echo [2/3] Exporting CSV to data\exports\questions.csv...
".venv\Scripts\python.exe" -m app.cli.main export --format csv --output data/exports/questions.csv

echo.
echo [3/3] Exporting Markdown to data\exports\study_guide.md...
".venv\Scripts\python.exe" -m app.cli.main export --format md --output data/exports/study_guide.md

echo.
echo ============================================================
echo   All exports generated in data\exports\ !
echo ============================================================
echo.
pause
