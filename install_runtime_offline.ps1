param([switch]$Silent)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonInstaller = Join-Path $Root 'runtime-installers\python-3.10.11-amd64.exe'
$nodeInstaller = Join-Path $Root 'runtime-installers\node-v22.18.0-x64.msi'
if (-not (Test-Path $pythonInstaller) -or -not (Test-Path $nodeInstaller)) { throw 'Runtime installers are missing from runtime-installers.' }
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python -or ((python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')").Trim() -ne '3.10')) {
  $args = if ($Silent) { '/quiet InstallAllUsers=0 PrependPath=1 Include_test=0' } else { 'InstallAllUsers=0 PrependPath=1 Include_test=0' }
  Start-Process $pythonInstaller -ArgumentList $args -Wait
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  $args = if ($Silent) { '/i', "`"$nodeInstaller`"", '/qn', '/norestart' } else { '/i', "`"$nodeInstaller`"", '/norestart' }
  Start-Process msiexec.exe -ArgumentList $args -Wait
}
Write-Host 'Python 3.10 and Node.js runtime installation finished. Open a new terminal before setup.' -ForegroundColor Green
