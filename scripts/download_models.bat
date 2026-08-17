@echo off
setlocal
title Download Models - Local AI Voice Studio

echo ============================================================
echo   Model Download - Local AI Voice Studio
echo ============================================================
echo.

cd /d "%~dp0\.."

REM ============================================================
REM Check virtual environment
REM ============================================================

if exist "venv\Scripts\python.exe" (
    set "PYTHON=venv\Scripts\python.exe"
    echo Python environment: venv
) else if exist ".venv\Scripts\python.exe" (
    set "PYTHON=.venv\Scripts\python.exe"
    echo Python environment: .venv
) else (
    echo ERROR: Virtual environment not found.
    echo.
    echo Run:
    echo   scripts\install.bat
    echo.
    pause
    exit /b 1
)

echo.

REM ============================================================
REM Run model downloader
REM ============================================================

"%PYTHON%" "%~dp0download_models.py"

if errorlevel 1 (
    echo.
    echo ============================================================
    echo   Model download failed.
    echo ============================================================
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   Model download completed.
echo ============================================================
echo.

pause
endlocal