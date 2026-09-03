"""Explicit native lifecycle acceptance; never uses production state or port 8765.

Runs the actual scripts, venv launcher, Gateway process and loopback listener.
No provider calls, browser profiles or real account connections are involved.
"""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

REPO = Path(__file__).resolve().parents[2]
SHELLS = [name for name in ("powershell.exe", "pwsh.exe") if shutil.which(name)]
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows lifecycle acceptance")


def command(shell, script):
    return [
        shell,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(REPO / "scripts" / script),
    ]


def run(shell, script, env):
    result = subprocess.run(command(shell, script), env=env, capture_output=True, text=True, timeout=45)
    assert result.returncode == 0, result.stdout + result.stderr
    return result


def fixture_environment(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    assert port != 8765
    config = tmp_path / "config.toml"
    root = tmp_path.as_posix()
    config.write_text(
        f"[server]\nport = {port}\nhealth_path = '/alive'\n"
        f"[storage]\ndatabase = '{root}/state/gateway.db'\n"
        f"content_directory = '{root}/state/content'\nbackup_directory = '{root}/state/backups'\n"
        f"[crawl]\nbase_directory = '{root}/browser'\n",
        encoding="utf-8",
    )
    env = dict(os.environ, LOCALAPPDATA=str(tmp_path), HALO_RESEARCH_CONFIG=str(config))
    env["PSModulePath"] = os.pathsep.join(
        [
            str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/Modules"),
            str(Path(os.environ["ProgramFiles"]) / "WindowsPowerShell/Modules"),
        ]
    )
    return env, port


def health(port):
    with urlopen(f"http://127.0.0.1:{port}/alive", timeout=3) as response:
        return json.load(response)


def assert_listener_closed(port):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        with socket.socket() as probe:
            probe.settimeout(0.3)
            if probe.connect_ex(("127.0.0.1", port)) != 0:
                return
        time.sleep(0.1)
    pytest.fail(f"Fixture Gateway listener remains on port {port}")


@pytest.mark.parametrize("shell", SHELLS)
def test_native_duplicate_start_stop_restart(tmp_path, shell):
    env, port = fixture_environment(tmp_path)
    record = tmp_path / "HaloResearchGateway" / "run" / "gateway.json"
    unrelated = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        creationflags=subprocess.CREATE_NO_WINDOW,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    starters = []
    try:
        starters = [
            subprocess.Popen(
                command(shell, "Start-HaloResearch.ps1"),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            for _ in range(2)
        ]
        outputs = [process.communicate(timeout=45) for process in starters]
        assert all(process.returncode == 0 for process in starters), outputs
        assert sum("already running" in stdout for stdout, _ in outputs) == 1, outputs
        first = json.loads(record.read_text(encoding="utf-8-sig"))
        assert first["schema"] == 2
        assert first["repository"] == str(REPO)
        assert health(port)["status"] == "ok"
        run(shell, "Stop-HaloResearch.ps1", env)
        assert not record.exists()
        assert_listener_closed(port)
        assert unrelated.poll() is None, "Gateway stop affected an unrelated process"
        run(shell, "Start-HaloResearch.ps1", env)
        second = json.loads(record.read_text(encoding="utf-8-sig"))
        assert second["started_at"] != first["started_at"]
        assert health(port)["status"] == "ok"
        run(shell, "Stop-HaloResearch.ps1", env)
        assert_listener_closed(port)
        assert unrelated.poll() is None
    finally:
        # Only fixture-created launcher processes and the isolated PID record.
        for process in starters:
            if process.poll() is None:
                process.terminate()
            process.wait(timeout=5)
        try:
            if record.exists():
                run(shell, "Stop-HaloResearch.ps1", env)
        finally:
            unrelated.terminate()
            unrelated.wait(timeout=5)
