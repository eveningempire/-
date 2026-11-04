@echo off
setlocal
cd /d "%~dp0"
set "PHM_PYTHON=%~dp0.venv\Scripts\python.exe"
if not exist "%PHM_PYTHON%" set "PHM_PYTHON=%~dp0runtime\python310\python.exe"
"%PHM_PYTHON%" manage.py import_simulation_datasets --include-baseline
if errorlevel 1 goto failed
echo Real simulation data imported. Refresh the dataset page.
pause
exit /b 0
:failed
echo Import failed. Run start_phm_platform.bat first and review the error above.
pause
exit /b 1
