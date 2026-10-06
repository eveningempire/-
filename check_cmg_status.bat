@echo off
chcp 65001 >nul
title PHM 平台状态检查

echo.
echo ========================================
echo    PHM 平台服务状态检查
echo ========================================
echo.

echo [1/3] 检查 Redis 服务状态...
tasklist /fi "imagename eq redis-server.exe" 2>nul | find /i "redis-server.exe" >nul
if %errorlevel% equ 0 (echo    [OK] Redis 服务正在运行) else (echo    [INFO] Redis 服务未运行(离线模式可不启用))
echo.

echo [2/3] 检查 Django 后端服务状态...
curl -s http://127.0.0.1:8000/ >nul 2>&1
if %errorlevel% equ 0 (echo    [OK] Django 服务响应正常) else (echo    [ERROR] Django 服务未运行或尚未启动)
echo.

echo [3/3] 检查平台端口...
netstat -ano | findstr ":8000 " >nul 2>&1
if %errorlevel% equ 0 (echo    [OK] 8000 端口正在监听) else (echo    [ERROR] 未检测到 8000 端口)
echo.
echo ========================================
echo 状态检查完成
echo ========================================
echo 如果发现问题,请先运行 stop_phm_platform.bat,再运行 start_phm_platform.bat。
pause
