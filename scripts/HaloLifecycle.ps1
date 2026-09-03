# Shared Windows lifecycle ownership. Dot-source only; no service is started here.
function Get-HaloLifecycleContext {
    $repository = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
    $runtimeDirectory = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'HaloResearchGateway'))
    return @{
        Repository = $repository
        Python = Join-Path $repository '.venv\Scripts\python.exe'
        Run = Join-Path $runtimeDirectory 'run'
        PidFile = Join-Path $runtimeDirectory 'run\gateway.json'
    }
}

function Enter-HaloLifecycleLock($Context) {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Context.Run.ToUpperInvariant())
        $key = [BitConverter]::ToString($hasher.ComputeHash($bytes)).Replace('-', '')
    } finally { $hasher.Dispose() }
    $sid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
    $mutex = New-Object Threading.Mutex($false, "Global\HaloResearchGateway-$sid-$key")
    try {
        try { $acquired = $mutex.WaitOne(30000) }
        catch [Threading.AbandonedMutexException] { $acquired = $true }
        if (-not $acquired) { throw 'Another Gateway start/stop operation is still running; retry shortly.' }
        return $mutex
    } catch { $mutex.Dispose(); throw }
}

function Get-HaloOwnedProcess($Context, $Identity) {
    $number = 0
    if (-not [int]::TryParse([string]$Identity.pid, [ref]$number) -or $number -le 0 -or
        $Identity.repository -ne $Context.Repository -or $Identity.executable -ne $Context.Python) {
        throw 'Gateway PID record does not match this repository and executable; leaving it untouched.'
    }
    # A CIM access error is not proof of a stale PID.
    $live = Get-CimInstance Win32_Process -Filter "ProcessId=$number" -ErrorAction Stop
    if (-not $live) { return $null }
    $held = Get-Process -Id $number -ErrorAction Stop
    try {
        # Hold the kernel process handle before validating it, avoiding a later PID lookup.
        $null = $held.Handle
        $recorded = $Identity.started_at
        if ($recorded -is [datetime]) { $recorded = $recorded.ToUniversalTime() }
        else { $recorded = [DateTimeOffset]::Parse([string]$recorded).UtcDateTime }
        $difference = ($recorded - $held.StartTime.ToUniversalTime()).TotalSeconds
        # Old launchers recorded wall-clock time just after launch, not creation time.
        # Only that legacy format gets a one-sided two-second compatibility window.
        $timeMatches = if ($Identity.schema -eq 2) { $difference -eq 0 }
            elseif (-not $Identity.schema) { $difference -ge 0 -and $difference -le 2 }
            else { $false }
        if ($held.HasExited -or -not $timeMatches -or $live.ExecutablePath -ne $Context.Python -or
            $live.CommandLine -notmatch '(?:^|\s)-m\s+halo_research_gateway\s*$') {
            throw "PID $number does not match the recorded Gateway process; leaving it untouched."
        }
        return $held
    } catch { $held.Dispose(); throw }
}

function Stop-HaloOwnedProcess($Process) {
    if (-not $Process.HasExited) {
        Stop-Process -InputObject $Process -ErrorAction Stop
        Wait-Process -InputObject $Process -Timeout 15 -ErrorAction Stop
    }
    if (-not $Process.HasExited) { throw 'Gateway has not exited; preserving its PID record.' }
}

function Get-HaloListeners([int]$Port) {
    try { return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Where-Object { $null -ne $_ }) }
    catch {
        if ($_.CategoryInfo.Category -eq 'ObjectNotFound') { return @() }
        throw
    }
}

function Get-HaloServerSettings($Context) {
    # Use the service's own loader; emit no credentials or unrelated settings.
    $query = @'
import json, os
from pathlib import Path
from halo_research_gateway.config import ROOT, GatewayConfig
p = Path(os.environ.get('HALO_RESEARCH_CONFIG', ROOT / 'config.toml'))
s = GatewayConfig.load(p if p.exists() else None).server
print(json.dumps({'port': s.port, 'health_path': s.health_path, 'mcp_path': s.mcp_path}))
'@
    $result = & $Context.Python -c $query
    if ($LASTEXITCODE -ne 0) { throw 'Cannot read Gateway configuration; no service was changed.' }
    return ($result | ConvertFrom-Json)
}

function Test-HaloReady($Process, $Server) {
    $Port = [int]$Server.port
    if ($Process.HasExited) { throw 'Gateway process exited before readiness.' }
    $listeners = @(Get-HaloListeners $Port)
    if (-not $listeners.Count) { return $false }
    foreach ($listener in $listeners) {
        $owner = [int]$listener.OwningProcess
        for ($depth = 0; $owner -ne $Process.Id -and $depth -lt 8; $depth++) {
            $child = Get-CimInstance Win32_Process -Filter "ProcessId=$owner" -ErrorAction Stop
            if (-not $child -or $child.CreationDate.ToUniversalTime() -lt $Process.StartTime.ToUniversalTime()) { break }
            $owner = [int]$child.ParentProcessId
            if ($owner -le 0) { break }
        }
        if ($owner -ne $Process.Id) { throw "Port $Port belongs to an unrelated process; leaving it untouched." }
    }
    try { $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port$($Server.health_path)" -TimeoutSec 2 -ErrorAction Stop }
    catch { return $false }
    return (-not $Process.HasExited -and $health.status -in @('ok','degraded'))
}

function Write-HaloPidRecord($Context, $Process) {
    $identity = [ordered]@{
        schema = 2; pid = $Process.Id; executable = $Context.Python
        started_at = $Process.StartTime.ToUniversalTime().ToString('o')
        repository = $Context.Repository
    }
    $temporary = Join-Path $Context.Run ("gateway-" + [guid]::NewGuid().ToString('N') + '.tmp')
    try {
        $identity | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding utf8
        Move-Item -LiteralPath $temporary -Destination $Context.PidFile -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}
