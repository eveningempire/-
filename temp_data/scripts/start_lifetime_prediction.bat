@echo off
echo ========================================
echo PHM鍋ュ悍绠＄悊骞冲彴 - 瀵垮懡棰勬祴鍔熻兘鍚姩
echo ========================================
echo.

echo 1. 婵€娲昏櫄鎷熺幆澧?..
call .venv\Scripts\activate

echo.
echo 2. 鍚姩Django鍚庣鏈嶅姟鍣?..
start "Django Backend" cmd /k "python manage.py runserver"

echo.
echo 3. 绛夊緟鍚庣鍚姩瀹屾垚...
timeout /t 3 /nobreak > nul

echo.
echo 4. 鍚姩鍓嶇寮€鍙戞湇鍔″櫒...
cd frontend
start "Frontend Dev Server" cmd /k "npm run dev"

echo.
echo ========================================
echo 鍚姩瀹屾垚锛?
echo ========================================
echo.
echo 鍚庣鏈嶅姟: http://localhost:8000
echo 鍓嶇鏈嶅姟: http://localhost:3000
echo 瀵垮懡棰勬祴椤甸潰: http://localhost:3000/lifetime-prediction
echo.
echo API娴嬭瘯:
echo - 鍋ュ悍妫€鏌? http://localhost:8000/api/v1/lifetime/health/
echo - PHM鍒楄〃: http://localhost:8000/api/v1/lifetime/cmgs/
echo.
echo 鎸変换鎰忛敭閫€鍑?..
pause > nul

