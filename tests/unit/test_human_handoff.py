"""Only the local operator may open a bounded research-login browser."""

import asyncio
import json
import re
import threading
from contextlib import asynccontextmanager

import httpx
import pytest
from test_crawl_options import application_at

from halo_research_gateway.providers.crawl4ai_provider import Crawl4AIProvider


@pytest.fixture
async def handoff_app(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    service = app.state.halo_service
    profile = tmp_path / "browser" / "profiles" / "research"
    profile.mkdir(parents=True)
    calls = []

    async def validate(*args):
        calls.append(("validate", args))

    monkeypatch.setattr(service.crawler, "_validate_browser_request", validate)
    try:
        yield app, calls
    finally:
        await service.close()


@asynccontextmanager
async def operator_client(app):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8765") as client:
        page = (await client.get("/operator")).text
        csrf = re.search(r'window.HALO_CSRF="([^"]+)"', page).group(1)
        client.headers["x-halo-csrf"] = csrf
        yield client


@pytest.mark.parametrize("headers", [{"x-halo-csrf": "wrong"}, {"origin": "https://untrusted.example"}])
async def test_handoff_requires_operator_csrf_and_origin(handoff_app, headers):
    app, calls = handoff_app
    async with operator_client(app) as client:
        response = await client.post(
            "/operator/api/research-session",
            headers=headers,
            json={"url": "https://example.org/read", "profile": "research"},
        )
        assert response.status_code == 403
        assert calls == []


@pytest.mark.parametrize(
    "values",
    [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ],
)
async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
    app, _ = handoff_app
    async with operator_client(app) as client:
        response = await client.post("/operator/api/research-session", json=values)
        assert response.status_code == 400


async def test_handoff_is_one_operator_session_with_no_secrets_in_state(handoff_app, monkeypatch):
    app, calls = handoff_app
    service = app.state.halo_service
    assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
    opened = asyncio.Event()

    async def browser(url, profile, done, ready):
        calls.append(("browser", url, profile))
        ready()
        opened.set()
        await done.wait()

    monkeypatch.setattr(service.crawler, "human_handoff", browser)
    async with operator_client(app) as client:
        response = await client.post(
            "/operator/api/research-session",
            json={
                "url": "https://example.org/private-path?token=fixture-secret",
                "profile": "research",
            },
        )
        assert response.status_code == 202
        await asyncio.wait_for(opened.wait(), 1)
        state = (await client.get("/operator/api/state")).json()["research_session"]
        assert state["state"] == "waiting_for_operator"
        assert service.health().get("research_session") == "waiting_for_operator"
        assert service.stats().get("research_session") == "waiting_for_operator"
        assert state["origin"] == "https://example.org"
        assert "fixture-secret" not in json.dumps(state)

        assert "private-path" not in json.dumps(state)
        duplicate = await client.post(
            "/operator/api/research-session",
            json={
                "url": "https://example.org/other",
                "profile": "research",
            },
        )
        assert duplicate.status_code == 409
        response = await client.post("/operator/api/research-session/done", json={"session_id": state["session_id"]})
        assert response.status_code == 200
        assert response.json()["state"] == "ready_to_retry"
        assert len([call for call in calls if call[0] == "browser"]) == 1
        assert len(await app.state.mcp_server.list_tools()) == 14


async def test_stale_done_cannot_complete_a_different_session(handoff_app, monkeypatch):
    app, _ = handoff_app
    service = app.state.halo_service
    assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"

    async def browser(url, profile, done, ready):
        ready()
        await done.wait()

    monkeypatch.setattr(service.crawler, "human_handoff", browser)
    async with operator_client(app) as client:
        await client.post("/operator/api/research-session", json={"url": "https://example.org", "profile": "research"})
        response = await client.post("/operator/api/research-session/done", json={"session_id": "stale"})
        assert response.status_code == 409
        state = (await client.get("/operator/api/state")).json()["research_session"]
        response = await client.post("/operator/api/research-session/cancel", json={"session_id": state["session_id"]})
        assert response.json()["state"] == "cancelled"


async def test_failed_browser_does_not_return_exception_secrets(handoff_app, monkeypatch):
    app, _ = handoff_app
    service = app.state.halo_service
    assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"

    async def browser(*args):
        raise RuntimeError("https://example.org?token=fixture-secret")

    monkeypatch.setattr(service.crawler, "human_handoff", browser)
    async with operator_client(app) as client:
        await client.post("/operator/api/research-session", json={"url": "https://example.org", "profile": "research"})
        await asyncio.sleep(0)
        state = (await client.get("/operator/api/state")).json()["research_session"]
        assert state["state"] == "failed"
        assert state["error"] == "RESEARCH_SESSION_FAILED"
        assert "fixture-secret" not in json.dumps(state)


@pytest.mark.parametrize("completion", ["done", "cancel", "timeout", "oversized"])
async def test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser(tmp_path, monkeypatch, completion):
    from playwright import async_api

    provider = Crawl4AIProvider(str(tmp_path))
    assert callable(getattr(provider, "human_handoff", None)), "missing browser handoff implementation"
    (tmp_path / "profiles" / "research").mkdir(parents=True)
    events = []
    ready = asyncio.Event()
    done = asyncio.Event()
    seed = [{"name": "session", "value": "old-fixture", "domain": "example.org", "path": "/"}]
    updated = [{**seed[0], "value": "new-fixture"}]
    if completion == "oversized":
        updated = [{**seed[0], "value": "x" * 2_097_153}]

    class Context:
        pages = []

        async def route(self, *args):
            pass

        async def cookies(self):
            return seed

        async def close(self):
            events.append("seed_closed")

    class Page:
        async def goto(self, url, **kwargs):
            events.append(("goto", url))

        def on(self, *args):
            pass

    class Session(Context):
        async def add_cookies(self, cookies):
            assert cookies == seed
            events.append("seeded")

        async def new_page(self):
            return Page()

        async def cookies(self):
            return updated

        def on(self, *args):
            pass

    class Browser:
        async def new_context(self, **kwargs):
            assert kwargs["accept_downloads"] is False
            assert kwargs["service_workers"] == "block"
            return Session()

        async def close(self):
            events.append("browser_closed")

    class Driver:
        chromium = None

        def __init__(self):
            self.chromium = self

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            events.append("driver_closed")

        async def launch_persistent_context(self, *args, **kwargs):
            assert kwargs["headless"] is True
            return Context()

        async def launch(self, **kwargs):
            assert kwargs["headless"] is False
            assert kwargs["channel"] == "chrome"
            return Browser()

    async def guard(*args, **kwargs):
        events.append("guarded")

    async def validate(*args):
        events.append("validated")

    monkeypatch.setattr(async_api, "async_playwright", Driver)
    monkeypatch.setattr(provider, "_guard_page", guard)
    monkeypatch.setattr(provider, "_validate_browser_request", validate)
    if completion == "timeout":
        provider.limits.job_timeout_seconds = 0.05
    task = asyncio.create_task(provider.human_handoff("https://example.org/read", "research", done, ready.set))
    await asyncio.wait_for(ready.wait(), 1)
    if completion == "cancel":
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    elif completion == "timeout":
        with pytest.raises(TimeoutError):
            await task
    else:
        done.set()
        if completion == "oversized":
            with pytest.raises(ValueError, match="RESEARCH_SESSION_TOO_LARGE"):
                await task
        else:
            await task
    assert "browser_closed" in events
    assert events.index("guarded") < events.index(("goto", "https://example.org/read"))
    assert await provider._profile_cookies("research") == (updated if completion == "done" else seed)
    await provider.close()
    assert await provider._profile_cookies("research") == seed


async def test_cookie_import_clears_temporary_session_only_for_replaced_profile(handoff_app, monkeypatch):
    app, _ = handoff_app
    service = app.state.halo_service
    provider = service.crawler
    provider._human_cookies = ("research", [{"name": "old", "value": "fixture-only"}])

    async def execute(plan_id, token, key, executor):
        return await executor({"action": "chrome_import", "import": {"destination_name": plan_id}})

    def import_profile(plan):
        assert provider._lock.locked(), "profile import raced a live research browser"
        return {"status": "imported"}

    monkeypatch.setattr(service.import_reviews, "execute", execute)
    monkeypatch.setattr(service.chrome_importer, "execute", import_profile)
    await service.chrome_import_execute("other", "fixture", "fixture")
    assert provider._human_cookies is not None
    await service.chrome_import_execute("research", "fixture", "fixture")
    assert provider._human_cookies is None


async def test_cancelled_import_keeps_profile_lock_until_copy_settles(handoff_app, monkeypatch):
    app, _ = handoff_app
    service = app.state.halo_service
    entered = asyncio.Event()
    release = threading.Event()
    loop = asyncio.get_running_loop()

    def import_profile(plan):
        loop.call_soon_threadsafe(entered.set)
        assert release.wait(5)
        return {"status": "imported"}

    async def execute(plan_id, token, key, executor):
        return await executor({"action": "chrome_import", "import": {"destination_name": "research"}})

    monkeypatch.setattr(service.import_reviews, "execute", execute)
    monkeypatch.setattr(service.chrome_importer, "execute", import_profile)
    task = asyncio.create_task(service.chrome_import_execute("research", "fixture", "fixture"))
    try:
        await asyncio.wait_for(entered.wait(), 2)
        task.cancel()
        await asyncio.sleep(0.02)
        assert service.crawler._lock.locked(), "cancel released ownership while the profile copy was still running"
    finally:
        release.set()
        await asyncio.gather(task, return_exceptions=True)
    assert not service.crawler._lock.locked()
