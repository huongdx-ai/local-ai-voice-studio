@echo off
title Local AI Voice Studio
echo ============================================================
echo   Local AI Voice Studio - Starting
echo ============================================================
echo.

cd /d "%~dp0\.."

:: Check venv
if not exist venv (
    echo ERROR: Virtual environment not found.
    echo Please run 'scripts\install.bat' first.
    pause
    exit /b 1
)

:: Activate venv
call venv\Scripts\activate.bat

:: Check CUDA
echo Detecting hardware...
python -c "import torch; cuda=torch.cuda.is_available(); name=torch.cuda.get_device_name(0) if cuda else 'N/A'; print(f'GPU: {name}') if cuda else print('GPU: Not detected'); print(f'CUDA: {\"Available\" if cuda else \"Not available\"}'); print(f'Device: {\"CUDA\" if cuda else \"CPU\"}')" 2>nul
if errorlevel 1 (
    echo GPU: Not detected
    echo CUDA: Not available
    echo Device: CPU
)

echo.
echo Starting backend server...
start /b cmd /c "cd /d %~dp0\.. && call venv\Scripts\activate.bat && python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload"

:: Wait for backend to start
echo Waiting for backend...
timeout /t 3 /nobreak >nul

echo Starting frontend...
start /b cmd /c "cd /d %~dp0\..\frontend && npm run dev"

:: Wait for frontend to start
timeout /t 3 /nobreak >nul

echo.
echo ============================================================
echo   Local AI Voice Studio is running!
echo ============================================================
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://127.0.0.1:8000
echo   API Docs:  http://127.0.0.1:8000/docs
echo.
echo   Press Ctrl+C to stop.
echo ============================================================
echo.

:: Open browser
start http://localhost:5173

:: Keep window open
echo Press any key to stop the server...
pause >nul

:: Kill processes
taskkill /f /im "node.exe" >nul 2>&1
taskkill /f /im "python.exe" >nul 2>&1
echo Servers stopped.
