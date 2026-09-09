@echo off
chcp 65001 >nul
echo ========================================
echo   PHM鍋ュ悍绠＄悊骞冲彴 - 绯荤粺鍚姩
echo ========================================
echo.

echo 姝ｅ湪鍚姩绯荤粺...
echo.

REM 妫€鏌ython鐜
python --version >nul 2>&1
if errorlevel 1 (
    echo 鉂?Python鏈畨瑁呮垨涓嶅湪PATH涓?
    echo 璇峰厛瀹夎Python 3.10+
    pause
    exit /b 1
)

REM 妫€鏌ヨ櫄鎷熺幆澧?
if not exist ".venv" (
    echo 鉂?铏氭嫙鐜涓嶅瓨鍦?
    echo 璇峰厛杩愯: python scripts/migration_setup.py
    pause
    exit /b 1
)

REM 婵€娲昏櫄鎷熺幆澧冨苟鍚姩绯荤粺
echo 馃殌 鍚姩PHM鍋ュ悍绠＄悊骞冲彴...
echo.

.venv\Scripts\python.exe scripts\start_system.py

echo.
echo 绯荤粺宸插仠姝㈣繍琛?
pause

