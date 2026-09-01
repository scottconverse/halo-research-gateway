param([ValidateSet('Commit','CI','Full')][string]$Scope = 'Commit')
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo

function Invoke-GateStep([string]$Name, [scriptblock]$Action) {
    Write-Host "[GATE] $Name"
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
}

Invoke-GateStep 'lock check' { uv lock --check }
Invoke-GateStep 'format' { uv run --locked ruff format --check src tests }
Invoke-GateStep 'lint' { uv run --locked ruff check src tests }
Invoke-GateStep 'unit and fixture tests' { uv run --locked python -m pytest -q tests/unit }
Invoke-GateStep 'skill package' {
    uv run --locked python scripts\validate_skill.py
}

$scan = @('README.md','src','scripts','config','skills')
if (Test-Path -LiteralPath 'adapters') { $scan += 'adapters' }
$forbidden = rg -n 'DSH-Strix-Halo-Spec-v(2\.|3\.[0-4])|stack\\worker\.patch\.yml' @scan 2>$null
if ($LASTEXITCODE -eq 0) {
    $bad = $forbidden | Where-Object { $_ -notmatch 'historical|supersed|deleted|must not|prohibition' }
    if ($bad) { $bad | Write-Error; throw 'staleness guard failed' }
}

Write-Host "[GATE] PASS ($Scope)"
