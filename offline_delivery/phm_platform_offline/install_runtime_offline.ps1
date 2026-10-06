param([switch]$Silent)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonInstaller = Join-Path $Root 'runtime-installers\python-3.10.11-amd64.exe'
$nodeInstaller = Join-Path $Root 'runtime-installers\node-v22.18.0-x64.msi'
$runtimeDir = Join-Path $Root 'runtime\python310'
if (-not (Test-Path $pythonInstaller) -or -not (Test-Path $nodeInstaller)) { throw 'Runtime installers are missing from runtime-installers.' }
$python = Get-Command python -ErrorAction SilentlyContinue
$pythonVersion = $null
if ($python -and $python.Source) {
  try {
    $pythonVersion = & $python.Source -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))' 2>$null | Select-Object -Last 1
    if ($LASTEXITCODE -ne 0) { $pythonVersion = $null }
  } catch { $pythonVersion = $null }
}
if (([string]$pythonVersion).Trim() -ne '3.10') {
  New-Item -ItemType Directory -Force -Path $runtimeDir | Out-Null
  # The project invokes python.exe directly; installing the optional Python
  # Launcher can fail with MSI 1603 when another launcher exists.
  $args = @('/quiet', 'InstallAllUsers=0', "TargetDir=`"$runtimeDir`"", 'PrependPath=0', 'Include_launcher=0', 'Include_test=0')
  $install = Start-Process $pythonInstaller -ArgumentList $args -Wait -PassThru
  if ($install.ExitCode -ne 0) { throw "Python installer failed with exit code $($install.ExitCode)." }
}
if (([string]$pythonVersion).Trim() -ne '3.10') {
  $knownPython = @(
    (Join-Path $runtimeDir 'python.exe'),
    (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python310\python.exe'),
    (Join-Path $env:ProgramFiles 'Python310\python.exe'),
    (Join-Path ${env:ProgramFiles(x86)} 'Python310\python.exe')
  ) | Where-Object { $_ -and (Test-Path -LiteralPath $_ -PathType Leaf) }
  foreach ($candidate in $knownPython) {
    try {
      $check = & $candidate -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))' 2>$null | Select-Object -Last 1
      if (([string]$check).Trim() -eq '3.10') { $pythonVersion = $check; break }
    } catch { }
  }
}
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
  $args = if ($Silent) { '/i', "`"$nodeInstaller`"", '/qn', '/norestart' } else { '/i', "`"$nodeInstaller`"", '/norestart' }
  $install = Start-Process msiexec.exe -ArgumentList $args -Wait -PassThru
  if ($install.ExitCode -notin @(0, 3010)) { throw "Node.js installer failed with exit code $($install.ExitCode)." }
}
Write-Host 'Local Python 3.10 and Node.js runtime installation finished. Run setup_migration.ps1.' -ForegroundColor Green
