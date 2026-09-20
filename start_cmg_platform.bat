@echo off
setlocal
chcp 65001 >nul
title PHM Platform Launcher
cd /d "%~dp0"

echo.
echo ========================================
echo   PHM Platform - One-click launcher
echo ========================================
echo.

if not exist "manage.py" (
    echo [ERROR] manage.py was not found.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment .venv was not found.
    pause
    exit /b 1
)

echo [1/4] Checking packaged frontend...
if not exist "frontend\dist\index.html" (
    echo [INFO] Packaged frontend was not found; a local build is required.
    where npm >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Install Node.js and npm, or restore frontend\dist.
        pause
        exit /b 1
    )
    if not exist "frontend\node_modules" (
        pushd frontend
        call npm install
        if errorlevel 1 (
            popd
            echo [ERROR] npm install failed.
            pause
            exit /b 1
        )
        popd
    )
    echo [2/4] Building frontend...
    pushd frontend
    call npm run build
    if errorlevel 1 (
        popd
        echo [ERROR] Frontend build failed.
        pause
        exit /b 1
    )
    popd
) else (
    echo [2/4] Using packaged frontend build.
)

set "USE_SQLITE=true"
set "DJANGO_DEBUG=True"

echo [3/4] Updating database...
call ".venv\Scripts\python.exe" manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] Database migration failed.
    pause
    exit /b 1
)

for /f "tokens=*" %%P in ('powershell -NoProfile -Command "(Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess"') do set "PORT_PID=%%P"
if defined PORT_PID (
    echo [INFO] Checking the process currently using port 8000...
    powershell -NoProfile -Command "$processId=%PORT_PID%; $command=(Get-CimInstance Win32_Process -Filter ('ProcessId=' + $processId)).CommandLine; if ($command -match 'manage\.py\s+runserver' -or $command -match 'daphne.*phm_backend') { Stop-Process -Id $processId -Force; exit 0 } else { exit 2 }"
    if errorlevel 2 (
        echo [ERROR] Port 8000 is occupied by another program, process %PORT_PID%.
        echo Close that program and run this launcher again.
        pause
        exit /b 1
    )
    timeout /t 1 /nobreak >nul
)

echo [4/4] Starting platform at http://127.0.0.1:8000/ ...
start "PHM Platform Server" cmd /k "cd /d ""%~dp0"" && set USE_SQLITE=true && set DJANGO_DEBUG=True && .venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000"

timeout /t 3 /nobreak >nul
start "" "http://127.0.0.1:8000/"

echo.
echo Platform started successfully.
echo Address: http://127.0.0.1:8000/
echo Redis and port 5173 are not required for normal use.
echo.
pause
