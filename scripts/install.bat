@echo off
setlocal EnableExtensions
title Local AI Voice Studio - Installer

echo ============================================================
echo   Local AI Voice Studio - Installation
echo ============================================================
echo.

cd /d "%~dp0\.."

:: ============================================================
:: [1/7] Check Python
:: ============================================================

echo [1/7] Checking Python...

python --version >nul 2>&1

if errorlevel 1 (
    echo ERROR: Python not found.
    echo Please install Python 3.10+ from:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYVER=%%a

echo Found Python %PYVER%
echo.

:: ============================================================
:: [2/7] Check Node.js
:: ============================================================

echo [2/7] Checking Node.js...

node --version >nul 2>&1

if errorlevel 1 (
    echo ERROR: Node.js not found.
    echo Please install Node.js 18+ from:
    echo https://nodejs.org/
    echo.
    pause
    exit /b 1
)

for /f "tokens=1" %%a in ('node --version 2^>^&1') do set NODEVER=%%a

echo Found Node.js %NODEVER%
echo.

:: ============================================================
:: [3/7] Create virtual environment
:: ============================================================

echo [3/7] Creating Python virtual environment...

if not exist venv (
    python -m venv venv

    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )

    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.

call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

:: ============================================================
:: Upgrade pip
:: ============================================================

echo Upgrading pip...

python -m pip install --upgrade pip

if errorlevel 1 (
    echo WARNING: pip upgrade failed.
)

echo.

:: ============================================================
:: [4/7] Detect hardware
:: ============================================================

echo [4/7] Detecting CPU / GPU / CUDA hardware...
echo.

venv\Scripts\python.exe scripts\detect_hardware.py

if errorlevel 1 (
    echo.
    echo ERROR: Hardware detection failed.
    pause
    exit /b 1
)

echo.

:: ============================================================
:: Read generated hardware config
:: ============================================================

if not exist hardware_config.json (
    echo ERROR: hardware_config.json was not generated.
    pause
    exit /b 1
)

:: ============================================================
:: [5/7] Install backend dependencies
:: ============================================================

echo [5/7] Installing backend dependencies...
echo.

python -m pip install -r backend\requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: Backend dependency installation failed.
    echo.
    pause
    exit /b 1
)

echo.
echo Backend dependencies installed successfully.
echo.

:: ============================================================
:: Verify PyTorch
:: ============================================================

echo ============================================================
echo   Verifying PyTorch / CUDA
echo ============================================================
echo.

venv\Scripts\python.exe -c "import torch; print('PyTorch:', torch.__version__); print('CUDA Build:', torch.version.cuda); print('CUDA Available:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'); print('VRAM:', round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2), 'GB' if torch.cuda.is_available() else 'N/A')" 

echo.

:: ============================================================
:: [6/7] Install frontend
:: ============================================================

echo [6/7] Installing frontend dependencies...
echo.

if exist frontend (
    cd frontend

    call npm install

    if errorlevel 1 (
        echo WARNING: Frontend npm install failed.
    )

    cd ..
) else (
    echo WARNING: frontend directory not found.
)

echo.

:: ============================================================
:: [7/7] Create directories
:: ============================================================

echo [7/7] Creating project directories...

if not exist models mkdir models
if not exist voices mkdir voices
if not exist outputs mkdir outputs
if not exist data mkdir data

echo Directories ready.
echo.

:: ============================================================
:: Final system check
:: ============================================================

echo ============================================================
echo   FINAL SYSTEM STATUS
echo ============================================================
echo.

venv\Scripts\python.exe scripts\check_gpu.py

echo.

echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.

echo Run:
echo   scripts\run.bat
echo.

pause
endlocal