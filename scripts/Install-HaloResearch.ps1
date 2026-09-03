param([switch]$RegisterTask, [switch]$RegisterHosts, [switch]$Start)
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$runtime = Join-Path $env:LOCALAPPDATA 'HaloResearchGateway'
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
Set-Location -LiteralPath $repo
uv sync --locked --extra crawl --extra documents --group dev
if ($LASTEXITCODE) { throw 'Locked environment installation failed' }
uv run --locked python -m halo_research_gateway.ocr_data
if ($LASTEXITCODE) { throw 'Verified local OCR-data installation failed' }
$config = Join-Path $runtime 'config.toml'
if (-not (Test-Path -LiteralPath $config)) { Copy-Item -LiteralPath (Join-Path $repo 'config\config.example.toml') -Destination $config }
git config --local core.hooksPath .githooks
if ($LASTEXITCODE) { throw 'Repository hook setup failed; host registrations were not changed.' }
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
    . (Join-Path $PSScriptRoot 'HaloLifecycle.ps1')
    $server = Get-HaloServerSettings (Get-HaloLifecycleContext)
    $lmConfig = Join-Path $env:USERPROFILE '.lmstudio\mcp.json'
    $originalHash = $null
    if (Test-Path -LiteralPath $lmConfig) {
        $originalHash = (Get-FileHash -LiteralPath $lmConfig -Algorithm SHA256).Hash
        try {
            $originalJson = Get-Content -LiteralPath $lmConfig -Raw -Encoding UTF8
            if (-not $originalJson.TrimStart().StartsWith('{')) { throw 'Expected JSON object' }
            $value = $originalJson | ConvertFrom-Json
        }
        catch { throw 'Cannot parse LM Studio configuration; original file was preserved. Inspect it locally without sharing credentials.' }
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $lmConfig) | Out-Null
        $value = [pscustomobject]@{}
    }
    if ($value -isnot [pscustomobject]) { throw 'LM Studio configuration must be a JSON object; original file was preserved.' }
    if (-not $value.PSObject.Properties['mcpServers']) {
        $value | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{})
    }
    if ($value.mcpServers -isnot [pscustomobject]) { throw 'LM Studio mcpServers must be a JSON object; original file was preserved.' }
    $value.mcpServers | Add-Member -NotePropertyName 'halo-research' -NotePropertyValue @{
        url = "http://127.0.0.1:$($server.port)$($server.mcp_path)"
    } -Force
    # Serialize before touching the original; reject depth-loss warnings.
    $serialized = $value | ConvertTo-Json -Depth 100 -WarningAction Stop
    $temporary = "$lmConfig.halo-new-$([guid]::NewGuid().ToString('N'))"
    try {
        $serialized | Set-Content -LiteralPath $temporary -Encoding utf8
        if ($originalHash) {
            if ((Get-FileHash -LiteralPath $lmConfig -Algorithm SHA256).Hash -ne $originalHash) {
                throw 'LM Studio configuration changed during installation; refusing to overwrite it.'
            }
            $backup = "$lmConfig.halo-backup-$([guid]::NewGuid().ToString('N'))"
            Copy-Item -LiteralPath $lmConfig -Destination $backup
        } elseif (Test-Path -LiteralPath $lmConfig) {
            throw 'LM Studio configuration appeared during installation; refusing to overwrite it.'
        }
        Move-Item -LiteralPath $temporary -Destination $lmConfig -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}
if ($RegisterTask) {
    $action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$repo\scripts\Start-HaloResearch.ps1`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
    $settings = New-ScheduledTaskSettingsSet -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -MultipleInstances IgnoreNew
    Register-ScheduledTask -TaskName 'Halo Research Gateway' -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
}
if ($Start) { & (Join-Path $PSScriptRoot 'Start-HaloResearch.ps1') }
Write-Host 'Halo Research Gateway installed.'
