"""Real Chrome + two network MCP clients + loopback fake solver. No paid calls."""

import asyncio
import json
import socket
from contextlib import AsyncExitStack
from urllib.parse import urlsplit

import httpx
import psutil
import pytest
import uvicorn
from aiohttp import web
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig, OptionalProviderConfig
from halo_research_gateway.providers import crawl4ai_provider
from halo_research_gateway.providers.paid import CapSolverAdapter

URL = "https://research.example/read"
TOKEN = "fixture-native-token-do-not-return"
TEXT = "NATIVE_SOURCE_EVIDENCE: independently readable research facts. " * 25


@pytest.mark.parametrize(
    "kind,navigate,cancel_solver",
    [("turnstile", False, False), ("recaptcha", False, False), ("turnstile", True, False), ("turnstile", False, True)],
)
async def test_native_token_application_two_mcp_clients_and_cleanup(
    tmp_path, monkeypatch, kind, navigate, cancel_solver
):
    before = {p.pid for p in psutil.Process().children(recursive=True)}
    calls, browser_requests, callback_proofs = [], [], []
    vendor_entered, vendor_release = asyncio.Event(), asyncio.Event()
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    config.crawl.base_directory = str(tmp_path / "browser")
    config.http.per_origin_interval_seconds = 0
    app = create_application(config)
    service = app.state.halo_service
    connection = service.connections.create("capsolver", "fixture", "api_key", {"api_key": "fixture-only-key"})
    service.optional_providers.configs["captcha"] = OptionalProviderConfig(
        enabled=True,
        provider="capsolver",
        connection_id=connection["connection_id"],
        allowed_domains=["research.example"],
        daily_attempt_limit=1,
        daily_spend_limit_usd=0.01,
        request_cost_usd=0.01,
    )

    async def vendor(request):
        body = await request.json()
        assert body["clientKey"] == "fixture-only-key"
        assert body["task"] == {
            "type": "AntiTurnstileTaskProxyLess" if kind == "turnstile" else "ReCaptchaV2TaskProxyLess",
            "websiteURL": URL,
            "websiteKey": "fixture-key",
        }
        calls.append(body)
        if cancel_solver:
            vendor_entered.set()
            await vendor_release.wait()
        return web.json_response(
            {"status": "ready", "solution": {"token" if kind == "turnstile" else "gRecaptchaResponse": TOKEN}}
        )

    vendor_app = web.Application()
    vendor_app.router.add_post("/createTask", vendor)
    runner = web.AppRunner(vendor_app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    vendor_port = site._server.sockets[0].getsockname()[1]

    async def requester(method, path, headers, body):
        assert method == "POST" and path == "/createTask"
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.post(f"http://127.0.0.1:{vendor_port}/createTask", json=body)
            response.raise_for_status()
            return response.json()

    service.optional_providers.register("captcha", "capsolver", CapSolverAdapter(requester=requester))
    original_guard = service.crawler._guard_page
    original_resolve = crawl4ai_provider.resolve_public

    async def resolve(target):
        if target.host == "research.example":
            return "93.184.216.34"
        return await original_resolve(target)

    async def guard(page, context, *args, **kwargs):
        await original_guard(page, context, *args, **kwargs)

        async def fixture(route, request):
            if urlsplit(request.url).hostname != "research.example":
                await route.abort()
                return
            await service.crawler._validate_browser_request(request.url, True, None, request.method)
            browser_requests.append((request.method, request.url))
            if request.url.endswith("/proof"):
                callback_proofs.append(True)
                await route.fulfill(status=200, body="ok")
                return
            if request.url.endswith("/source"):
                await route.fulfill(
                    status=200,
                    content_type="text/html",
                    body=f"<title>Research source</title><article>{TEXT}</article>",
                )
                return
            widget = "cf-turnstile" if kind == "turnstile" else "g-recaptcha"
            field = "cf-turnstile-response" if kind == "turnstile" else "g-recaptcha-response"
            completed = (
                "location.href='/source'"
                if navigate
                else "document.title='Research source'; document.body.innerHTML="
                + json.dumps(f"<article>{TEXT} {TOKEN}</article>")
            )
            html = f"""<title>Verify you are human</title><body>
<div class="{widget}" data-sitekey="fixture-key" data-callback="research.solved"></div>
<textarea name="{field}"></textarea><script>window.research={{solved:async function(token){{
if(token !== {json.dumps(TOKEN)} || document.querySelector('textarea').value !== token) throw Error('wrong fixture token');
await fetch('/proof'); {completed};
}}}};</script></body>"""
            await route.fulfill(status=403 if navigate else 200, content_type="text/html", body=html)

        await context.route("**/*", fixture)

    monkeypatch.setattr(crawl4ai_provider, "resolve_public", resolve)
    monkeypatch.setattr(service.crawler, "_guard_page", guard)
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen()
    server = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="on"))
    task = asyncio.create_task(server.serve(sockets=[listener]))
    try:
        async with asyncio.timeout(45):
            while not server.started:
                if task.done():
                    task.result()
                await asyncio.sleep(0.01)
        async with AsyncExitStack() as stack:
            clients = []
            for _ in range(2):
                streams = await stack.enter_async_context(
                    streamable_http_client(f"http://127.0.0.1:{listener.getsockname()[1]}/mcp")
                )
                client = await stack.enter_async_context(ClientSession(streams[0], streams[1]))
                await client.initialize()
                clients.append(client)

            async def call(client):
                response = await client.call_tool("web_crawl", {"url": URL, "max_chars": 6000})
                value = json.loads("\n".join(block.text for block in response.content if hasattr(block, "text")))
                assert not response.is_error and value["ok"], json.dumps(
                    {"error": value.get("error"), "warnings": value.get("warnings")}
                )
                assert TEXT.strip() in value["items"][0]["content"]
                assert TOKEN not in json.dumps(value) and "fixture-only-key" not in json.dumps(value)
                assert value["items"][0]["url"] == ("https://research.example/source" if navigate else URL)
                assert value["items"][0]["metadata"]["retrieval_provider"] == "capsolver"
                assert "CAPTCHA_RETRIEVAL_USED" in value["warnings"]
                return value

            if cancel_solver:
                operation = asyncio.create_task(service.crawler.crawl(URL))
                try:
                    await asyncio.wait_for(vendor_entered.wait(), 15)
                    operation.cancel()
                    with pytest.raises(asyncio.CancelledError):
                        await asyncio.wait_for(operation, 10)
                    assert not callback_proofs
                finally:
                    operation.cancel()
                    await asyncio.gather(operation, return_exceptions=True)
                    vendor_release.set()
            else:
                results = await asyncio.gather(*(call(client) for client in clients))
                assert results[0]["items"] == results[1]["items"]
                assert len(calls) == 1 and callback_proofs == [True]
                assert all(method == "GET" for method, _ in browser_requests)
            assert service.optional_providers.status()["captcha"]["attempts_today"] == 1
            assert service.crawler._crawler is None
    finally:
        vendor_release.set()
        server.should_exit = True
        await asyncio.wait_for(task, 15)
        listener.close()
        await service.close()
        await runner.cleanup()
    children = [p for p in psutil.Process().children(recursive=True) if p.pid not in before]
    _, alive = await asyncio.to_thread(psutil.wait_procs, children, timeout=15)
    assert not alive, "Owned browser child survived cleanup"
