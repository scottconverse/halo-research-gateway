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
        # Legacy diagnostic foreground mode is not PID-managed. Never retain the
        # lifecycle mutex for its lifetime and prevent other stop/start commands.
        $mutex.ReleaseMutex()
        $mutex.Dispose()
        $mutex = $null
        Set-Location -LiteralPath $context.Repository
        & $context.Python -m halo_research_gateway
        exit $LASTEXITCODE
    }
    $process = Start-Process -FilePath $context.Python -ArgumentList '-m','halo_research_gateway' -WorkingDirectory $context.Repository -WindowStyle Hidden -PassThru
    $createdHere = $true
    $null = $process.Handle
    Write-HaloPidRecord $context $process
    $recordWritten = $true
    for ($i=0; $i -lt 30; $i++) {
        if (Test-HaloReady $process $server) {
            Write-Host "Halo Research Gateway ready (PID $($process.Id))."
            exit 0
        }
        Start-Sleep -Milliseconds 500
    }
    throw 'Gateway did not become ready within its startup window.'
} catch {
    if ($createdHere -and $process) {
        Stop-HaloOwnedProcess $process
        if ($recordWritten) { Remove-Item -LiteralPath $context.PidFile -Force }
    }
    throw
} finally {
    if ($process) { $process.Dispose() }
    if ($mutex) {
        $mutex.ReleaseMutex()
        $mutex.Dispose()
    }
}
