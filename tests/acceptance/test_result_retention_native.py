"""Real native Gateway process, MCP clients and exact-target HTTP source.

Disposable state/ports only. No public egress, DSH, accounts or personal browser.
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
from contextlib import asynccontextmanager

import httpx
from aiohttp import web
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


@asynccontextmanager
async def mcp_at(port):
    async with httpx.AsyncClient(trust_env=False, timeout=15) as http:
        async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                yield session


async def read(session, **arguments):
    reply = await session.call_tool("local_fetch", {"max_chars": 2000, **arguments})
    wire = "\n".join(block.text for block in reply.content if hasattr(block, "text"))
    value = json.loads(wire)
    if value["ok"]:
        assert len(wire) == value["page"]["serialized_chars"] <= 2000
    return value


async def test_native_mcp_retention_shared_clients_lossless_pages_and_restart(tmp_path):
    hits = []
    body = "Native research evidence: every character must survive pagination.\n" * 120

    async def source(request):
        hits.append(request.path)
        return web.Response(text=body, content_type="text/plain")

    source_app = web.Application()
    source_app.router.add_get("/research/{name}", source)
    runner = web.AppRunner(source_app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    source_port = site._server.sockets[0].getsockname()[1]
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        gateway_port = probe.getsockname()[1]
    assert gateway_port not in {8765, source_port}
    root = tmp_path.as_posix()
    config = tmp_path / "config.toml"
    config.write_text(
        f"[server]\nport={gateway_port}\nlog_level='ERROR'\n"
        f"[storage]\ndatabase='{root}/state/gateway.db'\n"
        f"backup_directory='{root}/backups'\ncontent_directory='{root}/content'\n"
        f"[crawl]\nbase_directory='{root}/browser'\n"
        "[output]\nsnapshot_max_entries=2\nsnapshot_max_bytes=24000\n"
        f"[local_targets.fixture]\nscheme='http'\nhost='127.0.0.1'\nport={source_port}\n"
        "path_prefixes=['/research']\n",
        encoding="utf-8",
    )
    env = dict(os.environ, HALO_RESEARCH_CONFIG=str(config), LOCALAPPDATA=str(tmp_path))
    processes = []

    async def start_gateway():
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "halo_research_gateway",
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
        )
        output = asyncio.create_task(process.communicate())
        processes.append((process, output))
        async with httpx.AsyncClient(trust_env=False, timeout=1) as http:
            async with asyncio.timeout(20):
                while True:
                    if process.returncode is not None:
                        raise AssertionError((await output)[0].decode(errors="replace"))
                    try:
                        response = await http.get(f"http://127.0.0.1:{gateway_port}/health")
                        if response.status_code == 200 and response.json()["status"] == "ok":
                            return process, output
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(0.05)

    async def stop_gateway(process, output):
        if process.returncode is None:
            process.terminate()  # Only the exact native fixture process handle.
        await asyncio.wait_for(output, 10)
        assert process.returncode is not None

    try:
        first_process, first_output = await start_gateway()
        async with mcp_at(gateway_port) as first, mcp_at(gateway_port) as second:
            a, b = await asyncio.gather(
                read(first, target="fixture", path="/research/a"),
                read(second, target="fixture", path="/research/b"),
            )
            assert a["ok"] and b["ok"], (a, b)
            original_cursor, old_b = a["page"]["next_cursor"], b["page"]["next_cursor"]
            assert len(original_cursor) == len(old_b) == 51
            collected, page_count = "", 0
            while True:
                collected += "".join(item.get("content") or "" for item in a["items"])
                page_count += 1
                if not a["page"]["next_cursor"]:
                    break
                assert len(a["page"]["next_cursor"]) == 51
                assert page_count < 200
                a = await read(first, cursor=a["page"]["next_cursor"])
                assert a["ok"], a
            assert collected == body
            assert page_count > 1
            c = await read(second, target="fixture", path="/research/c")
            assert c["ok"], c
            gone = await read(second, cursor=old_b)
            assert not gone["ok"] and gone["error"]["code"] == "CURSOR_EVICTED", gone
            async with httpx.AsyncClient(trust_env=False) as http:
                stats = (await http.get(f"http://127.0.0.1:{gateway_port}/stats")).json()
                assert stats["snapshots"]["entries"] == 2
                assert 0 < stats["snapshots"]["payload_bytes"] <= 24000
                assert stats["cache"]["entries"] == 0
                assert 0 < stats["cursor_handles"]["entries"] <= 2
                assert 0 < stats["cursor_handles"]["payload_bytes"] <= 24000
        assert sorted(hits) == ["/research/a", "/research/b", "/research/c"]
        await stop_gateway(first_process, first_output)
        await start_gateway()
        async with mcp_at(gateway_port) as resumed:
            lost = await read(resumed, cursor=original_cursor)
            assert not lost["ok"] and lost["error"]["code"] == "CURSOR_EVICTED", lost
        assert len(hits) == 3, "cursor resume repeated an upstream HTTP request"
    finally:
        for process, output in processes:
            if process.returncode is None:
                process.kill()
            await asyncio.wait_for(output, 10)
        await runner.cleanup()
