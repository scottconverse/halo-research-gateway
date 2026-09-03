"""Native Chrome/MCP routing with a public header echo and local fake vendor.

No paid endpoint, real account, installed Gateway, DSH or personal profile is used.
The echo is an intentional challenge signal, not a claim of bypassing a real gate.
"""

import asyncio
import json
import socket
from contextlib import AsyncExitStack

import httpx
import psutil
import pytest
import uvicorn
from aiohttp import web
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig, OptionalProviderConfig
from halo_research_gateway.models import LocalTarget
from halo_research_gateway.providers import paid
from halo_research_gateway.providers.crawl4ai_provider import Crawl4AIProvider
from halo_research_gateway.providers.optional import OptionalProviderError
from halo_research_gateway.service import HaloService

ECHO = "https://httpbingo.org/response-headers?cf-mitigated=challenge"
GATE = '<title>Just a moment...</title><script src="/cdn-cgi/challenge-platform/test.js"></script><p>Verify you are human</p>'


@pytest.mark.parametrize("status", [200, 403])
async def test_native_chrome_rejects_local_challenge_without_outsourcing(tmp_path, status):
    async def page(request):
        return web.Response(text=GATE, status=status, content_type="text/html")

    app = web.Application()
    app.router.add_get("/research", page)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    target = LocalTarget("fixture", "http", "127.0.0.1", port, ("/research",), browser_allowed=True)
    provider = Crawl4AIProvider(str(tmp_path / "browser"))
    try:
        with pytest.raises(RuntimeError, match="^CRAWL_CHALLENGE_REQUIRED$"):
            await provider.crawl(target.build_url("/research"), public=False, local_target=target)
        assert provider._crawler is None
    finally:
        await provider.close()
        await runner.cleanup()


async def test_native_mcp_two_clients_route_challenge_to_fake_vendor_and_recover_budget(tmp_path, monkeypatch):
    before = {process.pid for process in psutil.Process().children(recursive=True)}
    vendor_calls = []
    fixture_text = "A controlled fixture supplies independently readable research evidence. " * 24

    async def vendor(request):
        body = await request.json()
        assert request.headers["Authorization"] == "Bearer fixture-only-key"
        assert body == {"zone": "fixture-only-zone", "url": ECHO, "format": "json", "method": "GET"}
        vendor_calls.append(body)
        return web.json_response(
            {
                "status_code": 200,
                "headers": {"content-type": "text/html"},
                "body": f"<title>Fixture source</title><p>{fixture_text}</p>",
            }
        )

    vendor_app = web.Application()
    vendor_app.router.add_post("/request", vendor)
    vendor_runner = web.AppRunner(vendor_app)
    await vendor_runner.setup()
    vendor_site = web.TCPSite(vendor_runner, "127.0.0.1", 0)
    await vendor_site.start()
    vendor_port = vendor_site._server.sockets[0].getsockname()[1]

    class VendorTransport(httpx.AsyncBaseTransport):
        """Test-only interception: the production fixed vendor API cannot leave loopback."""

        def __init__(self, target, address):
            assert target.host == "api.brightdata.com" and target.path_query == "/request"
            self.inner = httpx.AsyncHTTPTransport()

        async def handle_async_request(self, request):
            assert request.url.host == "api.brightdata.com" and request.url.path == "/request"
            local = httpx.Request(
                request.method,
                f"http://127.0.0.1:{vendor_port}/request",
                headers=request.headers,
                content=await request.aread(),
            )
            return await self.inner.handle_async_request(local)

        async def aclose(self):
            await self.inner.aclose()

    async def vendor_dns(target):
        assert target.host == "api.brightdata.com"
        return "127.0.0.1"

    monkeypatch.setattr(paid, "PinnedTransport", VendorTransport)
    monkeypatch.setattr(paid, "resolve_public", vendor_dns)
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    config.crawl.base_directory = str(tmp_path / "browser")
    config.server.log_level = "ERROR"
    app = create_application(config)
    service = app.state.halo_service
    connection = service.connections.create(
        "brightdata", "fixture", "api_key", {"api_key": "fixture-only-key", "zone": "fixture-only-zone"}
    )
    config.proxy = OptionalProviderConfig(
        enabled=True,
        provider="brightdata",
        connection_id=connection["connection_id"],
        allowed_domains=["httpbingo.org"],
        daily_attempt_limit=1,
        daily_spend_limit_usd=0.02,
        request_cost_usd=0.02,
    )
    service.optional_providers.configs["proxy"] = config.proxy
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    port = listener.getsockname()[1]
    assert port != 8765
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", access_log=False, lifespan="on"))
    task = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        async with asyncio.timeout(120):
            while not server.started:
                assert not task.done(), "Native fixture Gateway did not start"
                await asyncio.sleep(0.05)
            async with AsyncExitStack() as stack:
                clients = []
                for _ in range(2):
                    http = await stack.enter_async_context(httpx.AsyncClient(trust_env=False, timeout=90))
                    stream = await stack.enter_async_context(
                        streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http)
                    )
                    session = await stack.enter_async_context(ClientSession(stream[0], stream[1]))
                    await session.initialize()
                    clients.append(session)

                async def call(client, arguments):
                    response = await client.call_tool(
                        "web_crawl", dict(arguments, max_chars=2000), read_timeout_seconds=90
                    )
                    text = "\n".join(block.text for block in response.content if hasattr(block, "text"))
                    value = json.loads(text)
                    assert not response.is_error and value["ok"], value.get("error")
                    assert len(text) == value["page"]["serialized_chars"] <= 2000
                    assert "fixture-only-key" not in text and "fixture-only-zone" not in text
                    assert all(row["url"] == ECHO for row in value["items"])
                    return value

                first, concurrent = await asyncio.gather(*(call(client, {"url": ECHO}) for client in clients))
                assert len(vendor_calls) == 1
                assert first["items"] == concurrent["items"]
                page, content, pages = first, "", 0
                while True:
                    content += "".join(row.get("content") or "" for row in page["items"])
                    pages += 1
                    if not page["page"]["next_cursor"]:
                        break
                    assert pages < 100
                    page = await call(clients[1], {"cursor": page["page"]["next_cursor"]})
                assert fixture_text.strip() in content
                assert first["items"][0]["metadata"]["retrieval_provider"] == "brightdata"
                assert "PROXY_FINAL_URL_UNVERIFIED" in first["warnings"]
                again = await call(clients[0], {"url": ECHO})
                assert again["cache"]["hit"] and len(vendor_calls) == 1
                assert service.crawler._crawler is None
                print(
                    json.dumps(
                        {
                            "native_chrome_public_header_echo": True,
                            "native_network_mcp_clients": 2,
                            "local_fake_vendor_requests": len(vendor_calls),
                            "real_paid_requests": 0,
                            "content_chars": len(content),
                            "pages": pages,
                            "cache_reuse": True,
                            "reserved_estimated_usd": service.optional_providers.status()["proxy"]["spend_usd_today"],
                        }
                    )
                )
    finally:
        server.should_exit = True
        await asyncio.wait_for(task, 15)
        listener.close()
        await service.close()
        await vendor_runner.cleanup()

    restarted = HaloService(config)
    try:
        assert restarted.optional_providers.status()["proxy"]["attempts_today"] == 1
        with pytest.raises(OptionalProviderError, match="ATTEMPT_BUDGET_EXHAUSTED"):
            await restarted.optional_providers.execute("proxy", "httpbingo.org", url=ECHO)
        assert len(vendor_calls) == 1
    finally:
        await restarted.close()
    leaked = [
        process.pid
        for process in psutil.Process().children(recursive=True)
        if process.pid not in before and process.is_running()
    ]
    assert not leaked, f"Fixture left owned children: {leaked}"
    print("Native Chrome/MCP fake-vendor routing, durable budget and owned-browser cleanup PASS")
