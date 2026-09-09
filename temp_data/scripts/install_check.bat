@echo off
chcp 65001 >nul
echo ============================================================
echo    PHM鍋ュ悍绠＄悊骞冲彴 - 绯荤粺渚濊禆妫€鏌ヨ剼鏈?(Windows鐗堟湰)
echo    Control Moment Gyroscope Health Management System
echo ============================================================
echo.

REM 妫€鏌ython鏄惁瀹夎
echo 姝ｅ湪妫€鏌ython鐜...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [閿欒] Python鏈畨瑁呮垨鏈坊鍔犲埌PATH鐜鍙橀噺
    echo 璇峰畨瑁匬ython 3.8+骞剁‘淇濇坊鍔犲埌PATH
    pause
    exit /b 1
)

REM 妫€鏌ode.js鏄惁瀹夎
echo 姝ｅ湪妫€鏌ode.js鐜...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [閿欒] Node.js鏈畨瑁呮垨鏈坊鍔犲埌PATH鐜鍙橀噺
    echo 璇峰畨瑁匩ode.js 16+骞剁‘淇濇坊鍔犲埌PATH
    pause
    exit /b 1
)

REM 妫€鏌pm鏄惁瀹夎
echo 姝ｅ湪妫€鏌pm鐜...
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [閿欒] npm鏈畨瑁呮垨鏈坊鍔犲埌PATH鐜鍙橀噺
    echo 璇风‘淇漬pm宸叉纭畨瑁?
    pause
    exit /b 1
)

REM 妫€鏌ヨ櫄鎷熺幆澧?
echo 姝ｅ湪妫€鏌ヨ櫄鎷熺幆澧?..
if exist ".venv" (
    echo [淇℃伅] 妫€娴嬪埌.venv铏氭嫙鐜鐩綍
    echo 璇锋縺娲昏櫄鎷熺幆澧? .venv\Scripts\activate
) else (
    echo [璀﹀憡] 鏈娴嬪埌.venv铏氭嫙鐜鐩綍
    echo 寤鸿浣跨敤铏氭嫙鐜杩愯Python搴旂敤
)

REM 妫€鏌ラ」鐩枃浠?
echo 姝ｅ湪妫€鏌ラ」鐩枃浠?..
if not exist "phm_backend\settings.py" (
    echo [閿欒] 缂哄皯phm_backend\settings.py鏂囦欢
    pause
    exit /b 1
)

if not exist "frontend\package.json" (
    echo [閿欒] 缂哄皯frontend\package.json鏂囦欢
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo [閿欒] 缂哄皯requirements.txt鏂囦欢
    pause
    exit /b 1
)

if not exist "manage.py" (
    echo [閿欒] 缂哄皯manage.py鏂囦欢
    pause
    exit /b 1
)

echo [淇℃伅] 椤圭洰鏂囦欢妫€鏌ラ€氳繃

REM 杩愯Python妫€鏌ヨ剼鏈?
echo.
echo 姝ｅ湪杩愯璇︾粏鐨勭幆澧冩鏌?..
python install_check.py

echo.
echo 妫€鏌ュ畬鎴愶紒
echo 濡傛灉鎵€鏈夋鏌ラ兘閫氳繃锛屾偍鍙互寮€濮嬩娇鐢–MG鍋ュ悍绠＄悊骞冲彴
echo 濡傛灉瀛樺湪闂锛岃鏍规嵁涓婅堪鎻愮ず杩涜淇
pause


