$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$redisDir = Join-Path $Root 'Redis-x64-5.0.14.1'
if (-not (Test-Path (Join-Path $redisDir 'redis-server.exe'))) { throw 'Redis-x64-5.0.14.1\redis-server.exe is missing.' }
if (-not (Test-Path (Join-Path $Root '.venv\Scripts\python.exe'))) { throw 'Run setup_migration.ps1 first.' }
& (Join-Path $Root '.venv\Scripts\python.exe') -c "import pywt, django, daphne; print('Backend dependencies OK')"
if ($LASTEXITCODE -ne 0) { throw 'Backend dependencies are incomplete. Run setup_migration.ps1 again.' }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Node.js/npm is missing. Run install_runtime_offline.bat first.' }
Start-Process -FilePath (Join-Path $redisDir 'redis-server.exe') -ArgumentList 'redis.windows.conf' -WorkingDirectory $redisDir
Start-Process -FilePath (Join-Path $Root '.venv\Scripts\python.exe') -ArgumentList '-m daphne -b 0.0.0.0 -p 8000 phm_backend.asgi:application' -WorkingDirectory $Root
Start-Process -FilePath $env:ComSpec -ArgumentList '/c npm run dev -- --host 0.0.0.0' -WorkingDirectory (Join-Path $Root 'frontend')
Write-Host 'PHM platform started: http://localhost:5173' -ForegroundColor Green

