"""Disposable native Gateway, two network MCP clients and local HTTP sources.

No installed Gateway/DSH restart, account, personal profile or paid endpoint.
"""

import asyncio
import os
import socket
import subprocess
import sys

import httpx
import pytest
from aiohttp import web
from test_result_retention_native import mcp_at, read

from halo_research_gateway.providers.github import GitHubProvider


async def test_native_local_bounds_queue_pagination_and_recovery(tmp_path):
    hits = []
    active = 0
    peak = 0
    body = "Native bounded source evidence. " * 100

    async def source(request):
        nonlocal active, peak
        hits.append(request.match_info["name"])
        active += 1
        peak = max(peak, active)
        try:
            name = request.match_info["name"]
            if name == "redirect":
                raise web.HTTPFound("/forbidden")
            if name == "slow":
                await asyncio.sleep(0.6)
            else:
                await asyncio.sleep(0.03)
            text = "x" * 8192 if name in {"oversized", "compressed"} else body
            response = web.Response(text=text)
            if name == "compressed":
                response.enable_compression()
            return response
        finally:
            active -= 1

    app = web.Application()
    app.router.add_get("/research/{name}", source)
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
        f"[server]\nport={port}\nlog_level='ERROR'\n"
        f"[storage]\ndatabase='{root}/state/gateway.db'\n"
        f"backup_directory='{root}/backups'\ncontent_directory='{root}/content'\n"
        f"[crawl]\nbase_directory='{root}/browser'\n"
        "[http]\nglobal_concurrency=1\nper_origin_concurrency=1\n"
        "per_origin_interval_seconds=0\nmax_decompressed_bytes=4096\ntotal_timeout_seconds=0.3\n"
        f"[local_targets.fixture]\nscheme='http'\nhost='127.0.0.1'\nport={source_port}\n"
        "path_prefixes=['/research']\n",
        encoding="utf-8",
    )
    process = None
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
                a, b = await asyncio.gather(
                    read(first, target="fixture", path="/research/a"),
                    read(second, target="fixture", path="/research/b"),
                )
                assert a["ok"] and b["ok"], (a, b)
                assert peak == 1, "local clients bypassed shared concurrency"
                collected, pages = "", 0
                while True:
                    collected += "".join(item.get("content") or "" for item in a["items"])
                    pages += 1
                    if not a["page"]["next_cursor"]:
                        break
                    assert pages < 30
                    a = await read(first, cursor=a["page"]["next_cursor"])
                    assert a["ok"], a
                assert collected == body and pages > 1
                for name, code in (
                    ("oversized", "LOCAL_RESPONSE_TOO_LARGE"),
                    ("compressed", "LOCAL_RESPONSE_TOO_LARGE"),
                    ("redirect", "LOCAL_REDIRECT_DENIED"),
                    ("slow", "LOCAL_REQUEST_TIMEOUT"),
                ):
                    failed = await read(first, target="fixture", path=f"/research/{name}")
                    assert not failed["ok"] and failed["error"]["code"] == code, failed
                    assert not failed["items"], "failure exposed partial source as successful evidence"
                recovered = await read(second, target="fixture", path="/research/recovered")
                assert recovered["ok"], recovered
                stats = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
                assert stats["cache"]["entries"] == 0
                assert stats["queues"]["http"]["pending"] == 0
                print(
                    f"NATIVE local bounds: two MCP clients; {len(body)} characters/{pages} pages; "
                    "initial source peak=1; overflow/compression/redirect/timeout rejected; "
                    "subsequent read passed; cache entries=0; HTTP pending=0."
                )
        assert hits == ["a", "b", "oversized", "compressed", "redirect", "slow", "recovered"]
    finally:
        if process is not None:
            if process.returncode is None:
                process.kill()  # Exact disposable handle, never the installed service.
            await asyncio.wait_for(output, 10)
            assert process.returncode is not None
        await runner.cleanup()


async def test_native_public_github_response_limit_and_followup():
    # Public unauthenticated API only. No account lookup or token minting.
    provider = GitHubProvider(None, max_response_bytes=1)
    with pytest.raises(ValueError, match="^GITHUB_RESPONSE_TOO_LARGE$"):
        await provider._request_json("GET", "/rate_limit", provider._headers(None), None)
    provider.max_response_bytes = 20_971_520
    result = await provider._request_json("GET", "/rate_limit", provider._headers(None), None)
    assert isinstance(result.get("resources"), dict)
    print("NATIVE public GitHub: one-byte cap rejected real API response; normal-cap followup decoded resources.")
