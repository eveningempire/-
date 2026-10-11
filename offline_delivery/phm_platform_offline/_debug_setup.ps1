param([switch]$SkipFrontend)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host 'PHM migration setup (offline)' -ForegroundColor Cyan
function Find-Python310 {
  $candidates = @()
  $bundledRuntime = Join-Path $Root 'runtime\python310\python.exe'
  if (Test-Path -LiteralPath $bundledRuntime -PathType Leaf) { $candidates += $bundledRuntime }
  $launcher = Get-Command py -ErrorAction SilentlyContinue
  if ($launcher) {
    try {
      $launcherPath = & $launcher.Source -3.10 -c 'import sys; print(sys.executable)' 2>$null | Select-Object -Last 1
      if ($LASTEXITCODE -eq 0 -and $launcherPath) { $candidates += [string]$launcherPath }
    } catch { }
  }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python -and $python.Source) { $candidates += $python.Source }
  if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python310\python.exe') }
  if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python310-64\python.exe') }
  if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles 'Python310\python.exe') }
  if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Python310\python.exe') }
  foreach ($key in @('HKCU:\Software\Python\PythonCore\3.10\InstallPath', 'HKLM:\Software\Python\PythonCore\3.10\InstallPath', 'HKLM:\Software\WOW6432Node\Python\PythonCore\3.10\InstallPath')) {
    try {
      $installPath = (Get-ItemProperty -LiteralPath $key -ErrorAction Stop).'(default)'
      if ($installPath) { $candidates += (Join-Path ([string]$installPath) 'python.exe') }
    } catch { }
  }
  if ($env:LOCALAPPDATA) {
    try { $candidates += Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'Programs\Python') -Filter 'python.exe' -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'Python310' } | Select-Object -ExpandProperty FullName } catch { }
  }
  foreach ($candidate in $candidates) {
    if (-not $candidate -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    try {
      $version = & $candidate -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))' 2>$null | Select-Object -Last 1
      if ($LASTEXITCODE -eq 0 -and ([string]$version).Trim() -eq '3.10') { return $candidate }
    } catch { }
  }
  return $null
}
$Py = Join-Path $Root '.venv\Scripts\python.exe'
$venvReady = $false
$venvVersion = $null
if (Test-Path -LiteralPath $Py -PathType Leaf) {
  try {
    $venvVersion = & $Py -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))' 2>$null | Select-Object -Last 1
    if ($LASTEXITCODE -eq 0 -and ([string]$venvVersion).Trim() -eq '3.10') {
      & $Py -c 'import django, daphne, channels, redis, pywt' *> $null
      $venvReady = ($LASTEXITCODE -eq 0)
    }
  } catch { }
}
if (-not $venvReady -and (Test-Path -LiteralPath (Join-Path $Root '.venv'))) {
  $backup = Join-Path $Root ('.venv-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
  Move-Item -LiteralPath (Join-Path $Root '.venv') -Destination $backup
  Write-Host "Bundled .venv is not usable here; preserved at $backup" -ForegroundColor Yellow
}
if (-not (Test-Path -LiteralPath $Py -PathType Leaf)) {
  $python310 = Find-Python310; Write-Host "DEBUG PY=<$python310>"
  if (-not $python310) {
    $installer = Join-Path $Root 'runtime-installers\python-3.10.11-amd64.exe'
    if (Test-Path -LiteralPath $installer -PathType Leaf) {
      Write-Host 'Python 3.10 not found. Installing the bundled runtime locally...' -ForegroundColor Yellow
      # Use a package-local target so the next step does not depend on PATH,
      # the Python launcher, or registry entries on the destination VM.
      $runtimeDir = Join-Path $Root 'runtime\python310'
      New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
      # The project invokes python.exe directly; installing the optional
      # Python Launcher can fail with MSI 1603 when another launcher exists.
      $arguments = @('/quiet', 'InstallAllUsers=0', "TargetDir=`"$runtimeDir`"", 'PrependPath=0', 'Include_launcher=0', 'Include_test=0')
      $install = Start-Process $installer -ArgumentList $arguments -Wait -PassThru
      if ($install.ExitCode -ne 0) { throw "Python 3.10 installer failed with exit code $($install.ExitCode)." }
      $python310 = Find-Python310; Write-Host "DEBUG PY=<$python310>"
    }
    if (-not $python310) { throw "Python installer finished, but no usable Python 3.10 was found. Check $runtimeDir or %LOCALAPPDATA%\Programs\Python\Python310\python.exe, then rerun this script." }
  }
  Write-Host 'Creating Python 3.10 virtual environment...' -ForegroundColor Cyan
  & $python310 -m venv (Join-Path $Root '.venv')
  if ($LASTEXITCODE -ne 0) { throw 'Failed to create .venv. Verify that the Python 3.10 installation includes the standard library and venv module.' }
}
if (-not (Test-Path $Py)) { throw "Virtual environment was not created at $Py. Run install_runtime_offline.bat, reopen PowerShell, and retry." }
if ($venvReady) {
  Write-Host 'Bundled Python environment is available; skipping package download.' -ForegroundColor Green
  if (-not (Test-Path 'db.sqlite3')) { & $Py manage.py migrate }
  if (-not (Test-Path 'media')) { New-Item -ItemType Directory media | Out-Null }
  Write-Host 'Setup complete. Run start_phm_platform.bat.' -ForegroundColor Green
  exit 0
}
if (-not (Get-ChildItem -LiteralPath 'offline\python' -Filter '*.whl' -File -ErrorAction SilentlyContinue | Select-Object -First 1)) { throw 'Offline Python wheels are missing from offline\python. Use the corrected delivery package.' }
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
if (-not $SkipFrontend -and -not (Test-Path 'frontend\dist\index.html')) {
  if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw 'Node.js 18+ and npm are required when frontend\dist is missing.' }
  if (-not (Test-Path 'frontend\node_modules')) {
    & npm ci --offline --prefix frontend
    if ($LASTEXITCODE -ne 0) { throw 'Offline frontend dependency installation failed. The system was not started.' }
  }
  & npm run build --prefix frontend
  if ($LASTEXITCODE -ne 0) { throw 'Offline frontend build failed. The system was not started.' }
}
if (-not (Test-Path 'db.sqlite3')) { & $Py manage.py migrate }
if (-not (Test-Path 'media')) { New-Item -ItemType Directory media | Out-Null }
Write-Host 'Setup complete. Run start_phm_platform.bat.' -ForegroundColor Green


