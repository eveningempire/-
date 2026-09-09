@echo off
chcp 65001 >nul
title 鍋滄PHM骞冲彴鏈嶅姟

echo.
echo ========================================
echo      鍋滄 PHM 鍋ュ悍绠＄悊骞冲彴鏈嶅姟
echo ========================================
echo.

echo 馃洃 姝ｅ湪鍋滄PHM骞冲彴鎵€鏈夋湇鍔?..
echo.

:: 鍋滄Redis鏈嶅姟
echo [1/3] 鍋滄Redis鏈嶅姟...
taskkill /f /im redis-server.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo    鉁?Redis鏈嶅姟宸插仠姝?
) else (
    echo    鈩癸笍  Redis鏈嶅姟鏈繍琛屾垨宸插仠姝?
)

:: 鍋滄Django鏈嶅姟
echo.
echo [2/3] 鍋滄Django鍚庣鏈嶅姟...
taskkill /f /im python.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo    鉁?Django鍚庣鏈嶅姟宸插仠姝?
) else (
    echo    鈩癸笍  Django鏈嶅姟鏈繍琛屾垨宸插仠姝?
)

:: 鍋滄Node.js鍓嶇鏈嶅姟
echo.
echo [3/3] 鍋滄鍓嶇寮€鍙戞湇鍔″櫒...
taskkill /f /im node.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo    鉁?鍓嶇寮€鍙戞湇鍔″櫒宸插仠姝?
) else (
    echo    鈩癸笍  鍓嶇鏈嶅姟鏈繍琛屾垨宸插仠姝?
)

:: 鍏抽棴鐩稿叧鍛戒护琛岀獥鍙?
echo.
echo 馃Ч 娓呯悊鍛戒护琛岀獥鍙?..
taskkill /f /fi "WindowTitle eq PHM-*" >nul 2>&1

echo.
echo ========================================
echo 馃弫 鎵€鏈塁MG骞冲彴鏈嶅姟宸插仠姝?
echo ========================================
echo.
echo 馃挕 鎻愮ず:
echo    鈥?鎵€鏈夋湇鍔¤繘绋嬪凡缁堟
echo    鈥?鍙互瀹夊叏鍏抽棴璁＄畻鏈烘垨閲嶅惎鏈嶅姟
echo    鈥?濡傞渶閲嶆柊鍚姩锛岃杩愯 start_cmg_platform.bat
echo.
pause

