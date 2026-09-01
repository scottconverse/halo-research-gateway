param([switch]$Foreground)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $env:LOCALAPPDATA 'HaloResearchGateway'
$run = Join-Path $runtime 'run'
$pidFile = Join-Path $run 'gateway.json'
$python = Join-Path $repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python)) { throw "Locked environment missing: $python" }
New-Item -ItemType Directory -Force -Path $run | Out-Null

if (Test-Path -LiteralPath $pidFile) {
    $identity = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
    $live = Get-CimInstance Win32_Process -Filter "ProcessId=$($identity.pid)" -ErrorAction SilentlyContinue
    if ($live -and $live.ExecutablePath -eq $python -and $live.CommandLine -like '*halo_research_gateway*') {
        Write-Host "Halo Research Gateway already running (PID $($identity.pid))."
        exit 0
    }
    Remove-Item -LiteralPath $pidFile -Force
}

$portOwner = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
if ($portOwner) { throw "Port 8765 is already owned by PID $($portOwner.OwningProcess)." }

if ($Foreground) {
    Set-Location -LiteralPath $repo
    & $python -m halo_research_gateway
    exit $LASTEXITCODE
}

$process = Start-Process -FilePath $python -ArgumentList '-m','halo_research_gateway' -WorkingDirectory $repo -WindowStyle Hidden -PassThru
$identity = [ordered]@{ pid=$process.Id; executable=$python; started_at=(Get-Date).ToUniversalTime().ToString('o'); repository=$repo }
$identity | ConvertTo-Json | Set-Content -LiteralPath $pidFile -Encoding utf8
for ($i=0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 2
        if ($health.status -in @('ok','degraded','starting')) { Write-Host "Halo Research Gateway $($health.status) (PID $($process.Id))."; exit 0 }
    } catch {}
    Start-Sleep -Milliseconds 500
}
throw 'Gateway did not become healthy within 15 seconds.'
