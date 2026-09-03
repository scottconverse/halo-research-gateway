"""Actual crawl dispatch with a fake page/vendor; real JavaScript is tested natively."""

import asyncio
from types import SimpleNamespace

import pytest

from halo_research_gateway.config import CrawlConfig
from halo_research_gateway.providers.crawl4ai_provider import Crawl4AIProvider

URL = "https://example.org/research"
TOKEN = "fixture-solver-token-private"
GATE = '<title>Verify you are human</title><div class="cf-turnstile" data-sitekey="fixture-sitekey" data-callback="solved"></div>'
SOURCE = "<title>Research</title><article>Independent research evidence.</article>"


@pytest.fixture
async def setup(tmp_path, monkeypatch):
    hooks = {}
    state = SimpleNamespace(
        html=GATE,
        calls=[],
        applied=[],
        closed=0,
        token=TOKEN,
        url=URL,
        callable=True,
        native_result=False,
        solved_html=SOURCE,
        apply_result=True,
        status=200,
    )
    provider = Crawl4AIProvider(str(tmp_path), limits=CrawlConfig(page_timeout_seconds=5))

    class Page:
        url = URL

        async def content(self):
            return state.html

        async def wait_for_function(self, *_, **__):
            return True

        async def evaluate(self, script, values):
            if "apply-token" in script:
                state.applied.append(values)
                state.html = state.solved_html
                return state.apply_result
            return state.callable

        def on(self, *_):
            pass

        def remove_listener(self, *_):
            pass

    async def execute(kind, domain, **values):
        state.calls.append((kind, domain, values))
        return {"result": {"status": "ready", "solution": {"token": state.token}}}

    provider.optional_providers = SimpleNamespace(
        configs={
            "captcha": SimpleNamespace(enabled=True, provider="capsolver"),
            "proxy": SimpleNamespace(enabled=False),
        },
        execute=execute,
    )

    async def arun(url, config):
        page = Page()
        if hooks.get("after_goto"):
            await hooks["after_goto"](
                page, context=None, url=url, response=SimpleNamespace(headers={}, status=state.status), config=config
            )
        from crawl4ai.models import CrawlResult, MarkdownGenerationResult

        result_class = CrawlResult if state.native_result else SimpleNamespace
        return result_class(
            success=True,
            html=state.html,
            markdown=MarkdownGenerationResult(
                raw_markdown=state.html, markdown_with_citations=state.html, references_markdown=""
            )
            if state.native_result
            else state.html,
            metadata={"title": "Research"},
            response_headers={},
            status_code=200,
            url=state.url,
            links={"internal": [], "external": []},
        )

    async def close():
        state.closed += 1

    async def start(*_, **__):
        provider._crawler = SimpleNamespace(
            arun=arun,
            close=close,
            crawler_strategy=SimpleNamespace(set_hook=lambda key, value: hooks.update({key: value})),
        )

    async def validate(*_, **__):
        pass

    monkeypatch.setattr(provider, "start", start)
    monkeypatch.setattr(provider, "_validate_browser_request", validate)
    yield provider, state
    await provider.close()


async def test_actual_crawl_applies_solver_token_then_returns_source(setup):
    provider, state = setup
    try:
        result = await provider.crawl(URL)
    except RuntimeError as exc:
        pytest.fail(f"Configured solver did not retrieve the source: {exc}")
    assert state.calls == [
        (
            "captcha",
            "example.org",
            {"task": {"type": "AntiTurnstileTaskProxyLess", "websiteURL": URL, "websiteKey": "fixture-sitekey"}},
        )
    ]
    assert len(state.applied) == 1
    assert "Independent research evidence" in result.items[0].content
    assert result.items[0].url == URL
    assert result.items[0].metadata["retrieval_provider"] == "capsolver"
    assert TOKEN not in repr(result)
    assert state.closed == 1


async def test_real_crawl_result_model_accepts_solver_metadata(setup):
    provider, state = setup
    state.native_result = True
    result = await provider.crawl(URL)
    assert result.items[0].metadata["retrieval_provider"] == "capsolver"


@pytest.mark.parametrize(
    "option", [{"mode": "standard"}, {"mode": "managed_profile", "profile": "fixture"}, {"interaction": "scroll"}]
)
async def test_explicit_nonautomatic_modes_do_not_spend(setup, option):
    provider, state = setup
    with pytest.raises(RuntimeError, match="CRAWL_CHALLENGE_REQUIRED"):
        await provider.crawl(URL, **option)
    assert not state.calls and not state.applied


async def test_widget_without_callable_callback_does_not_spend(setup):
    provider, state = setup
    state.callable = False
    with pytest.raises(RuntimeError, match="CRAWL_CHALLENGE_UNSUPPORTED"):
        await provider.crawl(URL)
    assert not state.calls and not state.applied


@pytest.mark.parametrize(
    "token",
    [None, "", {"bad": True}, "x" * 32769, "bad\nsecret"],
    ids=["null", "empty", "object", "oversized", "newline"],
)
async def test_invalid_solution_is_never_applied_or_returned(setup, token):
    provider, state = setup
    state.token = token
    with pytest.raises(RuntimeError, match="CRAWL_CHALLENGE_SOLUTION_INVALID"):
        await provider.crawl(URL)
    assert not state.applied and state.closed == 1


@pytest.mark.parametrize(
    "html",
    [
        GATE.replace('data-sitekey="fixture-sitekey"', ""),
        GATE.replace('data-callback="solved"', 'data-callback="alert(1)"'),
        GATE.replace('data-callback="solved"', 'data-callback="constructor.constructor"'),
        GATE + '<div class="cf-turnstile"></div>',
        GATE.replace("cf-turnstile", "h-captcha"),
        GATE + '<input type="password">',
        GATE + '<form action="/buy"></form>',
    ],
    ids=["missing-key", "expression", "prototype", "ambiguous", "unsupported-kind", "password", "business-form"],
)
async def test_unsupported_or_nonresearch_widget_never_spends(setup, html):
    provider, state = setup
    state.html = html
    with pytest.raises(RuntimeError, match="CRAWL_CHALLENGE_UNSUPPORTED"):
        await provider.crawl(URL)
    assert not state.calls and not state.applied


async def test_unknown_solver_does_not_block_ordinary_research(setup):
    provider, state = setup
    state.html = SOURCE
    provider.optional_providers.configs["captcha"].provider = "not-installed"
    result = await provider.crawl(URL)
    assert "Independent research evidence" in result.items[0].content
    assert not state.calls


async def test_vendor_error_text_is_not_exposed(setup):
    provider, state = setup

    async def broken(*_, **__):
        raise RuntimeError(TOKEN)

    provider.optional_providers.execute = broken
    with pytest.raises(RuntimeError, match="^CRAWL_CHALLENGE_SOLVER_FAILED$"):
        await provider.crawl(URL)
    assert not state.applied and state.closed == 1


async def test_cancellation_while_solving_closes_crawler(setup):
    provider, state = setup
    entered = asyncio.Event()

    async def wait(*_, **__):
        entered.set()
        await asyncio.Event().wait()

    provider.optional_providers.execute = wait
    operation = asyncio.create_task(provider.crawl(URL))
    try:
        await asyncio.wait_for(entered.wait(), 3)
        operation.cancel()
        with pytest.raises(asyncio.CancelledError):
            await operation
        assert state.closed == 1 and not state.applied
    finally:
        operation.cancel()
        await asyncio.gather(operation, return_exceptions=True)


@pytest.mark.parametrize("options", [{"public": False, "local_target": object()}, {"url": URL + "?token=private"}])
async def test_local_or_sensitive_request_does_not_export_to_solver(setup, options):
    provider, state = setup
    with pytest.raises(RuntimeError, match="CRAWL_CHALLENGE_REQUIRED"):
        await provider.crawl(**{"url": URL, **options})
    assert not state.calls


async def test_changed_widget_does_not_become_evidence(setup):
    provider, state = setup
    state.apply_result = False
    with pytest.raises(RuntimeError, match="CRAWL_CHALLENGE_CHANGED"):
        await provider.crawl(URL)


async def test_solver_cannot_turn_http_error_into_success(setup):
    provider, state = setup
    state.status = 403
    with pytest.raises(RuntimeError, match="CRAWL_NO_EVIDENCE"):
        await provider.crawl(URL)


async def test_still_challenged_after_callback_does_not_become_evidence(setup):
    provider, state = setup
    state.solved_html = GATE
    with pytest.raises(RuntimeError, match="CRAWL_CHALLENGE_REQUIRED"):
        await provider.crawl(URL)


@pytest.mark.parametrize(
    "attribute,value",
    [("data-callback", "a" * 257), ("data-response-field-name", "f" * 257), ("data-response-field-name", "bad\nfield")],
    ids=["oversized-callback", "oversized-response-field", "control-character-field"],
)
async def test_widget_metadata_is_bounded_before_spending(setup, attribute, value):
    provider, state = setup
    state.html = GATE.replace(
        'data-callback="solved"',
        f'{attribute}="{value}"' + (' data-callback="solved"' if attribute != "data-callback" else ""),
    )
    with pytest.raises(RuntimeError, match="CRAWL_CHALLENGE_UNSUPPORTED"):
        await provider.crawl(URL)
    assert not state.calls and not state.applied
