"""Native MCP and loopback fake GitHub API; no accounts or installed services."""

import asyncio
import json
import os
import socket
import subprocess
import sys

import httpx
from aiohttp import web
from test_result_retention_native import mcp_at

BOOTSTRAP = """
import sys
import uvicorn
from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.providers import github

github.API_BASE = "http://github-fixture.example.test:" + sys.argv[2]
async def fixture_resolve(target):
    assert target.host == "github-fixture.example.test" and target.port == int(sys.argv[2])
    return "127.0.0.1"
github.resolve_public = fixture_resolve
class FixtureConnections:
    def list(self):
        return [{"connection_id": "fixture", "provider": "github", "status": "ready"}]
    def secret(self, connection_id):
        assert connection_id == "fixture"
        return {"token": "synthetic-native-token"}
config = GatewayConfig.load(sys.argv[1])
app = create_application(config)
app.state.halo_service.github.connections = FixtureConnections()
uvicorn.run(app, host="127.0.0.1", port=config.server.port, log_level="error")
"""


async def test_native_mcp_github_total_bounds_and_followup_clients(tmp_path):
    hits, disconnected = [], []
    second_started = asyncio.Event()
    disconnect_seen = asyncio.Event()

    async def source(request):
        query = request.query.get("q", "").split(" ")[0]
        # GitHub searches both issue and PR kinds through /search/issues.
        endpoint = "pulls" if "is:pr" in request.query.get("q", "") else request.match_info["endpoint"]
        hits.append((query, endpoint))
        if query == "slow":
            if endpoint == "issues":
                await asyncio.sleep(0.5)
            else:
                response = web.StreamResponse(headers={"content-type": "application/json"})
                await response.prepare(request)
                await response.write(b'{"items":[')
                second_started.set()
                for _ in range(110):
                    await asyncio.sleep(0.025)
                    if request.transport is None or request.transport.is_closing():
                        disconnected.append(query)
                        disconnect_seen.set()
                        return response
                await response.write(b"]}")
                return response
        body = "synthetic-private-evidence-" + "x" * 2400 if query == "aggregate" else f"Source for {query}/{endpoint}"
        return web.json_response(
            {
                "items": [
                    {
                        "html_url": f"https://github.com/acme/widgets/{endpoint}/1",
                        "title": f"{query} {endpoint}",
                        "body": body,
                    }
                ]
            }
        )

    api = web.Application()
    api.router.add_get("/search/{endpoint}", source)
    runner = web.AppRunner(api)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    api_port = site._server.sockets[0].getsockname()[1]
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    assert port not in {8765, api_port}
    root = tmp_path.as_posix()
    config = tmp_path / "config.toml"
    config.write_text(
        f"[server]\nport={port}\nlog_level='ERROR'\n"
        f"[storage]\ndatabase='{root}/state/gateway.db'\n"
        f"backup_directory='{root}/backups'\ncontent_directory='{root}/content'\n"
        f"[crawl]\nbase_directory='{root}/browser'\n"
        "[http]\nglobal_concurrency=2\nmax_decompressed_bytes=4096\ntotal_timeout_seconds=3\n",
        encoding="utf-8",
    )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-c",
        BOOTSTRAP,
        str(config),
        str(api_port),
        env=dict(os.environ, LOCALAPPDATA=str(tmp_path)),
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
                        response = await http.get(f"http://127.0.0.1:{port}/health")
                        if response.status_code == 200 and response.json()["status"] == "ok":
                            break
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(0.05)

        async def read(client, query):
            reply = await client.call_tool(
                "github_research",
                {
                    "query": query,
                    "repository": "acme/widgets",
                    "kinds": ["issues", "pulls"],
                    "max_results": 10,
                    "max_chars": 4000,
                },
            )
            wire = "\n".join(block.text for block in reply.content if hasattr(block, "text"))
            assert not reply.is_error and len(wire) <= 4000
            assert "synthetic-native-token" not in wire
            return json.loads(wire)

        async with mcp_at(port) as first, mcp_at(port) as second:
            tools = await first.list_tools()
            assert len(tools.tools) == 14
            for query, code in (("aggregate", "GITHUB_OPERATION_TOO_LARGE"), ("slow", "GITHUB_OPERATION_TIMEOUT")):
                result = await read(first, query)
                assert not result["ok"] and result["error"]["code"] == code, result
                assert not result["items"]
                assert "synthetic-private-evidence" not in json.dumps(result)
            assert second_started.is_set(), "Only the first request timed out; whole-operation path was not exercised"
            await asyncio.wait_for(disconnect_seen.wait(), 2)
            results = await asyncio.gather(read(first, "normal-a"), read(second, "normal-b"), return_exceptions=True)
            assert not any(isinstance(result, BaseException) for result in results), results
            assert all(result["ok"] and len(result["items"]) == 2 for result in results), results
            assert all(result["items"][0]["url"].startswith("https://github.com/") for result in results)
        async with httpx.AsyncClient(trust_env=False) as http:
            stats = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
            assert stats["queues"]["http"]["pending"] == 0
            assert stats["cache"]["entries"] == 0
        assert [endpoint for query, endpoint in hits if query == "slow"] == ["issues", "pulls"]
        assert [endpoint for query, endpoint in hits if query == "aggregate"] == ["issues", "pulls"]
        print(
            json.dumps(
                {
                    "tools": 14,
                    "mcp_clients": 2,
                    "aggregate_error": "GITHUB_OPERATION_TOO_LARGE",
                    "deadline_error": "GITHUB_OPERATION_TIMEOUT",
                    "second_request_disconnected": True,
                    "followup_source_counts": [len(result["items"]) for result in results],
                    "http_pending": 0,
                    "cache_entries": 0,
                    "real_github_authentication": False,
                }
            )
        )
    finally:
        try:
            if process.returncode is None:
                process.terminate()
            await asyncio.wait_for(output, 10)
            assert process.returncode is not None
            logs = (await output)[0].decode(errors="replace")
            assert "synthetic-native-token" not in logs and "synthetic-private-evidence" not in logs
        finally:
            await runner.cleanup()
