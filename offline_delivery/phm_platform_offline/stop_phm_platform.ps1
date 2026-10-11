$ErrorActionPreference = 'Stop'
$marker = Join-Path $PSScriptRoot 'logs\server-process.json'
if (-not (Test-Path -LiteralPath $marker)) {
    Write-Host 'PHM has no recorded server process in this folder.'
    exit 0
}
$record = Get-Content -LiteralPath $marker -Raw -Encoding UTF8 | ConvertFrom-Json
$process = Get-CimInstance Win32_Process -Filter "ProcessId=$($record.process_id)" -ErrorAction SilentlyContinue
if ($process) {
    if (($process.ExecutablePath -ne [string]$record.executable) -or ($process.CommandLine -notmatch 'manage\.py\s+runserver')) {
        throw 'The recorded PID belongs to a different process. No process was stopped.'
    }
    Stop-Process -Id $record.process_id -Force
}
Remove-Item -LiteralPath $marker
Write-Host 'PHM stopped.'
