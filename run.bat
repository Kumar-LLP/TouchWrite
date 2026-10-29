@echo off
title TouchWrite Launcher
cd /d "%~dp0"

echo ========================================================
echo   Starting TouchWrite - Finger Digital Handwriting
echo ========================================================
echo.

python main.py

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
