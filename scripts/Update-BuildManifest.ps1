$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$paths = git ls-files --cached --others --exclude-standard |
    Where-Object { $_ -ne 'BUILD-MANIFEST.json' } |
    Sort-Object -Unique
$files = foreach ($relative in $paths) {
    $full = Join-Path $repo $relative
    if (Test-Path -LiteralPath $full -PathType Leaf) {
        [ordered]@{
            path = $relative.Replace('\','/')
            sha256 = (Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash.ToLowerInvariant()
            bytes = (Get-Item -LiteralPath $full).Length
        }
    }
}
$manifest = [ordered]@{
    schema = 1
    generated_at = (Get-Date).ToUniversalTime().ToString('o')
    project = 'halo-research-gateway'
    version = '0.2.0'
    specification = 'docs/RESEARCH-ONLY-SCOPE.md'
    result_schema = '1.5'
    python = '3.12'
    files = @($files)
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $repo 'BUILD-MANIFEST.json') -Encoding utf8
Write-Host "Wrote BUILD-MANIFEST.json with $($files.Count) files."
