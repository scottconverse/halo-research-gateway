param([switch]$RemoveRuntimeState)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Stop-HaloResearch.ps1')
Unregister-ScheduledTask -TaskName 'Halo Research Gateway' -Confirm:$false -ErrorAction SilentlyContinue
if ($RemoveRuntimeState) {
    $runtime = [IO.Path]::GetFullPath((Join-Path $env:LOCALAPPDATA 'HaloResearchGateway'))
    $expected = [IO.Path]::GetFullPath("$env:LOCALAPPDATA\HaloResearchGateway")
    if ($runtime -ne $expected) { throw 'Runtime path validation failed' }
    Remove-Item -LiteralPath $runtime -Recurse -Force
    Write-Host 'Removed encrypted runtime state at explicit request.'
} else { Write-Host 'Runtime vault, profiles, jobs, receipts, cache, and evidence were preserved.' }
