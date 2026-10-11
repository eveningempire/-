@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_phm_platform.ps1" %*
if errorlevel 1 goto failed
exit /b 0
:failed
echo PHM startup failed. See the error above.
pause
exit /b 1
