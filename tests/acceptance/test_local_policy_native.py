"""Native local read policy and synthetic session URL confidentiality."""

import asyncio
import json
import os
import socket
import subprocess
import sys

import httpx
import pytest
from aiohttp import web
from test_result_retention_native import mcp_at, read


@pytest.mark.parametrize("log_level", ["ERROR", "INFO", "DEBUG"])
async def test_native_local_policy_preserves_evidence_without_query_leak(tmp_path, log_level):
    calls = []
    secret = "fixture-native-session-value"
    body = "Native research session evidence. " * 100

    async def source(request):
        calls.append(dict(request.query))
        assert request.query.get("token") == secret
        return web.Response(text=body)

    app = web.Application()
    app.router.add_get("/research/source", source)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    source_port = site._server.sockets[0].getsockname()[1]
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    assert port not in {8765, source_port}
    root = tmp_path.as_posix()
    config = tmp_path / "config.toml"
    config.write_text(
        f"[server]\nport={port}\nlog_level='{log_level}'\n"
        f"[storage]\ndatabase='{root}/state/gateway.db'\n"
        f"backup_directory='{root}/backups'\ncontent_directory='{root}/content'\n"
        f"[crawl]\nbase_directory='{root}/browser'\n"
        "[http]\nper_origin_interval_seconds=0\n"
        f"[local_targets.reader]\nscheme='http'\nhost='127.0.0.1'\nport={source_port}\n"
        "path_prefixes=['/research']\nmethods=['GET']\n"
        f"[local_targets.head_only]\nscheme='http'\nhost='127.0.0.1'\nport={source_port}\n"
        "path_prefixes=['/research']\nmethods=['HEAD']\n",
        encoding="utf-8",
    )
    process = None
    captured = b""
    try:
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
        async with httpx.AsyncClient(trust_env=False, timeout=1) as http:
            async with asyncio.timeout(20):
                while True:
                    if process.returncode is not None:
                        raise AssertionError((await output)[0].decode(errors="replace"))
                    try:
                        if (await http.get(f"http://127.0.0.1:{port}/health")).status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(0.05)
            async with mcp_at(port) as first, mcp_at(port) as second:
                path = f"/research/source?token={secret}"
                denied = await read(first, target="head_only", path=path)
                assert not denied["ok"] and denied["error"]["code"] == "LOCAL_METHOD_NOT_ALLOWED", denied
                assert calls == []
                result = await read(first, target="reader", path=path)
                collected, pages = "", 0
                while True:
                    assert result["ok"] and secret not in json.dumps(result), result
                    collected += "".join(item.get("content") or "" for item in result["items"])
                    pages += 1
                    cursor = result["page"]["next_cursor"]
                    if not cursor:
                        break
                    assert pages < 100
                    result = await read(second, cursor=cursor)
                assert collected == body and pages > 1 and len(calls) == 1
                stats = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
                assert stats["cache"]["entries"] == 0
                print(
                    f"Native local policy: denied target made zero requests; {len(body)} characters/{pages} pages; one source read; no disk cache."
                )
    finally:
        if process is not None:
            if process.returncode is None:
                process.kill()  # Exact disposable child only.
            captured = (await asyncio.wait_for(output, 10))[0]
            assert process.returncode is not None
        await runner.cleanup()
    assert secret.encode() not in captured, "Gateway stdout/stderr exposed the synthetic session query value"
