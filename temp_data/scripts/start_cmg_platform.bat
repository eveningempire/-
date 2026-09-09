@echo off
chcp 65001 >nul
title PHM鍋ュ悍绠＄悊骞冲彴鍚姩鍣?

echo.
echo ========================================
echo    PHM 鍋ュ悍绠＄悊骞冲彴 - 涓€閿惎鍔ㄨ剼鏈?
echo ========================================
echo.

:: 妫€鏌ユ槸鍚﹀湪姝ｇ‘鐨勭洰褰?
if not exist "manage.py" (
    echo 鉂?閿欒: 璇峰湪PHM椤圭洰鏍圭洰褰曚笅杩愯姝よ剼鏈?
    pause
    exit /b 1
)

:: 妫€鏌edis鐩綍
if not exist "Redis-x64-5.0.14.1" (
    echo 鉂?閿欒: 鏈壘鍒癛edis鐩綍 Redis-x64-5.0.14.1
    pause
    exit /b 1
)

:: 妫€鏌ヨ櫄鎷熺幆澧?
if not exist ".venv" (
    echo 鉂?閿欒: 鏈壘鍒拌櫄鎷熺幆澧冪洰褰?.venv
    pause
    exit /b 1
)

echo 馃殌 寮€濮嬪惎鍔–MG骞冲彴鏈嶅姟...
echo.

:: 1. 鍚姩Redis鏈嶅姟鍣?
echo [1/4] 鍚姩Redis鏈嶅姟鍣?..
start "PHM-Redis鏈嶅姟鍣? cmd /k "title Redis鏈嶅姟鍣?&& cd Redis-x64-5.0.14.1 && echo Starting Redis server... && redis-server.exe redis.windows.conf"

:: 绛夊緟Redis鍚姩
echo    绛夊緟Redis鏈嶅姟鍣ㄥ惎鍔?..
timeout 3 >nul

:: 娴嬭瘯Redis杩炴帴
echo    娴嬭瘯Redis杩炴帴...
cd Redis-x64-5.0.14.1
redis-cli.exe ping >nul 2>&1
if %errorlevel% neq 0 (
    echo    鈿狅笍  Redis鍙兘杩樺湪鍚姩涓紝缁х画绛夊緟...
    timeout 2 >nul
)
cd ..
echo    鉁?Redis鏈嶅姟鍣ㄥ凡鍚姩

:: 2. 鍚姩Django鍚庣 (浣跨敤ASGI鏈嶅姟鍣ㄦ敮鎸乄ebSocket)
echo.
echo [2/4] 鍚姩Django鍚庣鏈嶅姟鍣?(鏀寔WebSocket)...

:: 妫€鏌ヨ櫄鎷熺幆澧冧腑鏄惁瀹夎浜哾aphne
if not exist ".venv\Scripts\daphne.exe" (
    echo    馃摝 妫€娴嬪埌缂哄皯daphne锛屾鍦ㄥ畨瑁?..
    call .venv\Scripts\activate && pip install daphne
    if %errorlevel% neq 0 (
        echo    鉂?daphne瀹夎澶辫触锛屽皾璇曚娇鐢―jango寮€鍙戞湇鍔″櫒
        start "PHM-Django鍚庣" cmd /k "title Django鍚庣鏈嶅姟鍣?&& call .venv\Scripts\activate && echo Starting Django dev server... && python manage.py runserver 0.0.0.0:8000"
        goto :django_started
    )
)

:: 浣跨敤铏氭嫙鐜涓殑Python鏉ヨ繍琛宒aphne
start "PHM-Django鍚庣" cmd /k "title Django鍚庣鏈嶅姟鍣?ASGI) && call .venv\Scripts\activate && echo Starting Django backend with ASGI... && .venv\Scripts\python.exe -m daphne -b 0.0.0.0 -p 8000 phm_backend.asgi:application"

:django_started

:: 绛夊緟Django鍚姩
echo    绛夊緟Django鏈嶅姟鍣ㄥ惎鍔?..
timeout 4 >nul
echo    鉁?Django鍚庣鏈嶅姟鍣ㄥ凡鍚姩

:: 3. 妫€鏌ュ墠绔緷璧?
echo.
echo [3/4] 妫€鏌ュ墠绔幆澧?..
if exist "frontend\node_modules" (
    echo    鉁?鍓嶇渚濊禆宸插畨瑁?
) else (
    echo    馃摝 棣栨杩愯锛屾鍦ㄥ畨瑁呭墠绔緷璧?..
    cd frontend
    call npm install
    if %errorlevel% neq 0 (
        echo    鉂?鍓嶇渚濊禆瀹夎澶辫触
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo    鉁?鍓嶇渚濊禆瀹夎瀹屾垚
)

:: 4. 鍚姩鍓嶇寮€鍙戞湇鍔″櫒
echo.
echo [4/4] 鍚姩鍓嶇寮€鍙戞湇鍔″櫒...
start "PHM-鍓嶇寮€鍙戞湇鍔″櫒" cmd /k "title 鍓嶇寮€鍙戞湇鍔″櫒 && cd frontend && echo Starting frontend dev server... && npm run dev"

:: 绛夊緟鍓嶇鍚姩
echo    绛夊緟鍓嶇鏈嶅姟鍣ㄥ惎鍔?..
timeout 5 >nul

echo.
echo ========================================
echo 馃帀 PHM骞冲彴鍚姩瀹屾垚锛?
echo ========================================
echo.
echo 馃搵 鏈嶅姟鐘舵€?
echo    鈥?Redis鏈嶅姟鍣?      http://localhost:6379
echo    鈥?Django鍚庣:       http://localhost:8000
echo    鈥?鍓嶇寮€鍙戞湇鍔″櫒:   http://localhost:5173
echo.
echo 馃寪 璁块棶鍦板潃:
echo    鈥?骞冲彴棣栭〉:         http://localhost:5173
echo    鈥?鍚庣API:          http://localhost:8000/api/v1/
echo    鈥?绯荤粺鐘舵€佺洃鎺?     http://localhost:5173/system-status
echo.
echo 馃摑 浣跨敤璇存槑:
echo    1. 璇风瓑寰呮墍鏈夋湇鍔″畬鍏ㄥ惎鍔紙绾?0-15绉掞級
echo    2. 鍦ㄦ祻瑙堝櫒涓闂?http://localhost:5173
echo    3. 鍙互閫氳繃绯荤粺鐘舵€侀〉闈㈢洃鎺ф湇鍔″仴搴风姸鍐?
echo    4. 鍏抽棴鏃惰鍏抽棴鎵€鏈夊懡浠よ绐楀彛
echo.
echo 鈿狅笍  娉ㄦ剰浜嬮」:
echo    鈥?璇峰嬁鍏抽棴Redis鍜孌jango鐨勫懡浠よ绐楀彛
echo    鈥?濡傛灉閬囧埌绔彛鍗犵敤锛岃鍏堝叧闂浉鍏虫湇鍔?
echo    鈥?棣栨鍚姩鍙兘闇€瑕佹洿闀挎椂闂?
echo.

:: 璇㈤棶鏄惁鎵撳紑娴忚鍣?
set /p open_browser="鏄惁鑷姩鎵撳紑娴忚鍣? (Y/n): "
if /i "%open_browser%"=="n" goto :skip_browser
if /i "%open_browser%"=="no" goto :skip_browser

echo.
echo 馃寪 姝ｅ湪鎵撳紑娴忚鍣?..
timeout 3 >nul
start http://localhost:5173/

:skip_browser
echo.
echo 馃挕 鎻愮ず: 鎮ㄥ彲浠ラ殢鏃惰繍琛屾鑴氭湰鏉ュ惎鍔ㄥ钩鍙?
echo 馃搧 鏃ュ織鏂囦欢浣嶇疆: 鍚勬湇鍔＄殑鍛戒护琛岀獥鍙?
echo.
pause

