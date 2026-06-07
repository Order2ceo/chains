@echo off
REM ============================================================
REM  SOL Sniper Bot - Windows launcher
REM  Double-click this file to start the trading bot.
REM  Reads configuration from backend\.env
REM ============================================================
setlocal enabledelayedexpansion
cd /d "%~dp0backend"

REM --- First run: create the virtual environment + install deps ---
if not exist "venv\Scripts\python.exe" (
    echo [setup] Creating Python virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [error] Could not create venv. Is Python 3.12 installed and on PATH?
        pause
        exit /b 1
    )
    echo [setup] Installing dependencies...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM --- Load environment variables from backend\.env ---
if not exist ".env" (
    echo [error] backend\.env not found.
    echo         Copy backend\.env.example to backend\.env and fill in your values.
    pause
    exit /b 1
)
for /f "usebackq eol=# tokens=1,* delims==" %%a in (".env") do (
    if not "%%a"=="" set "%%a=%%b"
)

echo.
echo [start] Launching SOL Sniper Bot backend on http://localhost:8001
echo         LIVE_MODE=%LIVE_MODE%  AUTO_BUY_ENABLED=%AUTO_BUY_ENABLED%  BUY_AMOUNT_SOL=%BUY_AMOUNT_SOL%
echo         Press Ctrl+C to stop.
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8001

pause
