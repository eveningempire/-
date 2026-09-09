@echo off
chcp 65001 >nul
echo ============================================================
echo  PHM骞冲彴蹇€熻缃剼鏈?
echo ============================================================
echo.

:: 妫€鏌ユ槸鍚﹀湪椤圭洰鏍圭洰褰?
if not exist "manage.py" (
    echo 鉂?閿欒锛氳鍦ㄩ」鐩牴鐩綍杩愯姝よ剼鏈?
    echo 褰撳墠鐩綍锛?CD%
    pause
    exit /b 1
)

:: 鍒涘缓铏氭嫙鐜
if not exist ".venv" (
    echo 馃敡 鍒涘缓铏氭嫙鐜...
    python -m venv .venv
    if errorlevel 1 (
        echo 鉂?鍒涘缓铏氭嫙鐜澶辫触
        pause
        exit /b 1
    )
    echo 鉁?铏氭嫙鐜鍒涘缓鎴愬姛
)

:: 婵€娲昏櫄鎷熺幆澧?
echo.
echo 馃攧 婵€娲昏櫄鎷熺幆澧?..
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo 鉂?婵€娲昏櫄鎷熺幆澧冨け璐?
    pause
    exit /b 1
)

:: 妫€鏌ython渚濊禆
echo.
echo 馃摝 妫€鏌ython渚濊禆...
python -c "import django" 2>nul
if errorlevel 1 (
    echo 鈿狅笍  Django鏈畨瑁咃紝姝ｅ湪瀹夎渚濊禆...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 鉂?瀹夎渚濊禆澶辫触
        pause
        exit /b 1
    )
    echo 鉁?渚濊禆瀹夎瀹屾垚
) else (
    echo 鉁?Python渚濊禆宸插畨瑁?
)

:: 妫€鏌ユ暟鎹簱杩炴帴
echo.
echo 馃攳 妫€鏌ユ暟鎹簱杩炴帴...
python manage.py check --database default
if errorlevel 1 (
    echo 鈿狅笍  鏁版嵁搴撹繛鎺ユ鏌ュけ璐ワ紝璇锋鏌ユ暟鎹簱閰嶇疆
    echo 璇风‘淇濓細
    echo 1. MySQL鏈嶅姟姝ｅ湪杩愯
    echo 2. 鏁版嵁搴撻厤缃纭紙phm_backend/settings.py锛?
    echo 3. 鏁版嵁搴撶敤鎴锋湁瓒冲鏉冮檺
    echo.
    set /p continue="鏄惁缁х画锛?y/N): "
    if /i not "%continue%"=="y" (
        pause
        exit /b 1
    )
) else (
    echo 鉁?鏁版嵁搴撹繛鎺ユ甯?
)

:: 妫€鏌ヨ縼绉荤姸鎬?
echo.
echo 馃攧 妫€鏌ユ暟鎹簱杩佺Щ鐘舵€?..
python manage.py showmigrations
if errorlevel 1 (
    echo 鈿狅笍  杩佺Щ鐘舵€佹鏌ュけ璐?
) else (
    echo 鉁?杩佺Щ鐘舵€佹鏌ュ畬鎴?
)

:: 鍒涘缓绠＄悊鍛樿处鍙?
echo.
echo 馃懁 鍒涘缓绠＄悊鍛樿处鍙?..
echo 璇锋寜鎻愮ず杈撳叆绠＄悊鍛樿处鍙蜂俊鎭細
python scripts\setup_admin.py --create

:: 妫€鏌ュ墠绔緷璧?
echo.
echo 馃摝 妫€鏌ュ墠绔緷璧?..
if exist "frontend\node_modules" (
    echo 鉁?鍓嶇渚濊禆宸插畨瑁?
) else (
    echo 鈿狅笍  鍓嶇渚濊禆鏈畨瑁咃紝姝ｅ湪瀹夎...
    cd frontend
    npm install
    if errorlevel 1 (
        echo 鉂?鍓嶇渚濊禆瀹夎澶辫触
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo 鉁?鍓嶇渚濊禆瀹夎瀹屾垚
)

echo.
echo ============================================================
echo  鉁?璁剧疆瀹屾垚锛?
echo ============================================================
echo.
echo 馃敆 璁块棶鍦板潃:
echo    - 绠＄悊鍚庡彴: http://localhost:8000/admin/
echo    - 鍓嶇鐣岄潰: http://localhost:3000
echo    - API鎺ュ彛: http://localhost:8000/api/v1/
echo.
echo 馃殌 鍚姩鏈嶅姟:
echo    鍚庣: python manage.py runserver
echo    鍓嶇: cd frontend ^&^& npm run dev
echo.
echo 馃搵 鍏朵粬鍛戒护:
echo    - 鏌ョ湅鐢ㄦ埛: python scripts\setup_admin.py --list
echo    - 閲嶇疆瀵嗙爜: python scripts\setup_admin.py --reset
echo    - 鐢ㄦ埛绠＄悊: python scripts\setup_admin.py --interactive
echo.
pause

