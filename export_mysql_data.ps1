param(
  [string]$Host = '127.0.0.1',
  [string]$Port = '3306',
  [string]$Database = 'cmg_db',
  [string]$User = 'Kaimol',
  [string]$Password = '123456',
  [string]$Output = 'mysql_export.json'
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$Py = if (Test-Path '.venv\Scripts\python.exe') { (Resolve-Path '.venv\Scripts\python.exe').Path } else { 'python' }
$env:USE_SQLITE = 'false'; $env:MYSQL_HOST = $Host; $env:MYSQL_PORT = $Port
$env:MYSQL_DATABASE = $Database; $env:MYSQL_USER = $User; $env:MYSQL_PASSWORD = $Password
& $Py manage.py dumpdata --natural-foreign --natural-primary --exclude contenttypes --exclude admin.logentry --exclude sessions.session --indent 2 --output $Output
if ($LASTEXITCODE -ne 0) { throw 'MySQL export failed.' }
Write-Host "Export complete: $((Resolve-Path $Output).Path)" -ForegroundColor Green
