param([switch]$Foreground)
$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'HaloLifecycle.ps1')
$context = Get-HaloLifecycleContext
if (-not (Test-Path -LiteralPath $context.Python)) { throw "Locked environment missing: $($context.Python)" }
$server = Get-HaloServerSettings $context
New-Item -ItemType Directory -Force -Path $context.Run | Out-Null
$mutex = Enter-HaloLifecycleLock $context
$process = $null
$createdHere = $false
$recordWritten = $false
$ready = $false
try {
    if (Test-Path -LiteralPath $context.PidFile) {
        $identity = Get-Content -LiteralPath $context.PidFile -Raw | ConvertFrom-Json
        $process = Get-HaloOwnedProcess $context $identity
        if ($process) {
            if (-not (Test-HaloReady $process $server)) { throw 'Recorded Gateway is not ready; inspect it before restarting. No process was changed.' }
            Write-Host "Halo Research Gateway already running (PID $($process.Id))."
            exit 0
        }
        Remove-Item -LiteralPath $context.PidFile -Force
    }
    $portOwner = @(Get-HaloListeners $server.port)
    if ($portOwner.Count) { throw "Port $($server.port) is already owned by PID $($portOwner.OwningProcess)." }
    if ($Foreground) {
        $process = Start-Process -FilePath $context.Python -ArgumentList '-m','halo_research_gateway' -WorkingDirectory $context.Repository -NoNewWindow -PassThru
    } else {
        $process = Start-Process -FilePath $context.Python -ArgumentList '-m','halo_research_gateway' -WorkingDirectory $context.Repository -WindowStyle Hidden -PassThru
    }
    $createdHere = $true
    $null = $process.Handle
    Write-HaloPidRecord $context $process
    $recordWritten = $true
    for ($i=0; $i -lt 30; $i++) {
        if (Test-HaloReady $process $server) {
            $ready = $true
            Write-Host "Halo Research Gateway ready (PID $($process.Id))."
            break
        }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw 'Gateway did not become ready within its startup window.' }
    if ($Foreground) {
        # Stop and duplicate-start must be able to take the lifecycle lock while
        # this console waits. Retain the process handle, not just a reusable PID.
        $mutex.ReleaseMutex()
        $mutex.Dispose()
        $mutex = $null
        $process.WaitForExit()
        exit $process.ExitCode
    }
    exit 0
} finally {
    try {
        if ($createdHere -and $process -and ($Foreground -or -not $ready)) {
            if (-not $mutex) { $mutex = Enter-HaloLifecycleLock $context }
            Stop-HaloOwnedProcess $process
            if ($recordWritten) { Remove-HaloLaunchedRecord $context $process }
        }
    } finally {
        if ($process) { $process.Dispose() }
        if ($mutex) {
            $mutex.ReleaseMutex()
            $mutex.Dispose()
        }
    }
}
