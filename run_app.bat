@echo off
title Smart Expense Tracker with Analytics
cd /d "%~dp0"
echo ========================================================
echo   Launching Smart Expense Tracker with Analytics...
echo ========================================================
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with an error.
    pause
)
