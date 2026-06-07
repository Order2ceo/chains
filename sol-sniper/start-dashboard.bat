@echo off
REM ============================================================
REM  SOL Sniper Bot - Dashboard (optional, for monitoring)
REM  The bot trades from the backend alone; this is just the UI.
REM  Double-click to launch the dashboard at http://localhost:5173
REM ============================================================
cd /d "%~dp0frontend"

if not exist "node_modules" (
    echo [setup] Installing frontend dependencies (first run)...
    call npm install
)

echo.
echo [start] Dashboard at http://localhost:5173  (Ctrl+C to stop)
echo.
call npm run dev

pause
