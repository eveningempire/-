param([switch]$SkipFrontend, [switch]$Offline)
$ErrorActionPreference = 'Stop'
$Root = $PSScriptRoot
Set-Location -LiteralPath $Root
$env:USE_SQLITE = 'true'
$env:PYTHONNOUSERSITE = '1'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
Remove-Item Env:PYTHONHOME -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue

function Test-CompatiblePython([string]$Candidate) {
    if (-not $Candidate -or -not (Test-Path -LiteralPath $Candidate -PathType Leaf)) { return $false }
    try {
        & $Candidate -c 'import sys,struct; sys.exit(0 if (3,10) <= sys.version_info[:2] < (3,13) and struct.calcsize(chr(80))==8 else 1)' *> $null
        return ($LASTEXITCODE -eq 0)
    } catch { return $false }
}

function Find-CompatiblePython {
    $candidates = @($env:PHM_PYTHON, (Join-Path $Root 'runtime\python310\python.exe'))
    $launcher = Get-Command py -ErrorAction SilentlyContinue
    if ($launcher) {
        foreach ($version in @('-3.10', '-3.11', '-3.12')) {
            try {
                $candidate = & $launcher.Source $version -c 'import sys; print(sys.executable)' 2>$null | Select-Object -Last 1
                if ($LASTEXITCODE -eq 0) { $candidates += [string]$candidate }
            } catch { }
        }
    }
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) { $candidates += $command.Source }
    foreach ($version in @('310', '311', '312')) {
        if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA "Programs\Python\Python$version\python.exe") }
        if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles "Python$version\python.exe") }
    }
    foreach ($candidate in $candidates) {
        if (Test-CompatiblePython $candidate) { return $candidate }
    }
    return $null
}

try {
    Write-Host 'PHM - GitHub / offline environment setup' -ForegroundColor Cyan
    $Py = Join-Path $Root '.venv\Scripts\python.exe'
    if (-not (Test-CompatiblePython $Py)) {
        $basePython = Find-CompatiblePython
        if (-not $basePython) {
            throw 'Install 64-bit Python 3.10, 3.11 or 3.12, or set PHM_PYTHON to its python.exe. Download: https://www.python.org/downloads/windows/'
        }
        $venv = Join-Path $Root '.venv'
        if (Test-Path -LiteralPath $venv) {
            $resolved = (Resolve-Path -LiteralPath $venv).Path
            $expected = [IO.Path]::GetFullPath((Join-Path $Root '.venv'))
            if ($resolved -ne $expected) { throw 'Unexpected virtual environment path; setup stopped.' }
            $backup = Join-Path $Root ('.venv-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff'))
            Move-Item -LiteralPath $resolved -Destination $backup
            Write-Host "Preserved incompatible environment: $backup" -ForegroundColor Yellow
        }
        & $basePython -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw 'Failed to create .venv.' }
    }
    $ready = $false
    try {
        & $Py (Join-Path $Root 'verify_phm_runtime.py') *> $null
        $ready = ($LASTEXITCODE -eq 0)
    } catch { }
    if (-not $ready) {
        & $Py -m ensurepip --upgrade
        if ($LASTEXITCODE -ne 0) { throw 'Failed to initialize pip.' }
        $wheels = Join-Path $Root 'offline\python'
        $hasWheels = @(Get-ChildItem -LiteralPath $wheels -Filter '*.whl' -File -ErrorAction SilentlyContinue).Count -gt 0
        if ($hasWheels -or $Offline) {
            if (-not $hasWheels) { throw 'Offline wheels are missing from offline\python.' }
            & $Py -m pip install --no-index --find-links $wheels -r (Join-Path $Root 'requirements-migration.txt')
            if ($LASTEXITCODE -ne 0) { throw 'Offline dependency installation failed.' }
        } else {
            Remove-Item Env:PIP_NO_INDEX -ErrorAction SilentlyContinue
            Write-Host 'Installing GitHub runtime dependencies from the network...' -ForegroundColor Yellow
            # Python 3.10.11 ships an older pip. Bootstrap a pinned wheel using
            # Windows TLS trust, then let modern pip use the OS certificate store.
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            $bootstrap = Join-Path $Root 'output\bootstrap'
            New-Item -ItemType Directory -Path $bootstrap -Force | Out-Null
            $pipWheel = Join-Path $bootstrap 'pip-26.0.1-py3-none-any.whl'
            if (-not (Test-Path -LiteralPath $pipWheel)) {
                Invoke-WebRequest -UseBasicParsing -Uri 'https://files.pythonhosted.org/packages/de/f0/c81e05b613866b76d2d1066490adf1a3dbc4ee9d9c839961c3fc8a6997af/pip-26.0.1-py3-none-any.whl' -OutFile $pipWheel
            }
            if ((Get-FileHash -LiteralPath $pipWheel -Algorithm SHA256).Hash -ne 'BDB1B08F4274833D62C1AA29E20907365A2CEB950410DF15FC9521BAD440122B') {
                throw 'pip bootstrap checksum mismatch. Remove output\bootstrap and retry.'
            }
            & $Py -m pip install --no-index $pipWheel
            if ($LASTEXITCODE -ne 0) { throw 'Failed to upgrade pip.' }
            & $Py -m pip install -r (Join-Path $Root 'requirements.txt')
            if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check network access and rerun.' }
            & $Py -m pip install 'torch==2.5.1' --index-url https://download.pytorch.org/whl/cpu
            if ($LASTEXITCODE -ne 0) { throw 'CPU PyTorch installation failed. Check download.pytorch.org access and rerun.' }
        }
    }
    & $Py (Join-Path $Root 'verify_phm_runtime.py')
    if ($LASTEXITCODE -ne 0) { throw 'Python runtime verification failed.' }
    & $Py manage.py migrate --noinput
    if ($LASTEXITCODE -ne 0) { throw 'Database migration failed.' }
    Write-Host 'Setup complete. Run create_superuser.bat, then start_phm_platform.bat.' -ForegroundColor Green
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
