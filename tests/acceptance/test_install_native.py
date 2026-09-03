"""Fresh native Windows checkout/venv, real installer, OCR, MCP, restart.

Uses existing Windows/Python/uv/Chrome prerequisites and a disposable profile;
not a clean OS, scheduled-logon or personal-profile acceptance claim.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest
from test_launcher_native import SHELLS, assert_listener_closed, fixture_environment, health

REPO = Path(__file__).resolve().parents[2]
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Native Windows installer acceptance")


@pytest.mark.parametrize("shell", SHELLS)
def test_fresh_native_install_start_stop_repair(tmp_path, shell):
    root = tmp_path / "fresh repo"
    root.mkdir()
    files = subprocess.check_output(
        [
            "git",
            "-c",
            f"safe.directory={REPO.as_posix()}",
            "-C",
            str(REPO),
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "-z",
        ],
        text=True,
    ).split("\0")
    for name in sorted(set(filter(None, files))):
        source = REPO / name
        if source.is_file():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    subprocess.run(["git", "init", str(root)], check=True, capture_output=True)
    env, port = fixture_environment(tmp_path)
    env.update(
        USERPROFILE=str(tmp_path / "user"),
        WIN_PD_OVERRIDE_LOCAL_APPDATA=str(tmp_path),
        UV_PYTHON=sys._base_executable,
        UV_PYTHON_DOWNLOADS="never",
        UV_NO_PROGRESS="1",
        PSModuleAnalysisCachePath=str(tmp_path / "module-analysis-cache"),
    )
    host = Path(env["USERPROFILE"]) / ".lmstudio/mcp.json"
    host.parent.mkdir(parents=True)
    original = {"mcpServers": {"other": {"command": "fixture-unrelated", "args": ["keep"]}}, "theme": "fixture"}
    host.write_text(json.dumps(original), encoding="utf-8")
    record = tmp_path / "HaloResearchGateway/run/gateway.json"
    traces = []
    code_hashes = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in filter(None, files)
        if (root / name).is_file()
        and (name.startswith(("src/", "scripts/", "config/")) or name in {"pyproject.toml", "uv.lock"})
    }

    class Source(BaseHTTPRequestHandler):
        def do_GET(self):
            paragraph = (
                "This local fixture describes a research source that can be read and cited after native installation. "
                * 12
            )
            rendered = json.dumps("NATIVE_JS_FROM_FRESH_INSTALL " + paragraph)
            body = (
                f"<title>Fresh install fixture</title><article>SERVER_SOURCE_FROM_FRESH_INSTALL {paragraph}</article>"
                f"<script>document.querySelector('article').textContent={rendered};</script>"
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_):
            pass

    source_server = ThreadingHTTPServer(("127.0.0.1", 0), Source)
    source_thread = threading.Thread(target=source_server.serve_forever, daemon=True)
    source_thread.start()
    test_config = Path(env["HALO_RESEARCH_CONFIG"])
    test_config.write_text(
        test_config.read_text(encoding="utf-8")
        + f"\n[local_targets.fixture]\nscheme='http'\nhost='127.0.0.1'\nport={source_server.server_port}\npath_prefixes=['/']\nmethods=['GET','HEAD']\nbrowser_allowed=true\n",
        encoding="utf-8",
    )

    def run_script(name, *args, timeout=240):
        result = subprocess.run(
            [
                shell,
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(root / "scripts" / name),
                *args,
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=root,
        )
        traces.append(
            {"script": name, "args": args, "exit": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        )
        assert result.returncode == 0, result.stdout + result.stderr
        return result

    try:
        assert not (root / ".venv").exists()
        installed = run_script("Install-HaloResearch.ps1", "-RegisterHosts", "-Start")
        assert "[GATE] PASS (Full)" in installed.stdout and "installed." in installed.stdout
        assert health(port)["status"] == "ok"
        identity = json.loads(record.read_text(encoding="utf-8-sig"))
        assert identity["repository"] == str(root)
        assert identity["executable"] == str(root / ".venv/Scripts/python.exe")
        configured = json.loads(host.read_text(encoding="utf-8-sig"))
        assert configured["mcpServers"]["other"] == original["mcpServers"]["other"]
        assert configured["theme"] == original["theme"]
        assert configured["mcpServers"]["halo-research"]["url"] == f"http://127.0.0.1:{port}/mcp"
        for folder in (".agents", ".claude", ".lmstudio"):
            skill = Path(env["USERPROFILE"]) / folder / "skills/halo-research"
            assert (skill / "SKILL.md").read_bytes() == (root / "skills/halo-research/SKILL.md").read_bytes()
            assert (skill / "references/RESEARCH-ONLY-SCOPE.md").read_bytes() == (
                root / "docs/RESEARCH-ONLY-SCOPE.md"
            ).read_bytes()
        from halo_research_gateway.ocr_data import ASSETS

        for name, _, size, digest in ASSETS:
            payload = (root / ".venv/share/tessdata" / name).read_bytes()
            assert len(payload) == size and hashlib.sha256(payload).hexdigest() == digest
        generated = tmp_path / "HaloResearchGateway/config.toml"
        probe = subprocess.run(
            [
                str(root / ".venv/Scripts/python.exe"),
                "-c",
                "import json,sys; from halo_research_gateway.config import GatewayConfig; c=GatewayConfig.load(sys.argv[1]); print(json.dumps([c.storage.database,c.storage.content_directory,c.storage.backup_directory,c.crawl.base_directory]))",
                str(generated),
            ],
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        assert probe.returncode == 0, probe.stderr
        assert all(Path(path).is_relative_to(tmp_path) for path in json.loads(probe.stdout)), (
            "Generated defaults escaped disposable profile"
        )
        # Check the actual new environment's MCP dispatcher and Chrome, not the original interpreter.
        probe_code = r"""
import asyncio,json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
async def run():
 async with streamable_http_client(URL) as streams:
  async with ClientSession(streams[0],streams[1]) as client:
   await client.initialize()
   tools=await client.list_tools()
   assert len(tools.tools)==14
   print(json.dumps(sorted(t.name for t in tools.tools)))
   for name,marker in [('local_fetch','SERVER_SOURCE_FROM_FRESH_INSTALL'),('local_crawl','NATIVE_JS_FROM_FRESH_INSTALL')]:
    response=await client.call_tool(name, {'target':'fixture','path':'/source'})
    value=json.loads('\n'.join(block.text for block in response.content if hasattr(block,'text')))
    assert not response.is_error and value['ok'], value.get('error')
    assert any(marker in item.get('content','') for item in value['items']), value
    print(json.dumps({'tool':name,'marker_found':True,'url':value['items'][0]['url']}))
asyncio.run(run())
""".replace("URL", repr(f"http://127.0.0.1:{port}/mcp"))
        probe = subprocess.run(
            [str(root / ".venv/Scripts/python.exe"), "-c", probe_code],
            env=env,
            capture_output=True,
            text=True,
            timeout=80,
        )
        traces.append(
            {"probe": "new-env-network-MCP", "exit": probe.returncode, "stdout": probe.stdout, "stderr": probe.stderr}
        )
        assert probe.returncode == 0, probe.stdout + probe.stderr
        state = tmp_path / "state/gateway.db"
        assert state.exists()
        run_script("Stop-HaloResearch.ps1", timeout=45)
        assert_listener_closed(port)
        db_before = state.read_bytes()
        config_before, host_before = generated.read_bytes(), host.read_bytes()
        # Repair uses the same locked environment and must preserve config/host records.
        repaired = run_script("Install-HaloResearch.ps1")
        assert "verified-existing" in repaired.stdout
        assert generated.read_bytes() == config_before and host.read_bytes() == host_before
        assert state.read_bytes() == db_before
        run_script("Start-HaloResearch.ps1", timeout=45)
        assert health(port)["status"] == "ok"
        after = json.loads(record.read_text(encoding="utf-8-sig"))
        assert after["started_at"] != identity["started_at"]
        run_script("Stop-HaloResearch.ps1", timeout=45)
        assert_listener_closed(port)
        assert not record.exists()
    finally:
        try:
            if record.exists():
                run_script("Stop-HaloResearch.ps1", timeout=45)
        finally:
            source_server.shutdown()
            source_server.server_close()
            source_thread.join(timeout=5)
        evidence = os.environ.get("HALO_INSTALL_NATIVE_EVIDENCE")
        if evidence:
            target = Path(evidence)
            target.mkdir(parents=True, exist_ok=True)
            (target / (shell + ".json")).write_text(
                json.dumps(
                    {
                        "fixtureRoot": str(tmp_path),
                        "shell": shell,
                        "port": port,
                        "codeHashes": code_hashes,
                        "traces": traces,
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
