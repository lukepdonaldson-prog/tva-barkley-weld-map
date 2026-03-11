@echo off
REM =========================================================
REM  START.bat — Launch the TVA Barkley Weld Inspector
REM  Double-click this file to start the application.
REM =========================================================

setlocal

REM Set portable mode so the app uses SQLite and local paths
set PORTABLE_MODE=1

REM Determine the directory where this batch file lives
set ROOT_DIR=%~dp0

REM Path to the portable Python interpreter
set PYTHON_EXE=%ROOT_DIR%python\python.exe

REM Path to the Django project
set APP_DIR=%ROOT_DIR%app

REM Check that the portable Python exists
if not exist "%PYTHON_EXE%" (
    echo ERROR: Portable Python not found at %PYTHON_EXE%
    echo Please re-run the package_portable.py build script.
    pause
    exit /b 1
)

REM Change to the app directory
cd /d "%APP_DIR%"

REM Run database migrations (safe to run on every start)
echo Applying database migrations...
"%PYTHON_EXE%" manage.py migrate --run-syncdb
if errorlevel 1 (
    echo WARNING: Migration step reported an error. The app may still work.
)

REM Start the Django development server in the background
REM Binding to 0.0.0.0 allows access from other PCs on the same network.
REM Change to 127.0.0.1 if you want localhost-only access.
echo Starting TVA Weld Inspector server...
start "" /b "%PYTHON_EXE%" manage.py runserver 0.0.0.0:8000 --noreload

REM Give the process a moment to start, then capture its PID for STOP.bat
timeout /t 1 /nobreak >nul
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo list ^| find "PID:"') do (
    set SERVER_PID=%%i
)
if defined SERVER_PID (
    echo %SERVER_PID%>"%ROOT_DIR%server.pid"
)

REM Wait 3 seconds for the server to start up
timeout /t 3 /nobreak >nul

REM Open the app in the default browser
echo Opening browser at http://localhost:8000 ...
start "" "http://localhost:8000"

REM Keep this window open so the server keeps running
echo.
echo =========================================================
echo  TVA Weld Inspector is running at http://localhost:8000
echo.
echo  Close this window to STOP the server.
echo  Or double-click STOP.bat to stop it from another window.
echo =========================================================
echo.
pause
