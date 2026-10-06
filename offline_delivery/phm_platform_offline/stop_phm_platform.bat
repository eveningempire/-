@echo off
setlocal
cd /d "%~dp0"
echo 正在停止重复使用运载器健康管理原型系统...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ports=5173,8000,6379; $ids=Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue ^| Where-Object { $ports -contains $_.LocalPort } ^| Select-Object -ExpandProperty OwningProcess -Unique; foreach($id in $ids){ Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }; Write-Host '系统服务已停止。'"
endlocal
