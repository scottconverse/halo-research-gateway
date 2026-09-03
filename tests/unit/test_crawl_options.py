"""Crawl controls must affect real collection, not just tool signatures."""

import asyncio
from types import SimpleNamespace

import pytest
from mcp.server.mcpserver import Context

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig, LocalTargetConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.security import validate_url

URL = "https://example.org/start"


def application_at(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    config.crawl.base_directory = str(tmp_path / "browser")
    config.http.per_origin_interval_seconds = 0
    config.local_targets["fixture"] = LocalTargetConfig(
        scheme="http", host="127.0.0.1", port=3090, path_prefixes=["/research"], browser_allowed=True
    )
    return create_application(config)


async def call(app, tool="web_crawl", **options):
    context = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={})), mcp_server=app.state.mcp_server
    )
    return await app.state.mcp_server._tool_manager.call_tool(tool, options, context)


async def test_web_crawl_forwards_all_content_controls_and_separates_cache(tmp_path):
    app = application_at(tmp_path)
    calls = []

    async def crawl(url, **options):
        calls.append(options)
        return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="text")])

    app.state.halo_service.crawler.crawl = crawl
    try:
        for depth, same_site in [(0, True), (1, True), (1, False)]:
            result = await call(app, url=URL, max_pages=3, max_depth=depth, same_site_only=same_site)
            assert result["ok"], result
        assert len(calls) == 3, "different depth/site options reused an incompatible cache result"
        assert [(options.get("max_depth"), options.get("same_site_only")) for options in calls] == [
            (0, True),
            (1, True),
            (1, False),
        ]
        assert all(options.get("interaction") == "none" and options.get("capture") == "none" for options in calls)
    finally:
        await app.state.halo_service.close()


async def test_local_mcp_forwards_depth_and_interaction(tmp_path):
    app = application_at(tmp_path)
    seen = []

    async def crawl(*args, **kwargs):
        seen.append(kwargs)
        return {"ok": True}

    app.state.halo_service.local_crawl = crawl
    try:
        await call(app, "local_crawl", target="fixture", path="/research/start", max_depth=2, interaction="scroll")
        assert seen[0].get("max_depth") == 2
        assert seen[0].get("interaction") == "scroll"
    finally:
        await app.state.halo_service.close()


class BrowserFixture:
    def __init__(self, pages):
        self.pages = pages
        self.calls = []
        self.closed = 0

    async def arun(self, url, config):
        self.calls.append((url, config))
        text, links = self.pages[url]
        return SimpleNamespace(
            success=True,
            markdown=SimpleNamespace(raw_markdown=text),
            url=url,
            metadata={"title": text},
            status_code=200,
            links={"internal": [{"href": link} for link in links], "external": []},
        )

    async def close(self):
        self.closed += 1


def install_browser(app, monkeypatch, pages):
    __import__("crawl4ai")  # Load SDK before any deliberately short fixture deadlines.
    provider = app.state.halo_service.crawler
    browser = BrowserFixture(pages)

    async def start(*args, **kwargs):
        provider._crawler = browser

    async def validate(*args, **kwargs):
        return None

    monkeypatch.setattr(provider, "start", start)
    monkeypatch.setattr(provider, "_validate_browser_request", validate)
    return browser


async def test_mcp_crawl_visits_linked_pages_to_requested_depth(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(
        app,
        monkeypatch,
        {
            URL: ("Root evidence", ["/child", URL + "#duplicate"]),
            "https://example.org/child": ("Child evidence", ["/grandchild"]),
            "https://example.org/grandchild": ("Grandchild evidence", [URL]),
        },
    )
    try:
        result = await call(app, url=URL, max_pages=3, max_depth=2, mode="standard")
        assert result["ok"], result
        assert [item["content"] for item in result["items"]] == [
            "Root evidence",
            "Child evidence",
            "Grandchild evidence",
        ]
        assert [item["metadata"]["depth"] for item in result["items"]] == [0, 1, 2]
        assert len(browser.calls) == 3
        assert browser.closed == 1, "crawl retained its browser after collection ended"
    finally:
        await app.state.halo_service.close()


@pytest.mark.parametrize("options", [{"max_pages": 0}, {"max_pages": 26}, {"max_depth": -1}, {"max_depth": 4}])
async def test_crawl_rejects_out_of_contract_limits_before_browser(tmp_path, monkeypatch, options):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
    try:
        result = await call(app, url=URL, **options)
        assert not result["ok"], "invalid crawl limits were silently accepted"
        assert not browser.calls
    finally:
        await app.state.halo_service.close()


async def test_page_failure_retains_other_citable_pages(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(
        app,
        monkeypatch,
        {
            URL: ("Root evidence", ["/missing", "/good"]),
            "https://example.org/good": ("Good evidence", []),
        },
    )
    try:
        result = await call(app, url=URL, max_pages=3, max_depth=1)
        assert result["ok"], result
        assert [item["content"] for item in result["items"]] == ["Root evidence", "Good evidence"]
        assert "CRAWL_PAGE_FAILED" in result["warnings"]
        assert len(browser.calls) == 3
    finally:
        await app.state.halo_service.close()


async def test_failed_all_pages_is_not_empty_success(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    install_browser(app, monkeypatch, {})
    try:
        result = await call(app, url=URL)
        assert not result["ok"]
        assert result["error"]["code"] == "CRAWL_NO_EVIDENCE"
    finally:
        await app.state.halo_service.close()


@pytest.mark.parametrize("same_site,expected", [(True, 1), (False, 2)])
async def test_cross_site_traversal_is_controlled(tmp_path, monkeypatch, same_site, expected):
    app = application_at(tmp_path)
    install_browser(
        app,
        monkeypatch,
        {
            URL: ("Root evidence", ["https://other.example/source"]),
            "https://other.example/source": ("Other evidence", []),
        },
    )
    try:
        result = await call(app, url=URL, max_pages=3, max_depth=1, same_site_only=same_site)
        assert result["ok"], result
        assert len(result["items"]) == expected
    finally:
        await app.state.halo_service.close()


async def test_filtered_local_link_does_not_abort_valid_research(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    install_browser(
        app,
        monkeypatch,
        {URL: ("Root evidence", ["/private", "/valid"]), "https://example.org/valid": ("Valid evidence", [])},
    )

    async def validate(url, *args):
        if url.endswith("/private"):
            raise ValueError("fixture forbidden target")

    monkeypatch.setattr(app.state.halo_service.crawler, "_validate_browser_request", validate)
    try:
        result = await call(app, url=URL, max_pages=3, max_depth=1)
        assert result["ok"], result
        assert [item["content"] for item in result["items"]] == ["Root evidence", "Valid evidence"]
        assert "CRAWL_LINK_BLOCKED" in result["warnings"]
    finally:
        await app.state.halo_service.close()


async def test_operator_page_ceiling_is_enforced_before_browser(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    app.state.halo_service.config.crawl.max_pages = 2
    browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
    try:
        result = await call(app, url=URL, max_pages=3, max_depth=1)
        assert not result["ok"]
        assert result["error"]["code"] == "CRAWL_LIMIT_INVALID"
        assert not browser.calls
    finally:
        await app.state.halo_service.close()


async def test_crawl_content_and_frontier_are_bounded_before_cache(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {URL: ("text " * 100_000, [f"/p{n}" for n in range(10_000)])})
    try:
        result = await app.state.halo_service.crawler.crawl(URL, max_pages=1, max_depth=1)
        assert len(result.items[0].content) <= 50_000
        assert "CRAWL_CONTENT_TRUNCATED" in result.warnings
        assert "CRAWL_LINK_LIMIT_REACHED" in result.warnings
        assert len(browser.calls) == 1
    finally:
        await app.state.halo_service.close()


async def test_managed_profile_result_is_not_persisted_by_public_crawl(tmp_path):
    app = application_at(tmp_path)
    seen = []

    async def crawl(url, **kwargs):
        seen.append(url)
        return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="text")])

    app.state.halo_service.crawler.crawl = crawl
    try:
        for _ in range(2):
            result = await call(app, url=URL, mode="managed_profile", profile="research-copy")
            assert result["ok"], result
        assert len(seen) == 2, "authenticated crawl was reused from disk cache without explicit permission"
    finally:
        await app.state.halo_service.close()


async def test_repeated_cancellation_cannot_abandon_owned_browser_cleanup(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {})
    entered, closing, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def wait_page(**kwargs):
        entered.set()
        await asyncio.Event().wait()

    async def slow_close():
        closing.set()
        await release.wait()
        browser.closed += 1

    browser.arun, browser.close = wait_page, slow_close
    operation = asyncio.create_task(app.state.halo_service.crawler.crawl(URL))
    try:
        await asyncio.wait_for(entered.wait(), 5)
        operation.cancel()
        await asyncio.wait_for(closing.wait(), 5)
        operation.cancel()
        await asyncio.sleep(0)
        release.set()
        with pytest.raises(asyncio.CancelledError):
            await operation
        assert browser.closed == 1, "second cancellation abandoned owned browser cleanup"
        assert app.state.halo_service.crawler._crawler is None
    finally:
        release.set()
        operation.cancel()
        await asyncio.gather(operation, return_exceptions=True)
        await app.state.halo_service.close()


@pytest.mark.parametrize("option", ["interaction", "capture", "mode"])
async def test_unimplemented_option_is_explicit_not_silent_success(tmp_path, monkeypatch, option):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
    value = {"interaction": "site_search", "capture": "pdf", "mode": "undetected"}[option]
    try:
        result = await call(app, url=URL, **{option: value})
        assert not result["ok"], f"{option} was silently ignored"
        assert result["error"]["code"] == f"CRAWL_{option.upper()}_UNAVAILABLE"
        assert not browser.calls
    finally:
        await app.state.halo_service.close()


async def test_scroll_is_explicit_and_bounded_not_implied_by_page_count(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
    try:
        result = await call(app, url=URL, interaction="scroll")
        assert result["ok"], result
        config = browser.calls[0][1]
        assert config.scan_full_page is True
        assert config.max_scroll_steps == 5
        assert config.verbose is False
        assert result["items"][0]["metadata"]["mode"] == "standard"
    finally:
        await app.state.halo_service.close()


async def test_whole_crawl_deadline_preserves_completed_evidence_and_closes(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {URL: ("Root evidence", ["/slow"])})
    app.state.halo_service.crawler.limits = SimpleNamespace(
        max_pages=25, max_depth=3, page_timeout_seconds=45, job_timeout_seconds=0.05, enabled=True
    )
    original = browser.arun

    async def slow_page(url, config):
        if url.endswith("/slow"):
            await asyncio.sleep(0.2)
        return await original(url, config)

    browser.arun = slow_page
    try:
        result = await call(app, url=URL, max_pages=2, max_depth=1)
        assert result["ok"], result
        assert "CRAWL_TIMEOUT" in result["warnings"]
        assert result["items"][0]["content"] == "Root evidence"
        assert result["items"][0]["metadata"].get("attempted_pages") == 2
        assert browser.closed == 1
    finally:
        await app.state.halo_service.close()


async def test_empty_render_is_not_research_evidence(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    install_browser(app, monkeypatch, {URL: ("   ", [])})
    try:
        result = await call(app, url=URL)
        assert not result["ok"]
        assert result["error"]["code"] == "CRAWL_NO_EVIDENCE"
    finally:
        await app.state.halo_service.close()


async def test_signed_browser_result_url_is_redacted_and_not_cached(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {URL: ("Public fixture evidence", [])})
    original = browser.arun

    async def redirected(url, config):
        result = await original(url, config)
        result.url = URL + "?token=fixture-secret"
        return result

    browser.arun = redirected
    try:
        for _ in range(2):
            result = await call(app, url=URL)
            assert result["ok"], result
            assert "fixture-secret" not in result["items"][0]["url"]
            assert "SENSITIVE_URL_NOT_CACHED" in result["warnings"]
        assert len(browser.calls) == 2
    finally:
        await app.state.halo_service.close()


async def test_browser_sdk_does_not_log_research_urls_by_default(tmp_path, monkeypatch):
    import crawl4ai

    app = application_at(tmp_path)
    configs = []
    browser = BrowserFixture({})
    browser.crawler_strategy = SimpleNamespace(set_hook=lambda *args: None)

    async def start():
        return None

    def construct(**options):
        configs.append(options["config"])
        return browser

    browser.start = start
    monkeypatch.setattr(crawl4ai, "AsyncWebCrawler", construct)
    try:
        await app.state.halo_service.crawler.start()
        assert configs[0].verbose is False
    finally:
        await app.state.halo_service.close()


@pytest.mark.parametrize(
    "options,code",
    [
        ({"mode": "managed_profile"}, "BROWSER_PROFILE_REQUIRED"),
        ({"profile": "research-copy"}, "BROWSER_PROFILE_REQUIRES_MANAGED_MODE"),
        ({"wait_for": "js:() => true"}, "CRAWL_SELECTOR_INVALID"),
        ({"wait_for": "#" + "x" * 1024}, "CRAWL_SELECTOR_INVALID"),
    ],
)
async def test_profile_and_selector_options_cannot_be_silently_misinterpreted(tmp_path, monkeypatch, options, code):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
    try:
        result = await call(app, url=URL, **options)
        assert not result["ok"], result
        assert result["error"]["code"] == code
        assert not browser.calls
    finally:
        await app.state.halo_service.close()


async def test_browser_http_error_response_is_not_source_success(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(app, monkeypatch, {URL: ("Error page body", [])})
    original = browser.arun

    async def unavailable(url, config):
        result = await original(url, config)
        result.status_code = 503
        return result

    browser.arun = unavailable
    try:
        result = await call(app, url=URL)
        assert not result["ok"]
        assert result["error"]["code"] == "CRAWL_NO_EVIDENCE"
    finally:
        await app.state.halo_service.close()


async def test_redirected_browser_url_is_the_citation_and_child_base(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    browser = install_browser(
        app, monkeypatch, {URL: ("Root evidence", ["child"]), "https://example.org/docs/child": ("Child evidence", [])}
    )
    original = browser.arun

    async def redirect(url, config):
        result = await original(url, config)
        if url == URL:
            result.redirected_url = "https://example.org/docs/index"
        return result

    browser.arun = redirect
    try:
        result = await call(app, url=URL, max_pages=2, max_depth=1)
        assert result["ok"], result
        assert result["items"][0]["url"] == "https://example.org/docs/index"
        assert result["items"][1]["url"] == "https://example.org/docs/child"
    finally:
        await app.state.halo_service.close()


async def test_public_crawl_shares_the_direct_http_origin_slot(tmp_path, monkeypatch):
    app = application_at(tmp_path)
    service = app.state.halo_service
    browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
    entered = asyncio.Event()
    original = service.crawler.start

    async def start(*args, **kwargs):
        await original(*args, **kwargs)
        entered.set()

    monkeypatch.setattr(service.crawler, "start", start)
    operation = None
    try:
        async with service.http._origin_gate(validate_url(URL)):
            operation = asyncio.create_task(service.web_crawl(URL))
            await asyncio.wait_for(entered.wait(), 5)
            assert not browser.calls, "browser navigation bypassed the direct HTTP origin slot"
        result = await asyncio.wait_for(operation, 5)
        assert result["ok"], result
        assert len(browser.calls) == 1
    finally:
        if operation is not None:
            operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)
        await service.close()
