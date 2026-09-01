param([switch]$RegisterTask, [switch]$RegisterHosts, [switch]$Start)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $env:LOCALAPPDATA 'HaloResearchGateway'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
Set-Location -LiteralPath $repo
uv sync --locked --extra crawl --extra documents --group dev
if ($LASTEXITCODE) { throw 'Locked environment installation failed' }
$config = Join-Path $runtime 'config.toml'
if (-not (Test-Path -LiteralPath $config)) { Copy-Item -LiteralPath (Join-Path $repo 'config\config.example.toml') -Destination $config }
git config --local core.hooksPath .githooks
& (Join-Path $PSScriptRoot 'Invoke-QualityGate.ps1') -Scope Full

$canonicalSkill = Join-Path $repo 'skills\halo-research'
foreach ($skillRoot in @(
    (Join-Path $env:USERPROFILE '.agents\skills'),
    (Join-Path $env:USERPROFILE '.claude\skills'),
    (Join-Path $env:USERPROFILE '.lmstudio\skills')
)) {
    $destination = Join-Path $skillRoot 'halo-research'
    New-Item -ItemType Directory -Force -Path $destination | Out-Null
    Copy-Item -Path (Join-Path $canonicalSkill '*') -Destination $destination -Recurse -Force
}

if ($RegisterHosts) {
    $lmConfig = Join-Path $env:USERPROFILE '.lmstudio\mcp.json'
    if (Test-Path -LiteralPath $lmConfig) {
        Copy-Item -LiteralPath $lmConfig -Destination "$lmConfig.halo-backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        $value = Get-Content -LiteralPath $lmConfig -Raw | ConvertFrom-Json -AsHashtable
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $lmConfig) | Out-Null
        $value = @{ mcpServers = @{} }
    }
    if (-not $value.ContainsKey('mcpServers')) { $value.mcpServers = @{} }
    $value.mcpServers['halo-research'] = @{ url = 'http://127.0.0.1:8765/mcp' }
    $value | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $lmConfig -Encoding utf8
}
if ($RegisterTask) {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\Start-HaloResearch.ps1`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName 'Halo Research Gateway' -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
}
if ($Start) { & (Join-Path $PSScriptRoot 'Start-HaloResearch.ps1') }
Write-Host 'Halo Research Gateway installed.'
