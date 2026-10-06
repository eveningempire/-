@echo off
setlocal
cd /d "%~dp0"
chcp 65001 >nul
echo Installing PyYAML for Hier14...
if not exist ".venv\Scripts\python.exe" (
  echo [ERROR] .venv was not found. Run the offline setup first.
  pause
  exit /b 1
)
if not exist "offline\python\PyYAML-6.0.2-cp310-cp310-win_amd64.whl" (
  echo [ERROR] PyYAML wheel was not found in offline\python.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m pip install --no-index --find-links "%CD%\offline\python" PyYAML==6.0.2
if errorlevel 1 (
  echo [ERROR] PyYAML installation failed.
  pause
  exit /b 1
)
.venv\Scripts\python.exe -c "import yaml; print('PyYAML OK:', yaml.__version__)"
if errorlevel 1 (
  echo [ERROR] yaml import verification failed.
  pause
  exit /b 1
)
echo Hier14 dependency fixed. Restart the platform with start_cmg_platform.bat.
pause
