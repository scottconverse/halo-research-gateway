"""Execute the actual installer with dependency/service/host boundaries isolated."""

import ast
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SHELLS = [name for name in ("powershell.exe", "pwsh.exe") if shutil.which(name)]
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows installer")


def fixture(tmp_path, shell, *, register=True, git_failure=False, existing=True, host_content=None):
    root = tmp_path / "fixture repo"
    for folder in ("scripts", "config", "skills/halo-research"):
        (root / folder).mkdir(parents=True)
    for name in ("Install-HaloResearch.ps1", "HaloLifecycle.ps1"):
        shutil.copyfile(REPO / "scripts" / name, root / "scripts" / name)
    shutil.copyfile(REPO / "config/config.example.toml", root / "config/config.example.toml")
    (root / "skills/halo-research/SKILL.md").write_text("fixture skill", encoding="utf-8")
    (root / "scripts/Invoke-QualityGate.ps1").write_text("$global:LASTEXITCODE=0", encoding="utf-8")
    user = tmp_path / "user"
    host = user / ".lmstudio/mcp.json"
    host.parent.mkdir(parents=True)
    original = {
        "mcpServers": {"other": {"command": "leave-me", "args": ["fixture"]}},
        "ui": {"theme": "dark", "saved": "2026-09-01T12:00:00Z", "label": "研究"},
    }
    if existing:
        host.write_text(json.dumps(original) if host_content is None else host_content, encoding="utf-8")
    appdata = tmp_path / "appdata"
    (appdata / "HaloResearchGateway").mkdir(parents=True)
    config = appdata / "HaloResearchGateway/config.toml"
    if register:
        config.write_text('[server]\nport = 18765\nmcp_path = "/research"\n', encoding="utf-8")
    wrapper = tmp_path / "wrapper.ps1"
    wrapper.write_text(
        "$ErrorActionPreference='Stop'\n"
        "function global:uv { $global:LASTEXITCODE=0 }\n"
        f"function global:git {{ $global:LASTEXITCODE={1 if git_failure else 0} }}\n"
        # Exercise the real settings query with the installed interpreter, not a fake URL.
        "function global:Join-Path { param($Path,$ChildPath)\n"
        "if($ChildPath -eq '.venv\\Scripts\\python.exe'){return $env:HALO_INSTALL_TEST_PYTHON}\n"
        "Microsoft.PowerShell.Management\\Join-Path $Path $ChildPath }\n"
        "& (Microsoft.PowerShell.Management\\Join-Path $env:HALO_INSTALL_TEST_REPO 'scripts\\Install-HaloResearch.ps1')"
        + (" -RegisterHosts" if register else "")
        + "\n",
        encoding="utf-8",
    )
    env = dict(
        os.environ,
        LOCALAPPDATA=str(appdata),
        USERPROFILE=str(user),
        WIN_PD_OVERRIDE_LOCAL_APPDATA=str(appdata),
        HALO_INSTALL_TEST_REPO=str(root),
        HALO_INSTALL_TEST_PYTHON=str(REPO / ".venv/Scripts/python.exe"),
        HALO_RESEARCH_CONFIG=str(config),
        PSModuleAnalysisCachePath=str(tmp_path / "module-analysis-cache"),
    )
    env["PSModulePath"] = os.pathsep.join(
        [
            str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/Modules"),
            str(Path(os.environ["ProgramFiles"]) / "WindowsPowerShell/Modules"),
        ]
    )
    result = subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-File", str(wrapper)],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
        cwd=tmp_path,
    )
    return result, host, original, config, user


@pytest.mark.parametrize("shell", SHELLS)
def test_registration_preserves_other_hosts_and_uses_configured_endpoint(tmp_path, shell):
    result, host, original, _, _ = fixture(tmp_path, shell)
    assert result.returncode == 0, result.stdout + result.stderr
    merged = json.loads(host.read_text(encoding="utf-8-sig"))
    assert merged["ui"] == original["ui"] and merged["mcpServers"]["other"] == original["mcpServers"]["other"]
    assert merged["mcpServers"]["halo-research"]["url"] == "http://127.0.0.1:18765/research"
    backups = list(host.parent.glob("mcp.json.halo-backup-*"))
    assert len(backups) == 1 and json.loads(backups[0].read_text(encoding="utf-8-sig")) == original


@pytest.mark.parametrize("shell", SHELLS)
def test_new_runtime_config_does_not_point_into_developer_profile(tmp_path, shell):
    result, _, _, config, _ = fixture(tmp_path, shell, register=False)
    assert result.returncode == 0, result.stdout + result.stderr
    developer_path_found = "C:\\\\Users\\\\scott" in config.read_text(encoding="utf-8")
    assert not developer_path_found, "New configuration points into the developer's absolute profile"


@pytest.mark.parametrize("shell", SHELLS)
def test_failed_hook_setup_cannot_report_success_or_change_host_settings(tmp_path, shell):
    result, host, original, _, user = fixture(tmp_path, shell, git_failure=True)
    assert result.returncode != 0, "Installer ignored failed git hook setup"
    assert json.loads(host.read_text(encoding="utf-8")) == original
    assert not (user / ".agents/skills/halo-research").exists()


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("content", ["not-json", "null", "[]", "[{}]", '{"mcpServers":null}', '{"mcpServers":[]}'])
def test_invalid_host_config_is_preserved_without_partial_write(tmp_path, shell, content):
    result, host, _, _, _ = fixture(tmp_path, shell, host_content=content)
    assert result.returncode != 0
    assert host.read_text(encoding="utf-8") == content
    assert not list(host.parent.glob("mcp.json.halo-new-*"))


@pytest.mark.parametrize("shell", SHELLS)
def test_new_host_registration_uses_custom_config_without_changing_it(tmp_path, shell):
    result, host, _, config, _ = fixture(tmp_path, shell, existing=False)
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(host.read_text(encoding="utf-8-sig")) == {
        "mcpServers": {"halo-research": {"url": "http://127.0.0.1:18765/research"}}
    }
    assert config.read_text(encoding="utf-8") == '[server]\nport = 18765\nmcp_path = "/research"\n'


@pytest.mark.parametrize("shell", SHELLS)
def test_malformed_host_file_does_not_echo_credential_like_content(tmp_path, shell):
    marker = "fixture-private-key-do-not-log"
    result, host, _, _, _ = fixture(tmp_path, shell, host_content=marker)
    assert result.returncode != 0
    assert host.read_text(encoding="utf-8") == marker
    if marker in result.stdout + result.stderr:
        pytest.fail("Parser failure exposed fixture host contents:\n" + result.stdout + result.stderr)


def test_native_install_probe_is_valid_python():
    tree = ast.parse((REPO / "tests/acceptance/test_install_native.py").read_text(encoding="utf-8"))
    scripts = [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and "asyncio.run(run())" in node.value
    ]
    assert len(scripts) == 1
    compile(scripts[0], "native-install-MCP-probe", "exec")
