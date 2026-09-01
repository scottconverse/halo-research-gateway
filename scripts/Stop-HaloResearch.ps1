$ErrorActionPreference = 'Stop'
$runtime = Join-Path $env:LOCALAPPDATA 'HaloResearchGateway'
$pidFile = Join-Path $runtime 'run\gateway.json'
if (-not (Test-Path -LiteralPath $pidFile)) { Write-Host 'Halo Research Gateway is not recorded as running.'; exit 0 }
$identity = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
$live = Get-CimInstance Win32_Process -Filter "ProcessId=$($identity.pid)" -ErrorAction SilentlyContinue
if (-not $live) { Remove-Item -LiteralPath $pidFile -Force; Write-Host 'Removed stale Halo PID record.'; exit 0 }
if ($live.ExecutablePath -ne $identity.executable -or $live.CommandLine -notlike '*halo_research_gateway*') {
    throw "PID $($identity.pid) no longer matches the recorded Halo process; refusing to stop it."
}
Stop-Process -Id $identity.pid
Wait-Process -Id $identity.pid -Timeout 15 -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $pidFile -Force
Write-Host 'Halo Research Gateway stopped.'
