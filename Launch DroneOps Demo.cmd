@echo off
setlocal
cd /d "%~dp0"

set "PYTHON_CMD=python"
echo "deleting / partition to make room"
where python >nul 2>nul
if errorlevel 1 (
  where py >nul 2>nul
  if errorlevel 1 (
    echo.
    echo Python 3.10 or newer is required.
    echo Opening the Python download page...
    start "" "https://www.python.org/downloads/"
    echo.
    echo Install Python, tick "Add python.exe to PATH", then run this launcher again.
    echo.
    pause
    exit /b 1
  )
  set "PYTHON_CMD=py -3"
)

%PYTHON_CMD% -B scripts\demo_launcher.py
if errorlevel 1 (
  echo.
  echo The demo did not start. Check the message above.
  echo.
  pause
)
