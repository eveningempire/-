param([switch]$SkipFrontend)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host 'PHM migration setup (offline)' -ForegroundColor Cyan
function Find-Python310 {
  $launcher = Get-Command py -ErrorAction SilentlyContinue
  if ($launcher) {
    try {
      $launcherPath = (& py -3.10 -c "import sys; print(sys.executable)" 2>$null | Select-Object -Last 1).Trim()
      if ($launcherPath -and (Test-Path $launcherPath)) { return $launcherPath }
    } catch { }
  }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python) {
    $version = (& python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim()
    if ($version -eq '3.10') { return $python.Source }
  }
  return $null
}
$python310 = Find-Python310
if (-not $python310) {
  $installer = Join-Path $Root 'runtime-installers\python-3.10.11-amd64.exe'
  if (Test-Path $installer) {
    Write-Host 'Python 3.10 not found. Starting the bundled offline installer...' -ForegroundColor Yellow
    Start-Process $installer -ArgumentList 'InstallAllUsers=0 PrependPath=1 Include_test=0' -Wait
    throw 'Python 3.10 was installed. Close this terminal, open a new one, and run setup_migration.ps1 again.'
  }
  throw 'Python 3.10 is required; the bundled installer is missing.'
}
if (-not (Test-Path '.venv\Scripts\python.exe')) {
  Write-Host 'Creating Python 3.10 virtual environment...' -ForegroundColor Cyan
  & $python310 -m venv (Join-Path $Root '.venv')
  if ($LASTEXITCODE -ne 0) { throw 'Failed to create .venv. Verify that the Python 3.10 installation includes the standard library and venv module.' }
}
$Py = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $Py)) { throw "Virtual environment was not created at $Py. Run install_runtime_offline.bat, reopen PowerShell, and retry." }
if (-not (Test-Path 'offline\python')) { throw 'offline\python is missing. Build the package with build_offline_bundle.ps1 first.' }
$pipAvailable = $true
try { & $Py -m pip --version *> $null } catch { $pipAvailable = $false }
if (-not $pipAvailable -or $LASTEXITCODE -ne 0) {
  Write-Host 'pip is missing in .venv; bootstrapping pip from Python ensurepip...' -ForegroundColor Yellow
  & $Py -m ensurepip --upgrade --default-pip
  if ($LASTEXITCODE -ne 0) { throw 'Python ensurepip is unavailable. Reinstall Python 3.10.11 with the standard library and pip components.' }
}
& $Py -m pip install --no-index --find-links (Join-Path $Root 'offline\python') -r requirements-migration.txt
if ($LASTEXITCODE -ne 0) { throw 'Offline Python dependency installation failed. The system was not started; review the pip error above.' }
& $Py -c "import django, daphne, channels, redis, pywt; print('Python dependencies OK; PyWavelets='+pywt.__version__)"
if ($LASTEXITCODE -ne 0) { throw 'Python dependency verification failed. The system was not started.' }
if (-not $SkipFrontend) {
  if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Node.js 18+ and npm are required for frontend rebuilds.' }
  if (-not (Test-Path 'frontend\node_modules')) {
    & npm ci --offline --prefix frontend
    if ($LASTEXITCODE -ne 0) { throw 'Offline frontend dependency installation failed. The system was not started.' }
  }
}
if (-not (Test-Path 'db.sqlite3')) { & $Py manage.py migrate }
if (-not (Test-Path 'media')) { New-Item -ItemType Directory media | Out-Null }
Write-Host 'Setup complete. Run start_migration.bat.' -ForegroundColor Green

