@echo off
setlocal
cd /d "%~dp0"
set "PHM_PYTHON=%~dp0runtime\python310\python.exe"
if not exist "%PHM_PYTHON%" set "PHM_PYTHON=%~dp0.venv\Scripts\python.exe"
"%PHM_PYTHON%" configure_matlab_engine.py
if errorlevel 1 goto failed
exit /b 0
:failed
echo MATLAB Engine setup failed. Check logs\matlab-engine-setup.log.
pause
exit /b 1
