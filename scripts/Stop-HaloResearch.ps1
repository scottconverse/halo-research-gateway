$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'HaloLifecycle.ps1')
$context = Get-HaloLifecycleContext
$mutex = Enter-HaloLifecycleLock $context
$process = $null
try {
    if (-not (Test-Path -LiteralPath $context.PidFile)) {
        Write-Host 'Halo Research Gateway is not recorded as running.'
        exit 0
    }
    $identity = Get-Content -LiteralPath $context.PidFile -Raw | ConvertFrom-Json
    $process = Get-HaloOwnedProcess $context $identity
    if ($process) { Stop-HaloOwnedProcess $process }
    Remove-Item -LiteralPath $context.PidFile -Force
    if ($process) { Write-Host 'Halo Research Gateway stopped.' }
    else { Write-Host 'Removed stale Halo PID record.' }
} finally {
    if ($process) { $process.Dispose() }
    $mutex.ReleaseMutex()
    $mutex.Dispose()
}
