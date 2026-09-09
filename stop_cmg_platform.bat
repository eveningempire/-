@echo off
setlocal
cd /d "%~dp0"
echo Stopping PHM services on ports 5173, 8000 and 6379...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports=5173,8000,6379; $ids=Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue ^| Where-Object { $ports -contains $_.LocalPort } ^| Select-Object -ExpandProperty OwningProcess -Unique; foreach($id in $ids){ Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }; Write-Host 'PHM services stopped.'"
endlocal

