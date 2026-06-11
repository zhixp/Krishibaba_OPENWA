@echo off
REM Krishi Baba - Daily Price Scraper Runner
REM Run this via Windows Task Scheduler

echo ============================================
echo Krishi Baba - Daily Price Update
echo %date% %time%
echo ============================================
echo.

cd /d "%~dp0"

REM Activate virtual environment if you have one
REM call venv\Scripts\activate.bat

echo Running scraper...
python scripts\watchdog.py

echo.
echo ============================================
echo Completed at %date% %time%
echo ============================================
