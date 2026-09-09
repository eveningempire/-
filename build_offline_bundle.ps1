param([string]$Output = 'offline\python')
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
New-Item -ItemType Directory -Force -Path $Output | Out-Null
if (-not (Test-Path '.venv\Scripts\python.exe')) { throw 'Create a Python 3.10 virtual environment in .venv before building.' }
$Py = Join-Path $Root '.venv\Scripts\python.exe'
& $Py -m pip download --only-binary=:all: --dest $Output -r requirements-migration.txt
if ($LASTEXITCODE -ne 0) { throw 'One or more dependencies have no compatible wheel; use Python 3.10 on the build machine.' }
Write-Host "Python wheels downloaded to $Output" -ForegroundColor Green
Write-Host 'Frontend node_modules is already bundled; keep frontend\package-lock.json for reproducible offline installs.'
