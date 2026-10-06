@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo PHM Platform administrator setup
if not exist "runtime\python310\python.exe" (
  echo [ERROR] Bundled Python 3.10 runtime was not found.
  pause
  exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Preparing the offline Python environment...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_migration.ps1" -SkipFrontend
  if errorlevel 1 exit /b 1
)

".venv\Scripts\python.exe" manage.py createsuperuser
if errorlevel 1 (
  echo.
  echo [ERROR] Administrator creation failed.
  pause
  exit /b 1
)
endlocal
