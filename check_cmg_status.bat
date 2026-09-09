@echo off
chcp 65001 >nul
title PHM骞冲彴鐘舵€佹鏌?

echo.
echo ========================================
echo    PHM 骞冲彴鏈嶅姟鐘舵€佹鏌?
echo ========================================
echo.

:: 妫€鏌edis鏈嶅姟
echo [1/3] 妫€鏌edis鏈嶅姟鐘舵€?..
tasklist /fi "imagename eq redis-server.exe" 2>nul | find /i "redis-server.exe" >nul
if %errorlevel% equ 0 (
    echo    鉁?Redis鏈嶅姟姝ｅ湪杩愯
    if exist "Redis-x64-5.0.14.1\redis-cli.exe" (
        cd Redis-x64-5.0.14.1
        redis-cli.exe ping >nul 2>&1
        if %errorlevel% equ 0 (
            echo    鉁?Redis杩炴帴姝ｅ父
        ) else (
            echo    鈿狅笍  Redis鏈嶅姟杩愯浣嗚繛鎺ュ紓甯?
        )
        cd ..
    )
) else (
    echo    鉂?Redis鏈嶅姟鏈繍琛?
)

echo.

:: 妫€鏌jango鏈嶅姟
echo [2/3] 妫€鏌jango鍚庣鏈嶅姟鐘舵€?..
tasklist /fi "imagename eq python.exe" 2>nul | find /i "python.exe" >nul
if %errorlevel% equ 0 (
    echo    鉁?Python杩涚▼姝ｅ湪杩愯
    
    :: 娴嬭瘯Django API
    curl -s http://localhost:8000/api/v1/data/cmgs/ >nul 2>&1
    if %errorlevel% equ 0 (
        echo    鉁?Django API鍝嶅簲姝ｅ父
    ) else (
        echo    鈿狅笍  Django鏈嶅姟鍙兘鏈畬鍏ㄥ惎鍔?
    )
) else (
    echo    鉂?Django鍚庣鏈嶅姟鏈繍琛?
)

echo.

:: 妫€鏌ュ墠绔湇鍔?
echo [3/3] 妫€鏌ュ墠绔紑鍙戞湇鍔″櫒鐘舵€?..
tasklist /fi "imagename eq node.exe" 2>nul | find /i "node.exe" >nul
if %errorlevel% equ 0 (
    echo    鉁?Node.js杩涚▼姝ｅ湪杩愯
    
    :: 娴嬭瘯鍓嶇鏈嶅姟
    curl -s http://localhost:3000 >nul 2>&1
    if %errorlevel% equ 0 (
        echo    鉁?鍓嶇鏈嶅姟鍝嶅簲姝ｅ父
    ) else (
        echo    鈿狅笍  鍓嶇鏈嶅姟鍙兘鏈畬鍏ㄥ惎鍔?
    )
) else (
    echo    鉂?鍓嶇寮€鍙戞湇鍔″櫒鏈繍琛?
)

echo.

:: 鏄剧ず绔彛浣跨敤鎯呭喌
echo 馃搳 绔彛浣跨敤鎯呭喌:
netstat -an | findstr ":6379 :8000 :3000" 2>nul
if %errorlevel% neq 0 (
    echo    鈩癸笍  鏈娴嬪埌鏈嶅姟绔彛鍗犵敤
)

echo.

:: 濡傛灉鏈塩url锛屾祴璇曞畬鏁寸殑鏈嶅姟閾?
where curl >nul 2>&1
if %errorlevel% equ 0 (
    echo 馃敆 娴嬭瘯鏈嶅姟杩炴帴鎬?..
    
    :: 娴嬭瘯Redis缂撳瓨鐘舵€丄PI
    curl -s http://localhost:8000/api/v1/data/data/cache-stats/ | findstr "redis_connected" >nul 2>&1
    if %errorlevel% equ 0 (
        echo    鉁?Redis缂撳瓨闆嗘垚姝ｅ父
    ) else (
        echo    鈿狅笍  Redis缂撳瓨闆嗘垚鍙兘鏈夐棶棰?
    )
)

echo.
echo ========================================
echo 馃弫 鐘舵€佹鏌ュ畬鎴?
echo ========================================
echo.
echo 馃挕 璇存槑:
echo    鉁?= 鏈嶅姟姝ｅ父杩愯
echo    鈿狅笍  = 鏈嶅姟杩愯浣嗗彲鑳芥湁闂  
echo    鉂?= 鏈嶅姟鏈繍琛?
echo.
echo 馃搵 濡傛灉鍙戠幇闂:
echo    1. 杩愯 stop_cmg_platform.bat 鍋滄鎵€鏈夋湇鍔?
echo    2. 绛夊緟鍑犵閽?
echo    3. 杩愯 start_cmg_platform.bat 閲嶆柊鍚姩
echo.
pause

