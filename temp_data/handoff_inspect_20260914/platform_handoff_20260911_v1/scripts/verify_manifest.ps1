$ErrorActionPreference = 'Stop'
$handoffRoot = Split-Path -Parent $PSScriptRoot
$manifest = Join-Path $handoffRoot 'manifests\SHA256SUMS.txt'
$failures = @()
foreach ($line in Get-Content -LiteralPath $manifest -Encoding UTF8) {
    if ([string]::IsNullOrWhiteSpace($line) -or $line.StartsWith('#')) { continue }
    $parts = $line -split '  ', 2
    if ($parts.Count -ne 2) { $failures += "Malformed: $line"; continue }
    $path = Join-Path $handoffRoot ($parts[1].Replace('/', '\'))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $failures += "Missing: $($parts[1])"; continue }
    $actual = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actual -ne $parts[0].ToLowerInvariant()) { $failures += "Hash mismatch: $($parts[1])" }
}
if ($failures.Count -gt 0) { throw ($failures -join [Environment]::NewLine) }
Write-Output 'HANDOFF_MANIFEST_PASS'
