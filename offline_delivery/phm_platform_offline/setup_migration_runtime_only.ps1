param([switch]$SkipFrontend)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

Write-Host 'PHM migration setup (bundled runtime only)' -ForegroundColor Cyan
$runtime = Join-Path $Root 'runtime\python310\python.exe'
if (-not (Test-Path -LiteralPath $runtime -PathType Leaf)) {
  throw "Bundled Python was not found: $runtime. Extract the runtime patch into this folder first."
}
$version = (& $runtime -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))' 2>&1 | Select-Object -Last 1)
if ($LASTEXITCODE -ne 0 -or ([string]$version).Trim() -ne '3.10') {
  throw "Bundled Python cannot run or is not Python 3.10: $runtime"
}
Write-Host "Using bundled Python: $runtime" -ForegroundColor Green

$venvDir = Join-Path $Root '.venv'
$py = Join-Path $venvDir 'Scripts\python.exe'
$venvReady = $false
if (Test-Path -LiteralPath $py -PathType Leaf) {
  try {
    $v = (& $py -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))' 2>$null | Select-Object -Last 1)
    if ($LASTEXITCODE -eq 0 -and ([string]$v).Trim() -eq '3.10') {
      & $py -c 'import django, daphne, channels, redis, pywt, yaml' *> $null
      $venvReady = ($LASTEXITCODE -eq 0)
    }
  } catch { }
}
if (-not $venvReady -and (Test-Path -LiteralPath $venvDir)) {
  $backup = Join-Path $Root ('.venv-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
  Move-Item -LiteralPath $venvDir -Destination $backup
  Write-Host "Old virtual environment moved to $backup" -ForegroundColor Yellow
}
if (-not $venvReady) {
  Write-Host 'Creating virtual environment from bundled Python...' -ForegroundColor Cyan
  & $runtime -m venv $venvDir
  if ($LASTEXITCODE -ne 0) { throw 'Could not create .venv from the bundled Python runtime.' }
}
if (-not (Test-Path -LiteralPath $py -PathType Leaf)) { throw "Virtual environment was not created: $py" }
& $py -m pip --version *> $null
if ($LASTEXITCODE -ne 0) {
  & $py -m ensurepip --upgrade --default-pip
  if ($LASTEXITCODE -ne 0) { throw 'pip bootstrap failed.' }
}
if (-not (Get-ChildItem -LiteralPath 'offline\python' -Filter '*.whl' -File -ErrorAction SilentlyContinue | Select-Object -First 1)) {
  throw 'Offline wheels are missing from offline\python.'
}
if (-not $venvReady) {
  & $py -m pip install --no-index --find-links (Join-Path $Root 'offline\python') -r (Join-Path $Root 'requirements-migration.txt')
  if ($LASTEXITCODE -ne 0) { throw 'Offline dependency installation failed.' }
}
& $py -c 'import django, daphne, channels, redis, pywt, yaml; print("Python dependencies OK")'
if ($LASTEXITCODE -ne 0) { throw 'Python dependency verification failed.' }
if (-not (Test-Path -LiteralPath 'db.sqlite3')) { & $py manage.py migrate --noinput }
if (-not (Test-Path -LiteralPath 'media')) { New-Item -ItemType Directory media | Out-Null }
Write-Host 'Setup complete. Run start_phm_platform.bat.' -ForegroundColor Green
