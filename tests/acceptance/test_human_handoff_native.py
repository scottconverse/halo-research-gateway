"""Real owned Chrome; an intercepted public-shaped site, no real account.

The test clicks a synthetic challenge button, not a live CAPTCHA. Network requests
to the fixture host are fulfilled in-process; DNS answers are fixture-injected.
The production public/local guards remain installed for all other destinations.
"""

import asyncio
import json
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import psutil

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.operator_ui import render_operator
from halo_research_gateway.providers import crawl4ai_provider

URL = "https://research.example/read"
TEXT = "CONTROLLED_RESEARCH_EVIDENCE: This source became readable after the synthetic human step."


def application_at(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    config.crawl.base_directory = str(tmp_path / "browser")
    config.http.per_origin_interval_seconds = 0
    return create_application(config)


@asynccontextmanager
async def operator_client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8765") as client:
        page = (await client.get("/operator")).text
        client.headers["x-halo-csrf"] = re.search(r'window.HALO_CSRF="([^"]+)"', page).group(1)
        yield client


async def test_visible_fixture_handoff_then_managed_read_and_cleanup(tmp_path, monkeypatch):
    before = {p.pid for p in psutil.Process().children(recursive=True)}
    app = application_at(tmp_path)
    service = app.state.halo_service
    provider = service.crawler
    (tmp_path / "browser" / "profiles" / "research").mkdir(parents=True)
    original_guard = provider._guard_page
    original_resolve = crawl4ai_provider.resolve_public
    opened = asyncio.Event()
    handoff_page = []
    calls = []

    async def resolve(target):
        if target.host == "research.example":
            return "93.184.216.34"
        return await original_resolve(target)

    async def guard(page, context, *args, **kwargs):
        await original_guard(page, context, *args, **kwargs)

        async def fixture(route, request):
            if urlsplit(request.url).hostname != "research.example":
                await route.fallback()
                return
            await provider._validate_browser_request(request.url, True, None, request.method)
            cookies = await context.cookies(URL)
            authenticated = any(c["name"] == "halo_fixture" and c["value"] == "solved" for c in cookies)
            calls.append({"method": request.method, "authenticated": authenticated})
            body = (
                f"<title>Research source</title><p>{TEXT}</p>"
                if authenticated
                else """<title>Verify you are human</title>
<div class="cf-turnstile"></div><button id="fixture-human" onclick="document.cookie='halo_fixture=solved; Secure; SameSite=Lax; path=/';location.reload()">Complete synthetic human step</button>"""
            )
            await route.fulfill(status=200, content_type="text/html", body=body)

        await context.route("**/*", fixture)
        if kwargs.get("single_page"):
            handoff_page.append(page)
            opened.set()

    monkeypatch.setattr(crawl4ai_provider, "resolve_public", resolve)
    monkeypatch.setattr(provider, "_guard_page", guard)
    try:
        async with operator_client(app) as client:
            started = await client.post("/operator/api/research-session", json={"url": URL, "profile": "research"})
            assert started.status_code == 202, started.text
            session_id = started.json()["session_id"]
            await asyncio.wait_for(opened.wait(), 40)
            page = handoff_page[0]
            await page.locator("#fixture-human").wait_for(timeout=20_000)
            # This is fixture-driven UI automation, not evidence of a real human/live challenge.
            await page.locator("#fixture-human").click()
            await page.get_by_text(TEXT).wait_for(timeout=20_000)
            finished = await client.post("/operator/api/research-session/done", json={"session_id": session_id})
            assert finished.json()["state"] == "ready_to_retry", finished.text
            assert page.is_closed()
            result = await service.web_crawl(URL, mode="managed_profile", profile="research")
            assert result["ok"], result
            assert TEXT in json.dumps(result)
            assert result["items"][0]["url"] == URL
            assert "solved" not in json.dumps(result)
            assert not await provider._profile_cookies("research") == []
            assert all(call["method"] == "GET" for call in calls)
            assert any(not call["authenticated"] for call in calls)
            assert any(call["authenticated"] for call in calls)
        await service.close()
        # Updated cookie never entered the imported profile; shutdown clears memory.
        assert await provider._profile_cookies("research") == []
    finally:
        await service.close()
    remaining = [p for p in psutil.Process().children(recursive=True) if p.pid not in before]
    _, alive = await asyncio.to_thread(psutil.wait_procs, remaining, timeout=15)
    assert alive == [], "owned browser descendants survived cleanup"


async def test_operator_handoff_states_and_small_viewport(tmp_path):
    from playwright.async_api import async_playwright

    app = application_at(tmp_path)
    service = app.state.halo_service
    state = {
        "health": service.health(),
        "connections": [],
        "imports": [],
        "receipts": [],
        "jobs": [],
        "stats": service.stats(),
        "research_session": {"state": "idle"},
    }
    errors = []
    evidence = Path(os.environ.get("HALO_UI_EVIDENCE_DIR", str(tmp_path)))
    await asyncio.to_thread(evidence.mkdir, parents=True, exist_ok=True)
    try:
        async with async_playwright() as driver:
            browser = await driver.chromium.launch(channel="chrome", headless=True)
            try:
                page = await browser.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))

                async def fixture(route):
                    if route.request.url.endswith("/operator"):
                        await route.fulfill(
                            content_type="text/html", body=render_operator("fixture-csrf", service.health())
                        )
                    else:
                        await route.fulfill(content_type="application/json", body=json.dumps(state))

                await page.route("http://127.0.0.1:8765/**", fixture)
                await page.goto("http://127.0.0.1:8765/operator")
                await page.locator("#researchMessage").get_by_text("No handoff is active.").wait_for()
                for status in (
                    "opening",
                    "waiting_for_operator",
                    "ready_to_retry",
                    "cancelled",
                    "timed_out",
                    "failed",
                    "idle",
                ):
                    await page.evaluate(
                        "s => showResearch(s)", {"state": status, "profile": "research", "session_id": "fixture"}
                    )
                    assert await page.locator("#researchDone").is_enabled() == (status == "waiting_for_operator")
                    assert await page.locator("#researchCancel").is_enabled() == (
                        status in {"opening", "waiting_for_operator"}
                    )
                    assert await page.locator("#researchMessage").inner_text()
                for name, width in [("desktop", 1280), ("mobile", 390)]:
                    await page.set_viewport_size({"width": width, "height": 900})
                    await page.screenshot(path=str(evidence / f"human-handoff-{name}.png"), full_page=True)
                    assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth"), name
                assert errors == [], errors
            finally:
                await browser.close()
    finally:
        await service.close()
