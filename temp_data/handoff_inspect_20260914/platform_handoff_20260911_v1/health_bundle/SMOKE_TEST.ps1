# Non-interactive bundle smoke: normal input, bad input, model replacement.
$ErrorActionPreference = 'Stop'
$python = if ($env:PYTHON) { $env:PYTHON } else { 'python' }
Set-Location -Path $PSScriptRoot
& $python -m platform_adapter.cli --bundle . --smoke
if ($LASTEXITCODE -ne 0) { exit 1 }
& $python -m platform_adapter.cli --bundle . --input examples/input_smoke.jsonl --output out_smoke.jsonl
if ($LASTEXITCODE -ne 0) { exit 1 }
$out = Get-Content out_smoke.jsonl | ForEach-Object { $_ | ConvertFrom-Json }
$has_hi = @($out | Where-Object { $_.component_hi -ne $null }).Count -ge 4
$has_bad_json = @($out | Where-Object { $_.error -eq 'E_BAD_JSON' }).Count -eq 1
$has_forbidden = @($out | Where-Object { $_.error -eq 'E_SCHEMA_FORBIDDEN_FIELD' }).Count -eq 1
$has_unknown = @($out | Where-Object { $_.error -eq 'E_UNKNOWN_COMPONENT' }).Count -eq 1
$has_summary = @($out | Where-Object { $_.summary_type }).Count -eq 1
if (-not ($has_hi -and $has_bad_json -and $has_forbidden -and $has_unknown -and $has_summary)) { exit 2 }
& $python -m platform_adapter.cli --bundle . --replace-drill
if ($LASTEXITCODE -ne 0) { exit 3 }
Write-Host 'BUNDLE_SMOKE_ALL_PASS'
