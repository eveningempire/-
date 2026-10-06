@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"
title PHM Offline Setup (bundled Python)

set "RUNTIME=%CD%\runtime\python310\python.exe"
set "VENV=%CD%\.venv\Scripts\python.exe"

echo PHM migration setup (bundled runtime only)
if not exist "%RUNTIME%" (
  echo [ERROR] Bundled Python was not found:
  echo         %RUNTIME%
  echo Extract the runtime patch into this folder and retry.
  pause
  exit /b 1
)

"%RUNTIME%" -V
if errorlevel 1 (
  echo [ERROR] Bundled Python cannot start.
  pause
  exit /b 1
)

if exist "%VENV%" (
  "%VENV%" -V >nul 2>&1
  if errorlevel 1 (
    echo [INFO] Existing .venv is unusable; preserving it.
    move ".venv" ".venv-backup-%RANDOM%" >nul
  )
)

if not exist "%VENV%" (
  echo Creating Python virtual environment...
  "%RUNTIME%" -m venv "%CD%\.venv"
  if errorlevel 1 (
    echo [ERROR] Could not create .venv from bundled Python.
    pause
    exit /b 1
  )
)

if not exist "offline\python\*.whl" (
  echo [ERROR] Offline wheels are missing from offline\python.
  pause
  exit /b 1
)

"%VENV%" -m ensurepip --upgrade --default-pip >nul 2>&1
"%VENV%" -m pip install --no-index --find-links "%CD%\offline\python" -r "%CD%\requirements-migration.txt"
if errorlevel 1 (
  echo [ERROR] Offline dependency installation failed.
  pause
  exit /b 1
)

"%VENV%" -c "import django, daphne, channels, redis, pywt, yaml"
if errorlevel 1 (
  echo [ERROR] Python dependency verification failed.
  pause
  exit /b 1
)

if not exist "db.sqlite3" "%VENV%" manage.py migrate --noinput
if not exist "media" mkdir media
echo Setup complete. Run start_cmg_platform.bat.
pause
