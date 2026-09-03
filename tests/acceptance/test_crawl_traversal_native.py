"""Owned Chrome against disposable local sites; no personal profiles/accounts."""

import asyncio
from urllib.parse import urlsplit

import psutil
import pytest
from aiohttp import web

from halo_research_gateway.models import LocalTarget
from halo_research_gateway.providers.crawl4ai_provider import Crawl4AIProvider


@pytest.fixture
async def research_site():
    hits = []

    async def page(request):
        hits.append(request.path)
        name = request.match_info["name"]
        if name == "missing":
            return web.Response(status=404, text="NOT_RESEARCH_EVIDENCE")
        links = {
            "root": '<a href="child">Child source</a><a href="/outside">Excluded path</a>',
            "child": '<a href="grandchild">Grandchild source</a><a href="root#same">Root duplicate</a>',
            "grandchild": "",
        }.get(name, "")
        return web.Response(
            content_type="text/html",
            text=f"""<!doctype html><html><head><title>{name}</title></head>
<body style="min-height:4000px"><h1>{name.upper()}_RESEARCH_EVIDENCE</h1>
<p>This is a controlled source for verifying the research reader with useful independent page content and citation identity.</p>
{links}<div id="rendered"></div><script>
setTimeout(() => {{ document.querySelector('#rendered').innerHTML='<p id="ready">DYNAMIC_{name.upper()}_EVIDENCE</p>'; }}, 50);
addEventListener('scroll', () => {{ if (scrollY > 200 && !document.querySelector('#scrolled')) {{
const p=document.createElement('p'); p.id='scrolled'; p.textContent='SCROLLED_RESEARCH_EVIDENCE'; document.body.appendChild(p);
}} }});
</script></body></html>""",
        )

    async def outside(request):
        hits.append(request.path)
        return web.Response(text="OUTSIDE_TARGET_NOT_ALLOWED")

    app = web.Application()
    app.router.add_get("/research/{name}", page)
    app.router.add_get("/outside", outside)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    target = LocalTarget("fixture", "http", "127.0.0.1", port, ("/research",), browser_allowed=True)
    try:
        yield target, hits
    finally:
        await runner.cleanup()


async def test_native_dynamic_three_page_traversal_and_exact_local_scope(tmp_path, research_site):
    target, hits = research_site
    provider = Crawl4AIProvider(str(tmp_path / "browser"))
    try:
        result = await provider.crawl(
            target.build_url("/research/root"),
            max_pages=3,
            max_depth=2,
            public=False,
            local_target=target,
            wait_for="#ready",
        )
        assert [item.url for item in result.items] == [
            target.build_url("/research/" + name) for name in ("root", "child", "grandchild")
        ]
        assert [item.metadata["depth"] for item in result.items] == [0, 1, 2]
        assert all("DYNAMIC_" in item.content for item in result.items)
        assert hits.count("/research/root") == 1
        assert "/outside" not in hits
        assert "CRAWL_LINK_BLOCKED" in result.warnings
        assert provider._crawler is None
    finally:
        await provider.close()


async def test_native_scroll_and_page_limit_are_separate(tmp_path, research_site):
    target, hits = research_site
    provider = Crawl4AIProvider(str(tmp_path / "browser"))
    try:
        result = await provider.crawl(
            target.build_url("/research/root"),
            max_pages=1,
            max_depth=2,
            interaction="scroll",
            public=False,
            local_target=target,
            wait_for="#ready",
        )
        assert "SCROLLED_RESEARCH_EVIDENCE" in result.items[0].content
        assert len(result.items) == 1
        assert "/research/child" not in hits
        assert "CRAWL_PAGE_LIMIT_REACHED" in result.warnings
        assert provider._crawler is None
    finally:
        await provider.close()


async def test_native_cancel_closes_owned_browser_processes(tmp_path):
    entered, release = asyncio.Event(), asyncio.Event()

    async def slow(request):
        entered.set()
        await release.wait()
        return web.Response(text="late fixture response")

    app = web.Application()
    app.router.add_get("/research/slow", slow)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    target = LocalTarget("fixture", "http", "127.0.0.1", port, ("/research",), browser_allowed=True)
    provider = Crawl4AIProvider(str(tmp_path / "browser"))
    before = {process.pid for process in psutil.Process().children(recursive=True)}
    operation = asyncio.create_task(
        provider.crawl(target.build_url("/research/slow"), public=False, local_target=target)
    )
    try:
        await asyncio.wait_for(entered.wait(), 15)
        owned = [process for process in psutil.Process().children(recursive=True) if process.pid not in before]
        assert any("chrome" in process.name().lower() for process in owned)
        operation.cancel()
        with pytest.raises(asyncio.CancelledError):
            await asyncio.wait_for(operation, 15)
        assert provider._crawler is None
        assert not [process.pid for process in owned if process.is_running()], (
            "owned browser/driver process survived cancellation"
        )
    finally:
        release.set()
        operation.cancel()
        await asyncio.gather(operation, return_exceptions=True)
        await provider.close()
        await runner.cleanup()


@pytest.mark.parametrize("same_site", [True, False])
async def test_native_cross_host_redirect_is_blocked_before_request_when_scoped(tmp_path, same_site):
    hits = []

    async def redirect(request):
        raise web.HTTPFound(f"http://localhost:{port}/destination")

    async def destination(request):
        hits.append("destination")
        return web.Response(
            content_type="text/html",
            text="<h1>Redirect source evidence</h1><p>This controlled fixture supplies enough useful source text to test whether a cross-host navigation was permitted before the browser made its request.</p>",
        )

    app = web.Application()
    app.router.add_get("/redirect", redirect)
    app.router.add_get("/destination", destination)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    provider = Crawl4AIProvider(str(tmp_path / "browser"))

    async def fixture_network_only(url, public, target=None, method="GET"):
        # Only this disposable server substitutes for public DNS/IP validation.
        # Scope and actual Chrome request interception remain production code.
        parsed = urlsplit(url)
        if parsed.scheme in {"data", "blob", "about"}:
            return
        if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.port != port or method not in {"GET", "HEAD"}:
            raise ValueError("fixture destination denied")

    provider._validate_browser_request = fixture_network_only
    try:
        if same_site:
            with pytest.raises(RuntimeError, match="CRAWL_NO_EVIDENCE"):
                await provider.crawl(f"http://127.0.0.1:{port}/redirect", same_site_only=True)
            assert not hits, "cross-host redirect reached the server despite same_site_only"
        else:
            result = await provider.crawl(f"http://127.0.0.1:{port}/redirect", same_site_only=False)
            assert "Redirect source evidence" in result.items[0].content
            assert hits == ["destination"]
    finally:
        await provider.close()
        await runner.cleanup()


async def test_native_fetch_redirect_chain_cannot_escape_local_path(tmp_path):
    hits = []

    async def source(request):
        return web.Response(
            content_type="text/html",
            text="""<html><head><title>Redirect policy fixture</title></head><body>
<h1>Research response-stage redirect test</h1><p>This controlled page checks fetch redirects, including a later hop, before an excluded endpoint can receive any request.</p>
<p id="result"></p><script>fetch('/research/first').then(r=>r.text()).then(t=>document.querySelector('#result').textContent=t)
.catch(()=>document.querySelector('#result').textContent='REDIRECT_BLOCKED').finally(()=>document.querySelector('#result').id='ready');</script></body></html>""",
        )

    async def redirect(request):
        hits.append(request.path)
        raise web.HTTPFound("/research/second" if request.path.endswith("first") else "/outside")

    async def forbidden(request):
        hits.append(request.path)
        return web.Response(text="MUST_NOT_BE_REQUESTED")

    app = web.Application()
    app.router.add_get("/research/page", source)
    app.router.add_get("/research/first", redirect)
    app.router.add_get("/research/second", redirect)
    app.router.add_get("/outside", forbidden)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]
    target = LocalTarget("fixture", "http", "127.0.0.1", port, ("/research",), browser_allowed=True)
    provider = Crawl4AIProvider(str(tmp_path / "browser"))
    try:
        result = await provider.crawl(
            target.build_url("/research/page"), public=False, local_target=target, wait_for="#ready"
        )
        assert "REDIRECT_BLOCKED" in result.items[0].content
        assert hits == ["/research/first", "/research/second"]
    finally:
        await provider.close()
        await runner.cleanup()
