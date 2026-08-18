@echo off
title Local AI Voice Studio - Installer
echo ============================================================
echo   Local AI Voice Studio - Installation
echo ============================================================
echo.

cd /d "%~dp0\.."

:: Check for Python (prefer Python 3.11/3.10 via py launcher)
echo [1/7] Checking Python version (Python 3.10 or 3.11 required)...
set "PY_CMD="

py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3.11"
    goto :py_found
)

py -3.10 --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3.10"
    goto :py_found
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=python"
    goto :py_found
)

echo ERROR: Python 3.10+ not found.
echo Please install Python 3.11 from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" and install the Python Launcher (py).
pause
exit /b 1

:py_found
for /f "tokens=2" %%a in ('%PY_CMD% --version 2^>^&1') do set PYVER=%%a
echo Found Python %PYVER% (using %PY_CMD%)

:: Check Node.js
echo [2/7] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found.
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=1" %%a in ('node --version 2^>^&1') do set NODEVER=%%a
echo Found Node.js %NODEVER%

:: Create Python virtual environment
echo.
echo [3/7] Creating Python virtual environment with %PY_CMD%...
if not exist venv (
    %PY_CMD% -m venv venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

:: Activate venv and upgrade pip
call venv\Scripts\activate.bat
echo Upgrading pip...
python -m pip install --upgrade pip

:: Detect GPU and install PyTorch
echo.
echo [4/7] Detecting GPU and installing PyTorch...
nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo No NVIDIA GPU detected. Installing CPU-only PyTorch...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
) else (
    echo NVIDIA GPU detected. Installing CUDA PyTorch...
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    if errorlevel 1 (
        echo CUDA install failed. Falling back to CPU PyTorch...
        pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    )
)

:: Install OmniVoice and other dependencies
echo.
echo [5/7] Installing OmniVoice and backend dependencies...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo WARNING: Some dependencies may have failed.
    echo Please check the output above.
)

:: Install frontend dependencies
echo.
echo [6/7] Installing frontend dependencies...
cd frontend
call npm install
cd ..

:: Create directories
echo.
echo [7/7] Creating project directories...
if not exist models mkdir models
if not exist voices mkdir voices
if not exist outputs mkdir outputs
if not exist data mkdir data

:: Final check
echo.
echo ============================================================
echo   Installation Complete!
echo ============================================================
echo.

python -c "import torch; cuda=torch.cuda.is_available(); print(f'  CUDA: {\"Available\" if cuda else \"Not available\"}')" 2>nul
if errorlevel 1 (
    echo   CUDA: Not available
    echo   Using CPU mode.
) else (
    python -c "import torch; print(f'  GPU: {torch.cuda.get_device_name(0)}') if torch.cuda.is_available() else None" 2>nul
)

python -c "import omnivoice; print('  OmniVoice: Installed')" 2>nul
if errorlevel 1 (
    echo   OmniVoice: NOT INSTALLED - run: pip install omnivoice
) 

echo.
echo Run 'scripts\run.bat' to start the application.
echo.
pause