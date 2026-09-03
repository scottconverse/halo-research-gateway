"""Expected job errors over actual loopback MCP, with disposable state only."""

import asyncio
import json
import os
import socket
import subprocess
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def test_native_job_control_errors_are_actionable_and_do_not_create_jobs(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    assert port != 8765
    root = tmp_path.as_posix()
    config = tmp_path / "config.toml"
    config.write_text(
        f"[server]\nport={port}\nlog_level='ERROR'\n"
        f"[storage]\ndatabase='{root}/state/gateway.db'\n"
        f"backup_directory='{root}/backups'\ncontent_directory='{root}/content'\n"
        f"[crawl]\nbase_directory='{root}/browser'\n",
        encoding="utf-8",
    )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "halo_research_gateway",
        env=dict(os.environ, HALO_RESEARCH_CONFIG=str(config), LOCALAPPDATA=str(tmp_path)),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
    )
    output = asyncio.create_task(process.communicate())
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=1) as http:
            async with asyncio.timeout(20):
                while True:
                    if process.returncode is not None:
                        raise AssertionError((await output)[0].decode(errors="replace"))
                    try:
                        health = await http.get(f"http://127.0.0.1:{port}/health")
                        if health.status_code == 200 and health.json()["status"] == "ok":
                            break
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(0.05)
        async with httpx.AsyncClient(trust_env=False, timeout=15) as http:
            async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
                async with ClientSession(streams[0], streams[1]) as client:
                    await client.initialize()
                    assert len((await client.list_tools()).tools) == 14
                    for arguments, code in [
                        ({"operation": "status", "job_id": "missing-fixture"}, "JOB_NOT_FOUND"),
                        ({"operation": "status"}, "JOB_NOT_FOUND"),
                        ({"operation": "create", "question": ""}, "INVALID_ARGUMENT"),
                        (
                            {"operation": "create", "question": "fixture", "limits": {"max_pages": 0}},
                            "INVALID_JOB_LIMITS",
                        ),
                    ]:
                        reply = await client.call_tool("research_job", arguments)
                        wire = "\n".join(block.text for block in reply.content if hasattr(block, "text"))
                        payload = json.loads(wire)
                        assert not reply.is_error, wire
                        assert payload["ok"] is False and payload["items"] == [], wire
                        assert payload["error"]["code"] == code, wire
                        assert "fixture" not in wire and len(wire) < 2000
            stats = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
            assert sum(stats["jobs"].values()) == 0
    finally:
        if process.returncode is None:
            process.terminate()  # Exact disposable fixture handle, never an installed PID.
        captured = (await asyncio.wait_for(output, 10))[0].decode(errors="replace")
        assert "missing-fixture" not in captured
        assert process.returncode is not None
