@echo off
REM =========================================================
REM  SETUP_USER.bat — Create the first admin login
REM  Run this once before using the app for the first time.
REM =========================================================

setlocal

set PORTABLE_MODE=1

set ROOT_DIR=%~dp0
set PYTHON_EXE=%ROOT_DIR%python\python.exe
set APP_DIR=%ROOT_DIR%app

if not exist "%PYTHON_EXE%" (
    echo ERROR: Portable Python not found at %PYTHON_EXE%
    echo Please re-run the package_portable.py build script.
    pause
    exit /b 1
)

cd /d "%APP_DIR%"

echo =========================================================
echo  TVA Weld Inspector — Create Admin User
echo =========================================================
echo.
echo You will be prompted to enter a username, email address,
echo and password for the admin account.
echo.

"%PYTHON_EXE%" manage.py createsuperuser

echo.
echo Done! You can now log in at http://localhost:8000
echo Start the app first by running START.bat.
echo.
pause
