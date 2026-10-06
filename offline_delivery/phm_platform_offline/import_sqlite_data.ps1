param([string]$Input = 'mysql_export.json')
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
if (-not (Test-Path $Input)) { throw "Fixture not found: $Input" }
$Py = Join-Path $Root '.venv\Scripts\python.exe'
if (-not (Test-Path $Py)) { throw 'Run setup_migration.ps1 first.' }
$env:USE_SQLITE = 'true'
& $Py manage.py loaddata $Input
if ($LASTEXITCODE -ne 0) { throw 'SQLite import failed.' }
Write-Host 'SQLite import complete.' -ForegroundColor Green
