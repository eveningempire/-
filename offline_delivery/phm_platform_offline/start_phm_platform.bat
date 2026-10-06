@echo off
setlocal
chcp 65001 >nul
title 重复使用运载器健康管理原型系统
cd /d "%~dp0"
echo.
echo ========================================
echo   重复使用运载器健康管理原型系统
echo   一键启动
echo ========================================
echo.
if not exist "manage.py" (echo [错误] 未找到 manage.py。& pause& exit /b 1)
if not exist ".venv\Scripts\python.exe" (
  echo [提示] 未找到 Python 虚拟环境,正在执行离线环境设置...
  powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_migration.ps1"
  if errorlevel 1 (echo [错误] 离线环境设置失败。& pause& exit /b 1)
)
if not exist "frontend\dist\index.html" (
  echo [提示] 未找到前端成品,请确认交付包完整。
  if not exist "frontend\node_modules" (echo [错误] frontend\dist 和 node_modules 均缺失。& pause& exit /b 1)
  pushd frontend
  call npm run build
  if errorlevel 1 (popd& echo [错误] 前端构建失败。& pause& exit /b 1)
  popd
)
set "USE_SQLITE=true"
set "DJANGO_DEBUG=True"
call ".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 (echo [错误] 数据库迁移失败。& pause& exit /b 1)
for /f "tokens=*" %%P in ('powershell -NoProfile -Command "(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess"') do set "PORT_PID=%%P"
if defined PORT_PID (
  powershell -NoProfile -Command "$p=Get-CimInstance Win32_Process -Filter ('ProcessId=' + '%PORT_PID%'); if($p.CommandLine -match 'manage\.py\s+runserver|daphne.*phm_backend'){Stop-Process -Id %PORT_PID% -Force} else {exit 2}"
  if errorlevel 2 (echo [错误] 8000 端口已被其他程序占用。& pause& exit /b 1)
)
echo 正在启动 http://127.0.0.1:8000/ ...
start "重复使用运载器健康管理原型系统" cmd /k "cd /d ""%~dp0"" && set ""USE_SQLITE=true"" && set ""DJANGO_DEBUG=True"" && .venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000 --noreload"
timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000/"
echo 系统已启动,服务器窗口请勿关闭。
pause


