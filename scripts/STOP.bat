@echo off
REM =========================================================
REM  STOP.bat — Stop the TVA Barkley Weld Inspector
REM  Double-click this file to stop the running server.
REM =========================================================

echo Stopping TVA Weld Inspector...

set ROOT_DIR=%~dp0
set PID_FILE=%ROOT_DIR%server.pid

REM If a PID file exists (written by START.bat), kill that specific process
if exist "%PID_FILE%" (
    set /p SERVER_PID=<"%PID_FILE%"
    echo Stopping server process (PID: %SERVER_PID%)...
    taskkill /F /PID %SERVER_PID% >nul 2>&1
    del "%PID_FILE%" >nul 2>&1
) else (
    REM Fallback: kill the portable python.exe by full path using wmic
    set PYTHON_EXE=%ROOT_DIR%python\python.exe
    wmic process where "ExecutablePath='%PYTHON_EXE:\=\\%'" delete >nul 2>&1
)

echo TVA Weld Inspector has been stopped.
echo You can now close this window.
pause
