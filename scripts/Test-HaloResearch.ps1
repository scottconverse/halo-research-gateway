param([switch]$Live, [switch]$Browser)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
& (Join-Path $PSScriptRoot 'Invoke-QualityGate.ps1') -Scope Full
$health = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' -TimeoutSec 5
$stats = Invoke-RestMethod -Uri 'http://127.0.0.1:8765/stats' -TimeoutSec 5
if ($health.status -notin @('ok','degraded')) { throw "Unexpected health: $($health.status)" }
if ($Browser) { uv run --locked python tests\acceptance\crawl_canary.py; if ($LASTEXITCODE) { throw 'Crawl canary failed' } }
if ($Live) {
    $response = Invoke-WebRequest -Uri 'https://example.com' -UseBasicParsing -TimeoutSec 15
    if ($response.StatusCode -ne 200) { throw 'Live public HTTP canary failed' }
}
Write-Host "Halo health=$($health.status); cache=$($health.cache_entries); queues=$($stats.queues.PSObject.Properties.Count)"
