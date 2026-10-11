param([string]$ProjectRoot)
$ErrorActionPreference = 'Stop'
# Simulate a broken HTTP association while retaining the real server launch.
function Start-Process {
    [CmdletBinding()]
    param([string]$FilePath, [string[]]$ArgumentList, [string]$WorkingDirectory,
          [string]$WindowStyle, [switch]$PassThru,
          [string]$RedirectStandardOutput, [string]$RedirectStandardError)
    if ($FilePath -like 'http://*') {
        throw 'Simulated Windows HTTP association failure'
    }
    Microsoft.PowerShell.Management\Start-Process @PSBoundParameters
}
. (Join-Path $ProjectRoot 'start_phm_platform.ps1') -Port 18009
