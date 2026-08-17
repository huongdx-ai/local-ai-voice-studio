@echo off
title Local AI Voice Studio - GPU Check

cd /d "%~dp0\.."

echo ============================================================
echo   Local AI Voice Studio - GPU / CUDA Check
echo ============================================================
echo.

if not exist venv\Scripts\python.exe (
    echo ERROR: Virtual environment not found.
    echo Please run scripts\install.bat first.
    echo.
    pause
    exit /b 1
)

venv\Scripts\python.exe scripts\check_gpu.py

echo.
pause