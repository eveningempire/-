function Find-Python310 {
  $candidates = @()
  $bundledRuntime = Join-Path $Root 'runtime\python310\python.exe'
  if (Test-Path -LiteralPath $bundledRuntime -PathType Leaf) { $candidates += $bundledRuntime }
  $launcher = Get-Command py -ErrorAction SilentlyContinue
  if ($launcher) {
    try {
      $launcherPath = & $launcher.Source -3.10 -c 'import sys; print(sys.executable)' 2>$null | Select-Object -Last 1
      if ($LASTEXITCODE -eq 0 -and $launcherPath) { $candidates += [string]$launcherPath }
    } catch { }
  }
  $python = Get-Command python -ErrorAction SilentlyContinue
  if ($python -and $python.Source) { $candidates += $python.Source }
  if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python310\python.exe') }
  if ($env:LOCALAPPDATA) { $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python310-64\python.exe') }
  if ($env:ProgramFiles) { $candidates += (Join-Path $env:ProgramFiles 'Python310\python.exe') }
  if (${env:ProgramFiles(x86)}) { $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Python310\python.exe') }
  foreach ($key in @('HKCU:\Software\Python\PythonCore\3.10\InstallPath', 'HKLM:\Software\Python\PythonCore\3.10\InstallPath', 'HKLM:\Software\WOW6432Node\Python\PythonCore\3.10\InstallPath')) {
    try {
      $installPath = (Get-ItemProperty -LiteralPath $key -ErrorAction Stop).'(default)'
      if ($installPath) { $candidates += (Join-Path ([string]$installPath) 'python.exe') }
    } catch { }
  }
  if ($env:LOCALAPPDATA) {
    try { $candidates += Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'Programs\Python') -Filter 'python.exe' -File -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'Python310' } | Select-Object -ExpandProperty FullName } catch { }
  }
  Write-Host ("CANDS=" + ($candidates -join "|")); foreach ($candidate in $candidates) {
    if (-not $candidate -or -not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    try {
      Write-Host ("TRY=" + $candidate); $version = & $candidate -c 'import sys; print("{}.{}".format(*sys.version_info[:2]))' 2>$null | Select-Object -Last 1
      if ($LASTEXITCODE -eq 0 -and ([string]$version).Trim() -eq '3.10') { return $candidate }
    } catch { }
  }
  return $null
}
$Root=(Get-Location).Path; $x=Find-Python310; Write-Host "RESULT <$x>"
