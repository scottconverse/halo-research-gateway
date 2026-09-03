import json
import re
import tomllib
from pathlib import Path

from halo_research_gateway import __version__
from halo_research_gateway.providers.github import GitHubProvider
from halo_research_gateway.providers.http_fetch import USER_AGENT

REPO = Path(__file__).resolve().parents[2]
INTEGRATION = REPO / "integrations" / "dsh"


def test_release_version_is_0_3_0_on_every_current_surface():
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    website = json.loads((REPO / "website/package.json").read_text(encoding="utf-8"))
    manifest_script = (REPO / "scripts/Update-BuildManifest.ps1").read_text(encoding="utf-8")
    current_docs = "\n".join(
        (REPO / relative).read_text(encoding="utf-8")
        for relative in ("README.md", "docs/USER-MANUAL.md", "website/app/page.tsx")
    )

    assert project["project"]["version"] == "0.3.0"
    assert __version__ == "0.3.0"
    assert website["version"] == "0.3.0"
    assert re.search(r"version\s*=\s*'0\.3\.0'", manifest_script)
    assert "Version 0.3.0" in current_docs
    assert "v0.3.0" in current_docs


def test_outbound_http_identifies_the_current_gateway_version():
    assert f"halo-research-gateway/{__version__}" in USER_AGENT
    assert GitHubProvider._headers(None)["User-Agent"] == f"halo-research-gateway/{__version__}"


def test_dsh_adapter_is_complete_optional_client_code_without_machine_paths():
    expected = {
        "README.md",
        "halo-research-state/index.mjs",
        "halo-research-state/acceptance.mjs",
        "halo-research-state/verify-history.mjs",
        "halo-research-state/test/acceptance.test.mjs",
        "halo-research-state/test/research-state.test.mjs",
        "patches/compaction-request-retention.patch",
        "patches/invalid-summary-rejection.patch",
    }
    actual = {path.relative_to(INTEGRATION).as_posix() for path in INTEGRATION.rglob("*") if path.is_file()}
    assert expected <= actual

    source = (INTEGRATION / "halo-research-state/index.mjs").read_text(encoding="utf-8")
    readme = (INTEGRATION / "README.md").read_text(encoding="utf-8")
    assert "mcp__halo_research__" in source
    assert "C:\\Users\\" not in source + readme
    assert "optional DSH client integration" in readme


def test_source_distribution_includes_the_optional_integration_and_operator_docs():
    project = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    includes = set(project["tool"]["hatch"]["build"]["targets"]["sdist"]["include"])
    assert {
        "/src/halo_research_gateway",
        "/README.md",
        "/CONTRIBUTING.md",
        "/CHANGELOG.md",
        "/docs/USER-MANUAL.md",
        "/docs/RELEASE-NOTES-v0.3.0.md",
        "/integrations/dsh",
    } <= includes


def test_dsh_compaction_patches_preserve_the_two_required_source_repairs():
    retention = (INTEGRATION / "patches/compaction-request-retention.patch").read_text(encoding="utf-8")
    invalid = (INTEGRATION / "patches/invalid-summary-rejection.patch").read_text(encoding="utf-8")

    assert "request-retention.spec.ts" in retention
    assert "compaction-basic" in retention
    assert "tool-call" in invalid
    assert "compaction" in invalid
    assert "C:\\Users\\" not in retention + invalid


def test_quality_gate_runs_the_dsh_adapter_tests():
    gate = (REPO / "scripts/Invoke-QualityGate.ps1").read_text(encoding="utf-8")
    assert "halo-research-state/test/*.test.mjs" in gate
    assert "node --test" in gate


def test_windows_ci_builds_the_documented_landing_page():
    workflow = (REPO / ".github/workflows/quality-gate.yml").read_text(encoding="utf-8")
    assert "actions/setup-node@v4" in workflow
    assert "node-version: '22'" in workflow
    assert "npm ci" in workflow
    assert "npm run lint" in workflow
    assert "npm run build" in workflow


def test_current_docs_keep_gateway_client_neutral_and_windows_only():
    surfaces = "\n".join(
        (REPO / relative).read_text(encoding="utf-8")
        for relative in ("README.md", "docs/USER-MANUAL.md", "docs/host-integration.md", "website/app/page.tsx")
    )
    for client in ("DSH", "Codex", "Claude", "OpenCode", "LM Studio Bionic"):
        assert client in surfaces
    assert "Windows-only" in surfaces
    assert "DSH is the first client" in surfaces
    assert "standard MCP" in surfaces
