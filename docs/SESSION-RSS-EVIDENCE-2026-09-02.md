# Research-session and RSS reliability evidence — 2026-09-02

Baseline was the green 148-test checkpoint d9bb096. Changes remain local until committed with this evidence. No personal Chrome profile, external login, paid provider or DSH configuration was used. Real browser fixtures are separate from deterministic CI.

The source-cookie test uses a newly created installed-Chrome profile, an HTTP-only cookie set by a disposable loopback source, a clean Chrome shutdown, cookie-only importer execution and Crawl4AI retrieval. SQLite metadata showed the fixture cookie uses v10 encryption, not v20 app-bound encryption. Successful reuse must not be presented as proof of v20 or real-site compatibility.

The first attempt raised CHROME_SOURCE_APPEARS_OPEN because Chrome leaves a database LOCK file after closing. After that fix, a tiny placeholder page triggered Crawl4AI's anti-bot heuristic; the fixture was changed to ordinary HTML with meaningful text. The assertion-based failure below then isolated absent authentication. Adding a named profile alone did not solve it: installed Crawl4AI 0.9.3's persistent path ignores chrome_channel and starts bundled Chromium. The final implementation lets installed Chrome read only the owned copy, blocks navigation during that read, and supplies cookies to the regular isolated research Chrome context in memory. It does not export plaintext cookies or persist refreshed research-context cookies back into the source. This adds one temporary Chrome launch when switching to an imported profile.

An initial post-reuse assertion incorrectly required no Login Data file after Chrome had opened the copy. Corrected verification checks that it is absent immediately after import and that Chrome's subsequently created database contains zero logins. The test was not relaxed to permit imported passwords.

RSS now uses the existing size-bounded, DNS-pinned, redirect-revalidating HTTP provider and an explicit Atom/RSS Accept header. Previously it created an unbounded independent HTTP request. HTTP429 now returns RATE_LIMITED with a retry delay and persists an immediate shared cooldown; threshold failures extend it. Paid fallback remains disabled.

## Closed-profile assertion RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_chrome_import.py -k stale_lock
```

```text
F                                                                        [100%]
================================== FAILURES ===================================
______ test_closed_chrome_stale_lock_file_does_not_prevent_cookie_import ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1856/test_closed_chrome_stale_lock_0')

    def test_closed_chrome_stale_lock_file_does_not_prevent_cookie_import(tmp_path):
        source = fixture_profile(tmp_path)
        (source / "LOCK").write_bytes(b"")
        importer = ChromeImporter(tmp_path / "gateway-profiles")
        preview = importer.preview(source, "closed-profile", ["cookies"])
        try:
            receipt = importer.execute(preview)
        except ValueError as exc:
            receipt = {"status": str(exc)}
>       assert receipt["status"] == "imported"
E       AssertionError: assert 'CHROME_SOURCE_APPEARS_OPEN' == 'imported'
E         
E         - imported
E         + CHROME_SOURCE_APPEARS_OPEN

tests\unit\test_chrome_import.py:50: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_chrome_import.py::test_closed_chrome_stale_lock_file_does_not_prevent_cookie_import
1 failed, 3 deselected in 0.20s

```

## Actual cookie assertion RED

Command:

```powershell
uv run --locked python -m pytest -q tests/acceptance/test_local_research_browser.py -k cookie_only
```

```text
F                                                                        [100%]
================================== FAILURES ===================================
__________ test_cookie_only_import_reuses_real_chrome_research_login __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1859/test_cookie_only_import_reuses0')

    @pytest.mark.asyncio
    async def test_cookie_only_import_reuses_real_chrome_research_login(tmp_path):
        from playwright.async_api import async_playwright
    
        from halo_research_gateway.connections.chrome_import import ChromeImporter
    
        async def login(request):
            response = web.Response(text="Fixture research session established")
            response.set_cookie("research_session", "fixture-only", max_age=3600, httponly=True)
            return response
    
        async def source(request):
            authorized = request.cookies.get("research_session") == "fixture-only"
            state = "AUTHENTICATED_RESEARCH_EVIDENCE" if authorized else "LOGIN_REQUIRED"
            return web.Response(text=f"<!doctype html><html><head><title>Research session fixture</title></head><body><h1>{state}</h1><p>This disposable research fixture checks browser session continuity. The browser must carry its own existing session cookie before the server supplies the protected evidence marker. No personal account, browsing history, saved password, payment data or external service is used by this test.</p></body></html>", content_type="text/html")
    
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
                context = await playwright.chromium.launch_persistent_context(str(source_root), channel="chrome", headless=True)
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
            result = await provider.crawl(target.build_url("/research/source"), public=False, local_target=target, mode="managed_profile", profile="research-copy")
>           assert "AUTHENTICATED_RESEARCH_EVIDENCE" in result.items[0].content
E           AssertionError: assert 'AUTHENTICATED_RESEARCH_EVIDENCE' in '# LOGIN_REQUIRED\nThis disposable research fixture checks browser session continuity. The browser must carry its own ...arker. No personal account, browsing history, saved password, payment data or external service is used by this test.\n'
E            +  where '# LOGIN_REQUIRED\nThis disposable research fixture checks browser session continuity. The browser must carry its own ...arker. No personal account, browsing history, saved password, payment data or external service is used by this test.\n' = EvidenceItem(url='http://127.0.0.1:53029/research/source', retrieved_at='2026-09-02T22:34:40.884233Z', title='Research...service is used by this test.\n', metadata={'mode': 'managed_profile', 'profile': 'research-copy', 'status_code': 200}).content

tests\acceptance\test_local_research_browser.py:140: AssertionError
---------------------------- Captured stderr call -----------------------------
[INIT].... \u2192 Crawl4AI 0.9.3 \n[FETCH]... \u2193 http://127.0.0.1:53029/research/source                                                               | \u2713 | \u23f1: 0.84s \n[SCRAPE].. \u25c6 http://127.0.0.1:53029/research/source                                                               | \u2713 | \u23f1: 0.00s \n[COMPLETE] \u25cf http://127.0.0.1:53029/research/source                                                               | \u2713 | \u23f1: 0.84s 
=========================== short test summary info ===========================
FAILED tests/acceptance/test_local_research_browser.py::test_cookie_only_import_reuses_real_chrome_research_login
1 failed, 1 deselected in 4.52s

```

## RSS transport/backoff RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_reddit_reliability.py
```

```text
FF                                                                       [100%]
================================== FAILURES ===================================
____________ test_rss_uses_shared_bounded_download_and_atom_accept ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1853/test_rss_uses_shared_bounded_d0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000014A6859E9F0>

    @pytest.mark.asyncio
    async def test_rss_uses_shared_bounded_download_and_atom_accept(tmp_path, monkeypatch):
        service = service_at(tmp_path)
        calls = []
    
        async def download(url, accept=None):
            calls.append((url, accept))
            return url, None, {}, ATOM
    
        async def resolve(target):
            return "8.8.8.8"
    
        monkeypatch.setattr("halo_research_gateway.service.resolve_public", resolve)
        monkeypatch.setattr("halo_research_gateway.service.PinnedTransport", lambda *_: httpx.MockTransport(lambda req: httpx.Response(200, content=ATOM)))
        service.http.download = download
        try:
            result = await service._rss("https://www.reddit.com/search.rss?q=research", 2)
            assert len(result.items) == 1
>           assert calls == [("https://www.reddit.com/search.rss?q=research", "application/atom+xml,application/rss+xml")]
E           AssertionError: assert [] == [('https://ww...ion/rss+xml')]
E             
E             Right contains one more item: ('https://www.reddit.com/search.rss?q=research', 'application/atom+xml,application/rss+xml')
E             Use -v to get more diff

tests\unit\test_reddit_reliability.py:36: AssertionError
____ test_reddit_429_reports_retry_and_backs_off_before_circuit_threshold _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1853/test_reddit_429_reports_retry_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000014A6859F830>

    @pytest.mark.asyncio
    async def test_reddit_429_reports_retry_and_backs_off_before_circuit_threshold(tmp_path, monkeypatch):
        service = service_at(tmp_path)
    
        def response(request):
            return httpx.Response(429, headers={"Retry-After": "120"}, request=request)
    
        async def resolve(target):
            return "8.8.8.8"
    
        async def download(url, accept=None):
            response(httpx.Request("GET", url)).raise_for_status()
    
        monkeypatch.setattr("halo_research_gateway.service.resolve_public", resolve)
        monkeypatch.setattr("halo_research_gateway.service.PinnedTransport", lambda *_: httpx.MockTransport(response))
        service.http.download = download
        try:
            result = await service.reddit_thread("https://www.reddit.com/r/test/comments/abc/topic/")
>           assert result["error"]["code"] == "RATE_LIMITED"
E           AssertionError: assert 'UPSTREAM_UNAVAILABLE' == 'RATE_LIMITED'
E             
E             - RATE_LIMITED
E             + UPSTREAM_UNAVAILABLE

tests\unit\test_reddit_reliability.py:59: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_reddit_reliability.py::test_rss_uses_shared_bounded_download_and_atom_accept
FAILED tests/unit/test_reddit_reliability.py::test_reddit_429_reports_retry_and_backs_off_before_circuit_threshold
2 failed in 1.36s

```

## Initial widened gate (browser passed; lint failed)

Command:

```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/acceptance/test_local_research_browser.py
pwsh -NoProfile -File scripts/Update-BuildManifest.ps1
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
72 files left unchanged
..                                                                       [100%]
2 passed in 5.72s
Wrote BUILD-MANIFEST.json with 195 files.
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
72 files already formatted
[GATE] lint
F401 [*] `.providers.http_fetch.PinnedTransport` imported but unused
  --> src\halo_research_gateway\service.py:35:54
   |
33 | from .providers.exa import ExaProvider, ExaRateLimited
34 | from .providers.github import GitHubProvider
35 | from .providers.http_fetch import HttpFetchProvider, PinnedTransport, resolve_public
   |                                                      ^^^^^^^^^^^^^^^
36 | from .providers.optional import OptionalProviderRegistry
37 | from .providers.paid import BrightDataUnlockerAdapter, CapSolverAdapter
   |
help: Remove unused import
   |
34 | from .providers.github import GitHubProvider
   - from .providers.http_fetch import HttpFetchProvider, PinnedTransport, resolve_public
35 + from .providers.http_fetch import HttpFetchProvider
36 | from .providers.optional import OptionalProviderRegistry
   |

F401 [*] `.providers.http_fetch.resolve_public` imported but unused
  --> src\halo_research_gateway\service.py:35:71
   |
33 | from .providers.exa import ExaProvider, ExaRateLimited
34 | from .providers.github import GitHubProvider
35 | from .providers.http_fetch import HttpFetchProvider, PinnedTransport, resolve_public
   |                                                                       ^^^^^^^^^^^^^^
36 | from .providers.optional import OptionalProviderRegistry
37 | from .providers.paid import BrightDataUnlockerAdapter, CapSolverAdapter
   |
help: Remove unused import
   |
34 | from .providers.github import GitHubProvider
   - from .providers.http_fetch import HttpFetchProvider, PinnedTransport, resolve_public
35 + from .providers.http_fetch import HttpFetchProvider
36 | from .providers.optional import OptionalProviderRegistry
   |

F401 [*] `.security.validate_url` imported but unused
  --> src\halo_research_gateway\service.py:42:39
   |
40 | from .providers.transcripts import TranscriptProvider
41 | from .rate_limit import ProviderRateLimited, RateLedger
42 | from .security import UrlPolicyError, validate_url
   |                                       ^^^^^^^^^^^^
help: Remove unused import: `.security.validate_url`
   |
41 | from .rate_limit import ProviderRateLimited, RateLedger
   - from .security import UrlPolicyError, validate_url
42 + from .security import UrlPolicyError
43 |
   |

Found 3 errors.
[*] 3 fixable with the `--fix` option.
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | lint failed with exit code 1

```

## Final verification

`uv run --locked python -m pytest -q tests/unit/test_reddit_reliability.py tests/unit/test_v15_state.py`:

```text
14 passed in 9.54s
```

`uv run --locked python -m pytest -q tests/acceptance/test_local_research_browser.py`:

```text
..                                                                       [100%]
2 passed in 5.72s
```

After removing obsolete RSS imports, `uv run --locked ruff format src tests`, `pwsh -NoProfile -File scripts/Update-BuildManifest.ps1`, and `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`:

```text
1 file reformatted, 71 files left unchanged
Wrote BUILD-MANIFEST.json with 195 files.
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
72 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
151 passed in 13.19s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

Files read before modification: cookie importer, browser provider and installed Crawl4AI launch implementation, service RSS/error path, rate ledger, affected unit/browser tests, manual, changelog, current skill limitations. No dependency added; no new model-facing tool or credential-bearing log. Per-context cookies still require private-result handling already present in managed-profile calls. Full job, challenge, reliability, DSH and delivery goals remain open.

