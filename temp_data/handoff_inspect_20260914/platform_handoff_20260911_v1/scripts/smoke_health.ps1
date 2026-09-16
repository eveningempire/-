$ErrorActionPreference = 'Stop'
$bundleRoot = Join-Path (Split-Path -Parent $PSScriptRoot) 'health_bundle'
Push-Location -LiteralPath $bundleRoot
try {
    & python 'run_smoke.py'
    if ($LASTEXITCODE -ne 0) { throw "Health smoke failed with exit code $LASTEXITCODE" }
}
finally {
    Pop-Location
}
