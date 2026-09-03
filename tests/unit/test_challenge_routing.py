"""Crawl challenge fallback must return source evidence, never a gate page."""

import asyncio
from types import SimpleNamespace

import pytest
from mcp.server.mcpserver import Context

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig, OptionalProviderConfig
from halo_research_gateway.providers.paid import BrightDataUnlockerAdapter

URL = "https://example.org/research"
CHALLENGE = (
    '<title>Just a moment...</title><script src="/cdn-cgi/challenge-platform/x.js"></script><p>Verify you are human</p>'
)
SOURCE = "<title>Research source</title><h1>Independent source evidence</h1><p>Collected research facts.</p>"


@pytest.fixture
async def setup(tmp_path, monkeypatch):
    import crawl4ai  # noqa: F401

    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    config.crawl.base_directory = str(tmp_path / "browser")
    config.http.per_origin_interval_seconds = 0
    app = create_application(config)
    service = app.state.halo_service
    connection = service.connections.create(
        "brightdata", "fixture", "api_key", {"api_key": "fixture-key", "zone": "fixture"}
    )
    policy = OptionalProviderConfig(
        enabled=True,
        provider="brightdata",
        connection_id=connection["connection_id"],
        allowed_domains=["example.org"],
        daily_attempt_limit=2,
        daily_spend_limit_usd=0.04,
    )
    service.optional_providers.configs["proxy"] = policy.model_copy(update={"request_cost_usd": 0.02})
    state = SimpleNamespace(html=CHALLENGE, status=200, api_body=SOURCE, api_status=200, calls=[], closed=0, links=[])

    async def request(method, path, headers, body):
        state.calls.append((method, path, headers, body))
        return {"status_code": state.api_status, "body": state.api_body, "headers": {"content-type": "text/html"}}

    service.optional_providers.register("proxy", "brightdata", BrightDataUnlockerAdapter(request))

    async def arun(url, config):
        return SimpleNamespace(
            success=True,
            html=state.html,
            markdown=SimpleNamespace(raw_markdown=state.html),
            metadata={"title": "Just a moment..." if state.html == CHALLENGE else "Research"},
            response_headers={},
            status_code=state.status,
            url=url,
            links={"internal": [{"href": link} for link in state.links], "external": []},
        )

    async def close():
        state.closed += 1

    async def start(*args, **kwargs):
        service.crawler._crawler = SimpleNamespace(arun=arun, close=close)

    async def validate(*args, **kwargs):
        return None

    monkeypatch.setattr(service.crawler, "start", start)
    monkeypatch.setattr(service.crawler, "_validate_browser_request", validate)
    try:
        yield app, service, state
    finally:
        await service.close()


async def call(app, **options):
    context = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={})), mcp_server=app.state.mcp_server
    )
    return await app.state.mcp_server._tool_manager.call_tool(
        "web_crawl", dict(url=URL, max_chars=6000, **options), context
    )


async def test_auto_crawl_uses_configured_proxy_and_returns_citable_source(setup):
    app, service, state = setup
    result = await call(app)
    assert len(state.calls) == 1, "Configured proxy is never invoked by the actual MCP crawl"
    assert result["ok"], result
    assert "Independent source evidence" in result["items"][0]["content"]
    assert "Verify you are human" not in str(result)
    assert result["items"][0]["url"] == URL
    assert result["items"][0]["metadata"]["retrieval_provider"] == "brightdata"
    assert result["items"][0]["metadata"]["mode"] == "proxy", "Actual fallback mode is mislabeled standard"
    assert result["items"][0]["metadata"]["final_url_verified"] is False
    assert "PROXY_FINAL_URL_UNVERIFIED" in result["warnings"]
    assert "fixture-key" not in str(result)
    assert state.calls[0][3]["format"] == "json"
    assert service.optional_providers.status()["proxy"]["spend_usd_today"] == 0.02
    assert state.closed == 1


@pytest.mark.parametrize("status", [200, 403, 429, 503])
async def test_disabled_proxy_returns_explicit_challenge_not_fake_evidence(setup, status):
    app, service, state = setup
    state.status = status
    service.optional_providers.configs["proxy"].enabled = False
    result = await call(app)
    assert not result["ok"], "Challenge page was called useful research"
    assert result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
    assert not state.calls


@pytest.mark.parametrize(
    "options", [{"mode": "standard"}, {"mode": "managed_profile", "profile": "research"}, {"interaction": "scroll"}]
)
async def test_challenge_does_not_silently_export_session_or_ignore_explicit_controls(setup, options):
    app, service, state = setup
    result = await call(app, **options)
    assert not result["ok"] and result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
    assert not state.calls


async def test_proxy_domain_denial_is_visible_and_never_sent(setup):
    app, service, state = setup
    service.optional_providers.configs["proxy"].allowed_domains = ["other.example"]
    result = await call(app)
    assert not result["ok"] and result["error"]["code"] == "OPTIONAL_PROVIDER_DOMAIN_NOT_ALLOWED"
    assert not state.calls


@pytest.mark.parametrize(
    "status,body,code",
    [
        (200, CHALLENGE, "CRAWL_CHALLENGE_REQUIRED"),
        (403, SOURCE, "PROXY_SOURCE_HTTP_ERROR"),
        (200, "", "PROXY_EMPTY_EVIDENCE"),
        (302, SOURCE, "PROXY_SOURCE_HTTP_ERROR"),
    ],
)
async def test_unsolved_or_bad_proxy_result_is_not_success(setup, status, body, code):
    app, service, state = setup
    state.api_status, state.api_body = status, body
    result = await call(app)
    assert not result["ok"] and result["error"]["code"] == code
    assert len(state.calls) == 1


async def test_normal_article_about_challenges_is_not_misclassified(setup):
    app, service, state = setup
    state.html = "<title>How CAPTCHA works</title><article>Verify you are human is text used by Cloudflare. Research discussion.</article>"
    result = await call(app)
    assert result["ok"] and "Research discussion" in result["items"][0]["content"]
    assert not state.calls


async def test_unrelated_http_failure_never_spends_proxy_budget(setup):
    app, service, state = setup
    state.html, state.status = "Internal server error", 500
    result = await call(app)
    assert not result["ok"] and not state.calls


async def test_proxy_cancellation_closes_browser_and_retains_reserved_attempt(setup):
    app, service, state = setup
    entered = asyncio.Event()

    async def stalled(**values):
        entered.set()
        await asyncio.Event().wait()

    service.optional_providers.register("proxy", "brightdata", stalled)
    task = asyncio.create_task(call(app))
    try:
        for _ in range(100):
            if entered.is_set() or task.done():
                break
            await asyncio.sleep(0.01)
        assert entered.is_set(), "Crawl never reached configured proxy"
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert service.optional_providers.status()["proxy"]["attempts_today"] == 1
        assert state.closed == 1
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def test_partial_proxy_crawl_retains_sources_when_shared_budget_runs_out(setup):
    app, service, state = setup
    state.api_body = SOURCE + '<a href="https://example.org/child">child</a><a href="https://example.org/last">last</a>'
    result = await call(app, max_pages=3, max_depth=1)
    assert result["ok"] and len(state.calls) == 2
    assert {row["url"] for row in result["items"]} == {URL, "https://example.org/child"}
    assert "OPTIONAL_PROVIDER_ATTEMPT_BUDGET_EXHAUSTED" in result["warnings"]
    assert "Verify you are human" not in str(result)


async def test_proxy_relative_links_are_not_resolved_against_an_unverified_final_url(setup):
    app, service, state = setup
    state.api_body = SOURCE + '<a href="child">relative</a>'
    result = await call(app, max_pages=2, max_depth=1)
    assert result["ok"] and len(state.calls) == 1
    assert "PROXY_RELATIVE_LINKS_SKIPPED" in result["warnings"]


async def test_unknown_provider_response_has_explicit_non_secret_error(setup):
    app, service, state = setup
    service.optional_providers.register("proxy", "brightdata", lambda **values: "unexpected fixture-key")
    result = await call(app)
    assert not result["ok"] and result["error"]["code"] == "PROXY_RESPONSE_INVALID"
    assert "fixture-key" not in str(result)


async def test_unmatched_proxy_selector_never_silently_succeeds(setup):
    app, service, state = setup
    result = await call(app, wait_for="#missing")
    assert not result["ok"] and result["error"]["code"] == "PROXY_SELECTOR_NOT_FOUND"


async def test_recognized_sensitive_query_never_sent_to_proxy(setup):
    app, service, state = setup
    result = await service.web_crawl(URL + "?token=private-fixture")
    assert not result["ok"] and result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
    assert not state.calls


async def test_legacy_cached_challenge_is_not_served_by_forum_reader(setup):
    import hashlib
    import json

    from halo_research_gateway.models import EvidenceItem, ProviderResult

    app, service, state = setup
    key = (
        "community-thread:"
        + hashlib.sha256(json.dumps([URL, 40, "source_default"], sort_keys=True).encode()).hexdigest()
    )
    bad = ProviderResult(
        "community-forum-crawl", [EvidenceItem(url=URL, retrieved_at="2026-09-03T00:00:00Z", content=CHALLENGE)]
    )
    service.cache.put(key, service._encode_result(bad), 3600)
    result = await service.community_thread(URL)
    assert not result["ok"] and result["error"]["code"] == "CRAWL_CHALLENGE_REQUIRED"
