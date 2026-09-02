"""Real Chrome/Crawl4AI acceptance; no personal profile or external sites."""

import pytest
from aiohttp import web

from halo_research_gateway.models import LocalTarget
from halo_research_gateway.providers.crawl4ai_provider import Crawl4AIProvider


@pytest.mark.asyncio
async def test_rendered_research_enforces_http_and_websocket_target(tmp_path):
    hits = []

    async def forbidden(request):
        hits.append(("forbidden", request.method, request.path))
        return web.Response(text="should never be read")

    peer = web.Application()
    peer.router.add_route("*", "/{tail:.*}", forbidden)
    peer_runner = web.AppRunner(peer)
    await peer_runner.setup()
    peer_site = web.TCPSite(peer_runner, "127.0.0.1", 0)
    await peer_site.start()
    peer_port = peer_site._server.sockets[0].getsockname()[1]

    async def page(request):
        return web.Response(
            content_type="text/html",
            text="""<!doctype html>
<html><head><title>Gateway browser fixture</title></head><body>
<h1>Research fixture</h1><div id="results"></div><script>
async function get(url, options) {
  try { return await (await fetch(url, options)).text(); }
  catch (_) { return 'BLOCKED'; }
}
function socket(path) {
  return new Promise(resolve => {
    const ws = new WebSocket('ws://' + location.host + path);
    const timer = setTimeout(() => { ws.close(); resolve('TIMEOUT'); }, 5000);
    ws.onmessage = e => { clearTimeout(timer); ws.close(); resolve(e.data); };
    ws.onclose = () => { clearTimeout(timer); resolve('BLOCKED'); };
    ws.onerror = () => { clearTimeout(timer); resolve('BLOCKED'); };
  });
}
(async () => {
  const values = await Promise.all([
    get('/research/data'), get('/outside'),
    get('http://127.0.0.1:PEER_PORT/other'),
    get('/research/data', {method:'POST'}),
    socket('/research/socket'), socket('/outside/socket')
  ]);
  document.querySelector('#results').textContent = values.join(' | ');
  const ready = document.createElement('p'); ready.id = 'ready';
  ready.textContent = 'RESEARCH_READY'; document.body.appendChild(ready);
})();</script></body></html>""".replace("PEER_PORT", str(peer_port)),
        )

    async def data(request):
        hits.append(("allowed", request.method, request.path))
        return web.Response(text="DYNAMIC_EVIDENCE")

    async def websocket(request):
        hits.append(("allowed", "WS", request.path))
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        await ws.send_str("WEBSOCKET_EVIDENCE")
        await ws.close()
        return ws

    app = web.Application()
    app.router.add_get("/research/page", page)
    app.router.add_get("/research/data", data)
    app.router.add_get("/research/socket", websocket)
    app.router.add_route("*", "/{tail:.*}", forbidden)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    target = LocalTarget("research-fixture", "http", "127.0.0.1", port, ("/research",), browser_allowed=True)
    provider = Crawl4AIProvider(str(tmp_path / "browser"))
    try:
        result = await provider.crawl(
            target.build_url("/research/page"), public=False, local_target=target, wait_for="#ready"
        )
        text = result.items[0].content
        assert "DYNAMIC_EVIDENCE | BLOCKED | BLOCKED | BLOCKED | WEBSOCKET_EVIDENCE | BLOCKED" in text
        assert "RESEARCH_READY" in text
        assert result.items[0].url == target.build_url("/research/page")
        assert not [hit for hit in hits if hit[0] == "forbidden"]
        assert ("allowed", "WS", "/research/socket") in hits
    finally:
        await provider.close()
        await runner.cleanup()
        await peer_runner.cleanup()


@pytest.mark.asyncio
async def test_cookie_only_import_reuses_real_chrome_research_login(tmp_path):
    import sqlite3

    from playwright.async_api import async_playwright

    from halo_research_gateway.connections.chrome_import import ChromeImporter

    async def login(request):
        response = web.Response(text="Fixture research session established")
        response.set_cookie("research_session", "fixture-only", max_age=3600, httponly=True)
        return response

    async def source(request):
        authorized = request.cookies.get("research_session") == "fixture-only"
        state = "AUTHENTICATED_RESEARCH_EVIDENCE" if authorized else "LOGIN_REQUIRED"
        return web.Response(
            text=f"<!doctype html><html><head><title>Research session fixture</title></head><body><h1>{state}</h1><p>This disposable research fixture checks browser session continuity. The browser must carry its own existing session cookie before the server supplies the protected evidence marker. No personal account, browsing history, saved password, payment data or external service is used by this test.</p></body></html>",
            content_type="text/html",
        )

    app = web.Application()
    app.router.add_get("/research/login", login)
    app.router.add_get("/research/source", source)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    target = LocalTarget("cookie-fixture", "http", "127.0.0.1", port, ("/research",), browser_allowed=True)
    source_root = tmp_path / "dedicated-source"
    provider = Crawl4AIProvider(str(tmp_path / "gateway-browser"))
    try:
        async with async_playwright() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                str(source_root), channel="chrome", headless=True
            )
            try:
                page = await context.new_page()
                await page.goto(target.build_url("/research/login"))
                await page.goto(target.build_url("/research/source"))
                assert "AUTHENTICATED_RESEARCH_EVIDENCE" in await page.content()
            finally:
                await context.close()
        importer = ChromeImporter(tmp_path / "gateway-browser" / "profiles")
        preview = importer.preview(source_root / "Default", "research-copy", ["cookies"])
        assert any(record["relative"].endswith("Cookies") for record in preview["files"])
        importer.execute(preview)
        copied_login_data = tmp_path / "gateway-browser" / "profiles" / "research-copy" / "Profile" / "Login Data"
        assert not copied_login_data.exists()
        result = await provider.crawl(
            target.build_url("/research/source"),
            public=False,
            local_target=target,
            mode="managed_profile",
            profile="research-copy",
        )
        assert "AUTHENTICATED_RESEARCH_EVIDENCE" in result.items[0].content
        assert "fixture-only" not in repr(result.items)
        # Chrome creates an empty password database when opening the copy;
        # prove it contains no imported passwords, rather than banning that file.
        with sqlite3.connect(f"file:{copied_login_data.as_posix()}?mode=ro", uri=True) as db:
            assert db.execute("SELECT count(*) FROM logins").fetchone()[0] == 0
    finally:
        await provider.close()
        await runner.cleanup()
