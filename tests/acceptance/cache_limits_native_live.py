"""Real native Gateway cache capacity, two-client traffic and restart proof.

Uses only public Python documentation in disposable loopback instances. Does not
change installed Gateway/DSH configuration, accounts, profiles or paid providers.
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import tempfile
from contextlib import AsyncExitStack
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

SOURCE = "https://docs.python.org/3/library/asyncio-exceptions.html"
CAPACITY = 4096


async def read_page(session, arguments, budget=2000):
    result = await session.call_tool("web_fetch", dict(arguments, max_chars=budget), read_timeout_seconds=40)
    wire = "\n".join(block.text for block in result.content if hasattr(block, "text"))
    value = json.loads(wire)
    assert not result.is_error and value["ok"], value.get("error")
    assert len(wire) == value["page"]["serialized_chars"] <= budget
    assert all(row["url"].startswith(SOURCE) for row in value["items"])
    return value


async def collect(session, first, budget=2000):
    content, page, count = "", first, 0
    while True:
        content += "".join(row.get("content") or "" for row in page["items"])
        count += 1
        cursor = page["page"]["next_cursor"]
        if not cursor:
            return content, count
        assert count < 100
        page = await read_page(session, {"cursor": cursor}, budget)


async def sessions(stack, url):
    clients = []
    for _ in range(2):
        http = await stack.enter_async_context(httpx.AsyncClient(trust_env=False, timeout=45))
        streams = await stack.enter_async_context(streamable_http_client(url, http_client=http))
        session = await stack.enter_async_context(ClientSession(streams[0], streams[1]))
        await session.initialize()
        clients.append(session)
    return clients


async def main():
    with tempfile.TemporaryDirectory(prefix="halo-cache-capacity-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        assert port != 8765
        address = f"http://127.0.0.1:{port}"
        config = root / "config.toml"
        base = root.as_posix()
        process, output = None, None

        async def configure(limit):
            content = (
                f"[server]\nport={port}\nlog_level='ERROR'\n"
                f"[storage]\ndatabase='{base}/state/gateway.db'\n"
                f"backup_directory='{base}/backups'\ncontent_directory='{base}/content'\n"
                f"cache_max_bytes={limit}\nentry_max_bytes={limit}\n"
                f"[crawl]\nbase_directory='{base}/browser'\n"
            )
            await asyncio.to_thread(config.write_text, content, encoding="utf-8")

        async def launch():
            nonlocal process, output
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "halo_research_gateway",
                env=dict(os.environ, HALO_RESEARCH_CONFIG=str(config), LOCALAPPDATA=str(root)),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
            )
            output = asyncio.create_task(process.communicate())
            async with httpx.AsyncClient(trust_env=False, timeout=1) as http:
                async with asyncio.timeout(20):
                    while True:
                        assert process.returncode is None, "Owned native Gateway exited during startup"
                        try:
                            response = await http.get(address + "/health")
                            if response.status_code == 200:
                                return response.json()["started_at"]
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.1)

        async def stop():
            if process is None:
                return
            if process.returncode is None:
                process.terminate()
            try:
                stdout, _ = await asyncio.wait_for(asyncio.shield(output), 15)
            except TimeoutError:
                process.kill()
                stdout, _ = await asyncio.wait_for(output, 5)
            if stdout:
                print("NATIVE GATEWAY OUTPUT:", stdout.decode(errors="replace"), flush=True)
            assert process.returncode is not None

        samples, watching = [], None
        stopped = asyncio.Event()

        async def watch():
            async with httpx.AsyncClient(trust_env=False, timeout=5) as http:
                while not stopped.is_set():
                    value = (await http.get(address + "/stats")).json()["cache"]
                    assert value["max_bytes"] == CAPACITY and value["entry_max_bytes"] == CAPACITY
                    samples.append(value["total_compressed_bytes"])
                    assert samples[-1] <= CAPACITY, "Native MCP clients exceeded shared cache limit"
                    await asyncio.sleep(0.05)

        try:
            async with asyncio.timeout(180):
                await configure(CAPACITY)
                first_start = await launch()
                async with AsyncExitStack() as stack:
                    clients = await sessions(stack, address + "/mcp")
                    first = await read_page(clients[0], {"url": SOURCE + "?halo_cache_case=0"})
                    assert first["page"]["next_cursor"] and first["cache"]["key"]
                    watching = asyncio.create_task(watch())

                    async def fetch(index):
                        initial = await read_page(
                            clients[index % 2], {"url": SOURCE + f"?halo_cache_case={index}"}, 6000
                        )
                        assert initial["cache"]["key"], initial["warnings"]
                        body, _ = await collect(clients[index % 2], initial, 6000)
                        assert len(body) > 500 and "CancelledError" in body
                        return body

                    bodies = await asyncio.gather(*(fetch(index) for index in range(1, 8)))
                    last_url = SOURCE + "?halo_cache_case=8"
                    last = await read_page(clients[1], {"url": last_url})
                    assert last["page"]["next_cursor"]
                    cached_last = await read_page(clients[0], {"url": last_url})
                    assert cached_last["cache"]["hit"]
                    original_body, pages = await collect(clients[1], first)
                    assert all(body == original_body for body in bodies)
                    assert (await collect(clients[0], last))[0] == original_body
                    async with httpx.AsyncClient(trust_env=False, timeout=5) as http:
                        stats = (await http.get(address + "/stats")).json()
                    assert 0 < stats["cache"]["entries"] < 9, "No actual eviction occurred"
                    assert all(
                        not item["enabled"] and item["attempts_today"] == 0
                        for item in stats["optional_providers"].values()
                    )
                    stopped.set()
                    await watching
                    print(
                        json.dumps(
                            {
                                "case": "two_native_mcp_clients_shared_cache",
                                "unique_urls": 9,
                                "samples": len(samples),
                                "peak_compressed_bytes": max(samples),
                                "limit": CAPACITY,
                                "retained_entries": stats["cache"]["entries"],
                                "body_chars": len(original_body),
                                "evicted_source_memory_pages": pages,
                                "recent_source_cache_hit": True,
                            }
                        ),
                        flush=True,
                    )
                await stop()
                assert await launch() != first_start
                async with AsyncExitStack() as stack:
                    clients = await sessions(stack, address + "/mcp")
                    old = await clients[0].call_tool("web_fetch", {"cursor": first["page"]["next_cursor"]})
                    value = json.loads("\n".join(block.text for block in old.content if hasattr(block, "text")))
                    assert not value["ok"] and value["error"]["code"] == "CURSOR_EVICTED"
                    resumed = await read_page(clients[1], {"cursor": last["page"]["next_cursor"]})
                    tail, remaining = await collect(clients[1], resumed)
                    prefix = "".join(row.get("content") or "" for row in last["items"])
                    assert prefix + tail == original_body
                    print(
                        json.dumps(
                            {
                                "case": "restart",
                                "evicted_cursor": "CURSOR_EVICTED",
                                "retained_cursor_identical": True,
                                "remaining_pages": remaining,
                            }
                        ),
                        flush=True,
                    )
                await stop()
                await configure(100)
                await launch()
                async with AsyncExitStack() as stack:
                    clients = await sessions(stack, address + "/mcp")
                    uncached = await read_page(clients[0], {"url": last_url})
                    assert uncached["cache"]["key"] == ""
                    assert "RESULT_NOT_CACHED_TOO_LARGE" in uncached["warnings"]
                    assert (await collect(clients[1], uncached))[0] == original_body
                    async with httpx.AsyncClient(trust_env=False, timeout=5) as http:
                        stats = (await http.get(address + "/stats")).json()["cache"]
                    assert stats["entries"] == 0 and stats["max_bytes"] == 100
                    print(
                        json.dumps(
                            {
                                "case": "lowered_cache_limit",
                                "body_preserved": True,
                                "warning": "RESULT_NOT_CACHED_TOO_LARGE",
                                "cache": stats,
                            }
                        ),
                        flush=True,
                    )
                print("Native shared cache limit, eviction/restart and uncached evidence PASS", flush=True)
        finally:
            stopped.set()
            if watching is not None and not watching.done():
                watching.cancel()
                await asyncio.gather(watching, return_exceptions=True)
            await stop()
            print(
                json.dumps({"owned_native_process_stopped": process is None or process.returncode is not None}),
                flush=True,
            )
    print("Temporary native Gateway state removed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
