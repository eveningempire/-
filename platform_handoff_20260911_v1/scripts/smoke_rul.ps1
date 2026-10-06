$ErrorActionPreference = 'Stop'
$handoffRoot = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $handoffRoot 'code'
$cases = @(
    @{ Bundle = 'p1_bilstm_candidate_v1_s3407'; Request = 'p1_sample_request.npz' },
    @{ Bundle = 'platform_lox_shadow_v1_s3407_r2'; Request = 'lox_sample_request.npz' }
)
foreach ($case in $cases) {
    $bundle = Join-Path (Join-Path $handoffRoot 'rul_shadow_bundles') $case.Bundle
    $request = Join-Path (Join-Path $handoffRoot 'data_examples\rul') $case.Request
    $output = Join-Path $env:TEMP ("20jd_" + $case.Bundle + '_smoke.jsonl')
    & python -m rul_prediction.deployment.cli healthcheck --bundle $bundle
    if ($LASTEXITCODE -ne 0) { throw "RUL healthcheck failed: $($case.Bundle)" }
    & python -m rul_prediction.deployment.cli predict --bundle $bundle --input $request --output $output
    if ($LASTEXITCODE -ne 0) { throw "RUL predict smoke failed: $($case.Bundle)" }
}
Write-Output 'RUL_BUNDLE_SMOKE_ALL_PASS'
