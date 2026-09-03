# Crawl traversal and cleanup evidence — 2026-09-02

Development checkpoint on private `main`, based on `14e78ce2550a02e121667b2e0ce6a4be9177b742`. Product 0.2.0; result schema 1.5. Commit/CI/live-service identity is recorded separately after delivery. This is not full research acceptance.

## What changed and why

Page/depth/site controls previously disappeared between the tool and crawler, and page count controlled scrolling rather than traversal. Public and local calls now preserve those controls, use option-specific cache keys and collect a bounded breadth-first set of pages with individual citations. Scrolling is an explicit separate request. Failed/empty/HTTP-error pages are not successful evidence; completed pages survive later failures and deadlines.

Public initial navigation shares the existing direct-HTTP origin slot. Managed public results and recognized sensitive final URLs bypass disk cache. CSS selectors/profile combinations are validated; absent advanced interactions, captures and modes return explicit unavailable errors. Standard/auto results identify the actual standard mode. SDK verbose output is disabled. Each bounded call settles owned-browser cleanup, including repeated cancellation.

Ordinary request interception failed the native redirect test. Chromium response-stage interception was then added and tested against top-level cross-host redirects and multi-hop JavaScript fetch redirects that attempt to escape an exact local path. This is consistent with the documented [Playwright route redirect limitation](https://playwright.dev/python/docs/api/class-browsercontext#browser-context-route) and the [Chromium Fetch response-stage protocol](https://chromedevtools.github.io/devtools-protocol/tot/Fetch/). Installed Crawl4AI 0.9.3 controls were inspected along with the official [page interaction documentation](https://docs.crawl4ai.com/core/page-interaction/). No dependency was added.

## Verification scope and falsification

Read before edits: app/service/provider/config/model/security/coordinator neighbors, existing browser/retrieval tests, installed Crawl4AI run/browser/result definitions, quality gate, scope, README/manual/operations/status/progress and manifest script. Current files were re-inspected before delivery.

- `tests/unit/test_crawl_options.py`: 31 cases exercise wrapper forwarding, distinct cache keys, BFS/depth/canonical duplicates, public cross-site choice, exact-local link rejection, lower operator ceilings, content/frontier bounds, partial/all/empty/error results, explicit absent options, profile/CSS validation, scroll bounds, sensitive citations/cache, logging controls, final redirected citation/base, shared HTTP origin exclusion, whole-crawl partial metadata and repeated cancellation.
- `tests/acceptance/test_crawl_traversal_native.py`: six native cases exercise actual installed Chrome, a three-page JavaScript-rendered local set, scroll/page separation, owned child-process exit, permitted/blocked cross-host redirect destinations and a multi-hop fetch redirect escaping a local path. Only the cross-host fixture substitutes public DNS/IP validation with its disposable loopback server permit; production navigation/redirect guards remain active. Other local tests use real exact-target validation.
- Existing `tests/acceptance/test_local_research_browser.py`: two unchanged native cases cover dynamic HTTP/WebSocket policy and an actual Chrome v10 encrypted-cookie import/login fixture.
- The standard gate runs unit/fixture tests only. The native browser cases are explicit separate runs. No private account, personal browser, paid provider, DSH model or DSH configuration was used/changed.

The timeout metadata run initially raised `KeyError`, which is NOT a valid assertion RED. The test was corrected to `.get()`, only the new metadata update was temporarily removed, the assertion failure was observed, and the update was restored before the final gate. The original invalid failure is retained below. The multi-hop fetch falsification was added after the redirect fix and is not claimed as a pre-fix RED. The first full gate failed import ordering; the formatting/import correction preceded the final passing gate.

## Security review and remaining work

- Inputs: strict page/depth ceilings, validated HTTP URLs, exact local policy, public destination resolution, bounded CSS selector syntax, profile/mode checks and response-stage redirect validation. CSS is not arbitrary JavaScript. Existing request/WebSocket policy retained. Chromium DNS rebinding/pinning and cross-origin out-of-process iframe coverage remain unproved.
- Routes/authentication: no new endpoints, account operations or authorization policy changes; existing localhost MCP and operator connection/profile handling retained. Local authenticated caching stays an explicit target setting.
- Secrets: managed public crawl disk caching disabled; recognized sensitive final citations redacted and disk cache skipped; SDK verbose logs disabled. These are not universal redaction of arbitrary page prose/embedded links, nor proof that every third-party error path is quiet. Repository scan is recorded with delivery.
- Rendering/eval/deserialization: no new user-controlled eval, general form actions or UI rendering. Existing page scripts execute in the owned research browser; fetched content remains untrusted evidence.
- Dependencies: no new package/version; uses locked Crawl4AI/Playwright, existing soupsieve and Python standard library. No fresh full dependency vulnerability-audit claim.

Limits: page attempts <=25, depth <=3 (or lower operator ceilings), <=5 scroll steps, <=50,000 content characters/page and <=400,000/crawl, title <=1000, <=250 inspected links/page and remembered frontier URLs. Default whole collection/page deadlines 120/45 seconds start after admission; cleanup duration is separate. Browser native memory, subresource bytes/count/pacing and redirect-origin slots are not fully bounded. SDK cleanup hangs, broad concurrency/crash/stress, foreground/logon/clean installation, arbitrary authenticated pages/app-bound cookies and DSH remain open. `auto` does not escalate anti-bot modes; consent/load-more/pagination-button/site-search, artifacts, stealth/undetected, human challenges and optional adapter crawl routing remain unfinished. Explicit errors do not count as implementing them.

Docs updated: README, manual, operations, changelog, implementation status, progress and the canonical/repository-mirror research-only scope. Updating the three installed host skill scope copies requires explicit approval from the permission reviewer; that approval was requested, and those copies were left unchanged. Full goal remains active. Native/live/CI/recovery receipts must be kept distinct.

## Delivery recheck and repository scan

The final-source native rerun used disposable Chrome/loopback fixtures only.

```powershell
uv run --locked pytest -q tests/acceptance/test_crawl_traversal_native.py tests/acceptance/test_local_research_browser.py
```

```text
........                                                                 [100%]
8 passed in 16.61s
```

Read-only credential-pattern scan (tracked/untracked nonignored files plus ignored AGENTS.md):

```powershell
$taskPaths=@(git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway ls-files --cached --others --exclude-standard | Sort-Object -Unique) + @('AGENTS.md')
$taskSecretPattern='(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|https?://[^\s/@]+:[^\s/@]+@)'
$taskFindings=@(foreach($taskPath in $taskPaths) { Select-String -LiteralPath $taskPath -Pattern $taskSecretPattern | ForEach-Object { [pscustomobject]@{Path=$taskPath;Line=$_.LineNumber} } })
$taskFindings | ConvertTo-Json -Compress
[pscustomobject]@{scanned_files=$taskPaths.Count;credential_pattern_matches=$taskFindings.Count;license_present=(Test-Path LICENSE);contributing_present=(Test-Path CONTRIBUTING.md)} | ConvertTo-Json -Compress
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway check-ignore .env config/config.toml runtime/test.db vault/test.key evidence/private/sample.txt .venv/test dist/test
```

```text
[{"Path":"debug_redaction.py","Line":7},{"Path":"tests/unit/test_redaction.py","Line":11},{"Path":"tests/unit/test_redaction.py","Line":48},{"Path":"tests/unit/test_security.py","Line":35},{"Path":"tests/unit/test_security.py","Line":106},{"Path":"verify_implementation.py","Line":8}]
{"scanned_files":225,"credential_pattern_matches":6,"license_present":false,"contributing_present":false}
.env
config/config.toml
runtime/test.db
vault/test.key
evidence/private/sample.txt
.venv/test
dist/test
```

All six matches were inspected: synthetic userinfo/redaction fixtures in the listed test/debug files, not live credentials. The scan is pattern-based, not a guarantee of all secret detection. The existing .gitignore covers the sampled environment/local-config/runtime/vault/private-evidence/dependency/build paths. LICENSE and CONTRIBUTING.md remain missing: this is a private development checkpoint, not public/package release approval. The README/manual/changelog and source-scope mirror were updated; installed skill instruction-file synchronization is separately approval-pending.

## Exact diagnostic transcript

All commands below ran in `C:\Users\scott\Desktop\Code\halo-research-gateway`. Output chunks are concatenated in observed order without dropping failures or warnings. Paths/URLs in deliberate failing fixtures are synthetic or disposable loopback resources, not credentials. Start/end output may have a chunk-boundary newline.

### Untouched baseline

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
86 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 28%]
................................................
........................ [ 56%]
........................................................................ [ 84%]
...........................
..............                                [100%]
257 passed in 48.26s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)

```

Exit code: 0.

### Option forwarding and real traversal RED

```powershell
uv run --locked pytest -q tests/unit/test_crawl_options.py
```

```text
FFFFFFF                                                                  [100%]
================================== FAILURES ===================================
______ test_web_crawl_forwards_all_content_controls_and_separates_cache _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1955/test_web_crawl_forwards_all_co0')

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
>           assert len(calls) == 3, "different depth/site options reused an incompatible cache result"
E           AssertionError: different depth/site options reused an incompatible cache result
E           assert 1 == 3
E            +  where 1 = len([{'max_pages': 3, 'mode': 'auto', 'wait_for': None, 'profile': None}])

tests\unit\test_crawl_options.py:47: AssertionError
________________ test_local_mcp_forwards_depth_and_interaction ________________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1955/test_local_mcp_forwards_depth_0')

    async def test_local_mcp_forwards_depth_and_interaction(tmp_path):
        app = application_at(tmp_path)
        seen = []
    
        async def crawl(*args, **kwargs):
            seen.append(kwargs)
            return {"ok": True}
    
        app.state.halo_service.local_crawl = crawl
        try:
            await call(app, "local_crawl", target="fixture", path="/research/start", max_depth=2, interaction="scroll")
>           assert seen[0].get("max_depth") == 2
E           AssertionError: assert None == 2
E            +  where None = <built-in method get of dict object at 0x00000284FE6C7C80>('max_depth')
E            +    where <built-in method get of dict object at 0x00000284FE6C7C80> = {'client': 'unidentified'}.get

tests\unit\test_crawl_options.py:67: AssertionError
____________ test_mcp_crawl_visits_linked_pages_to_requested_depth ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1955/test_mcp_crawl_visits_linked_p0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000284FE6A6990>

    async def test_mcp_crawl_visits_linked_pages_to_requested_depth(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {
            URL: ("Root evidence", ["/child", URL + "#duplicate"]),
            "https://example.org/child": ("Child evidence", ["/grandchild"]),
            "https://example.org/grandchild": ("Grandchild evidence", [URL]),
        })
        try:
            result = await call(app, url=URL, max_pages=3, max_depth=2, mode="standard")
            assert result["ok"], result
>           assert [item["content"] for item in result["items"]] == ["Root evidence", "Child evidence", "Grandchild evidence"]
E           AssertionError: assert ['Root evidence'] == ['Root eviden...ild evidence']
E             
E             Right contains 2 more items, first extra item: 'Child evidence'
E             Use -v to get more diff

tests\unit\test_crawl_options.py:116: AssertionError
_____ test_crawl_rejects_out_of_contract_limits_before_browser[options0] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1955/test_crawl_rejects_out_of_cont0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000284AF36A660>
options = {'max_pages': 0}

    @pytest.mark.parametrize("options", [{"max_pages": 0}, {"max_pages": 26}, {"max_depth": -1}, {"max_depth": 4}])
    async def test_crawl_rejects_out_of_contract_limits_before_browser(tmp_path, monkeypatch, options):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, **options)
>           assert not result["ok"], "invalid crawl limits were silently accepted"
E           AssertionError: invalid crawl limits were silently accepted
E           assert not True

tests\unit\test_crawl_options.py:130: AssertionError
_____ test_crawl_rejects_out_of_contract_limits_before_browser[options1] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1955/test_crawl_rejects_out_of_cont1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000284AF3BB920>
options = {'max_pages': 26}

    @pytest.mark.parametrize("options", [{"max_pages": 0}, {"max_pages": 26}, {"max_depth": -1}, {"max_depth": 4}])
    async def test_crawl_rejects_out_of_contract_limits_before_browser(tmp_path, monkeypatch, options):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, **options)
>           assert not result["ok"], "invalid crawl limits were silently accepted"
E           AssertionError: invalid crawl limits were silently accepted
E           assert not True

tests\unit\test_crawl_options.py:130: AssertionError
_____ test_crawl_rejects_out_of_contract_limits_before_browser[options2] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1955/test_crawl_rejects_out_of_cont2')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000284AF44B7D0>
options = {'max_depth': -1}

    @pytest.mark.parametrize("options", [{"max_pages": 0}, {"max_pages": 26}, {"max_depth": -1}, {"max_depth": 4}])
    async def test_crawl_rejects_out_of_contract_limits_before_browser(tmp_path, monkeypatch, options):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, **options)
>           assert not result["ok"], "invalid crawl limits were silently accepted"
E           AssertionError: invalid crawl limits were silently accepted
E           assert not True

tests\unit\test_crawl_options.py:130: AssertionError
_____ test_crawl_rejects_out_of_contract_limits_before_browser[options3] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1955/test_crawl_rejects_out_of_cont3')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000284AF49BBC0>
options = {'max_depth': 4}

    @pytest.mark.parametrize("options", [{"max_pages": 0}, {"max_pages": 26}, {"max_depth": -1}, {"max_depth": 4}])
    async def test_crawl_rejects_out_of_contract_limits_before_browser(tmp_path, monkeypatch, options):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, **options)
>           assert not result["ok"], "invalid crawl limits were silently accepted"
E           AssertionError: invalid crawl limits were silently accepted
E           assert not True

tests\unit\test_crawl_options.py:130: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_crawl_options.py::test_web_crawl_forwards_all_content_controls_and_separates_cache
FAILED tests/unit/test_crawl_options.py::test_local_mcp_forwards_depth_and_interaction
FAILED tests/unit/test_crawl_options.py::test_mcp_crawl_visits_linked_pages_to_requested_depth
FAILED tests/unit/test_crawl_options.py::test_crawl_rejects_out_of_contract_limits_before_browser[options0]
FAILED tests/unit/test_crawl_options.py::test_crawl_rejects_out_of_contract_limits_before_browser[options1]
FAILED tests/unit/test_crawl_options.py::test_crawl_rejects_out_of_contract_limits_before_browser[options2]
FAILED tests/unit/test_crawl_options.py::test_crawl_rejects_out_of_contract_limits_before_browser[options3]
7 failed in 3.43s

```

Exit code: 1.

### Option forwarding and traversal GREEN

```powershell
uv run --locked ruff format src/halo_research_gateway/app.py src/halo_research_gateway/service.py src/halo_research_gateway/providers/crawl4ai_provider.py tests/unit/test_crawl_options.py; uv run --locked pytest -q tests/unit/test_crawl_options.py
```

```text
4 files reformatted
.......                                                                  [100%]
7 passed in 6.20s

```

Exit code: 0.

### Failure, scope, limits, cache and cleanup RED

```powershell
uv run --locked pytest -q tests/unit/test_crawl_options.py -k 'failure or failed_all or cross_site or filtered_local or operator_page or content_and_frontier or managed_profile or repeated_cancellation'
```

```text
FF..FFFFF                                                                [100%]
================================== FAILURES ===================================
________________ test_page_failure_retains_other_citable_pages ________________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1957/test_page_failure_retains_othe0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000015F7A9FADB0>

    async def test_page_failure_retains_other_citable_pages(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {
            URL: ("Root evidence", ["/missing", "/good"]),
            "https://example.org/good": ("Good evidence", []),
        })
        try:
            result = await call(app, url=URL, max_pages=3, max_depth=1)
>           assert result["ok"], result
E           AssertionError: {'schema_version': '1.5', 'ok': False, 'request_id': '5597834d-7d66-4fe9-b970-e8508101bebf', 'tool': 'web_crawl', ...}
E           assert False

tests\unit\test_crawl_options.py:160: AssertionError
_________________ test_failed_all_pages_is_not_empty_success __________________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1957/test_failed_all_pages_is_not_e0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000015F2B8567B0>

    async def test_failed_all_pages_is_not_empty_success(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        install_browser(app, monkeypatch, {})
        try:
            result = await call(app, url=URL)
            assert not result["ok"]
>           assert result["error"]["code"] == "CRAWL_NO_EVIDENCE"
E           AssertionError: assert 'UPSTREAM_UNAVAILABLE' == 'CRAWL_NO_EVIDENCE'
E             
E             - CRAWL_NO_EVIDENCE
E             + UPSTREAM_UNAVAILABLE

tests\unit\test_crawl_options.py:174: AssertionError
___________ test_filtered_local_link_does_not_abort_valid_research ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1957/test_filtered_local_link_does_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000015F2B9512B0>

    async def test_filtered_local_link_does_not_abort_valid_research(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        install_browser(app, monkeypatch, {URL: ("Root evidence", ["/private", "/valid"]),
                                          "https://example.org/valid": ("Valid evidence", [])})
    
        async def validate(url, *args):
            if url.endswith("/private"):
                raise ValueError("fixture forbidden target")
    
        monkeypatch.setattr(app.state.halo_service.crawler, "_validate_browser_request", validate)
        try:
            result = await call(app, url=URL, max_pages=3, max_depth=1)
>           assert result["ok"], result
E           AssertionError: {'schema_version': '1.5', 'ok': False, 'request_id': '61535762-036b-40ea-a437-f0c0c00efd42', 'tool': 'web_crawl', ...}
E           assert False

tests\unit\test_crawl_options.py:204: AssertionError
____________ test_operator_page_ceiling_is_enforced_before_browser ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1957/test_operator_page_ceiling_is_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000015F2B9ABCB0>

    async def test_operator_page_ceiling_is_enforced_before_browser(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        app.state.halo_service.config.crawl.max_pages = 2
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, max_pages=3, max_depth=1)
>           assert not result["ok"]
E           assert not True

tests\unit\test_crawl_options.py:217: AssertionError
__________ test_crawl_content_and_frontier_are_bounded_before_cache ___________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1957/test_crawl_content_and_frontie0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000015F2BAD8F20>

    async def test_crawl_content_and_frontier_are_bounded_before_cache(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("text " * 100_000, [f"/p{n}" for n in range(10_000)])})
        try:
            result = await app.state.halo_service.crawler.crawl(URL, max_pages=1, max_depth=1)
>           assert len(result.items[0].content) <= 50_000
E           AssertionError: assert 500000 <= 50000
E            +  where 500000 = len('text text text text text text text text text text text text text text text text text text text text text text text te...xt text text text text text text text text text text text text text text text text text text text text text text text ')
E            +    where 'text text text text text text text text text text text text text text text text text text text text text text text te...xt text text text text text text text text text text text text text text text text text text text text text text text ' = EvidenceItem(url='https://example.org/start', retrieved_at='2026-09-03T02:07:17.214331Z', title='text text text text t... text text text text text text text text ', metadata={'mode': 'auto', 'profile': None, 'depth': 0, 'status_code': 200}).content

tests\unit\test_crawl_options.py:229: AssertionError
________ test_managed_profile_result_is_not_persisted_by_public_crawl _________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1957/test_managed_profile_result_is0')

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
>           assert len(seen) == 2, "authenticated crawl was reused from disk cache without explicit permission"
E           AssertionError: authenticated crawl was reused from disk cache without explicit permission
E           assert 1 == 2
E            +  where 1 = len(['https://example.org/start'])

tests\unit\test_crawl_options.py:250: AssertionError
_______ test_repeated_cancellation_cannot_abandon_owned_browser_cleanup _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1957/test_repeated_cancellation_can0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000015F2BBC3E60>

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
>           assert browser.closed == 1, "second cancellation abandoned owned browser cleanup"
E           AssertionError: second cancellation abandoned owned browser cleanup
E           assert 0 == 1
E            +  where 0 = <test_crawl_options.BrowserFixture object at 0x0000015F2BD25A90>.closed

tests\unit\test_crawl_options.py:280: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_crawl_options.py::test_page_failure_retains_other_citable_pages
FAILED tests/unit/test_crawl_options.py::test_failed_all_pages_is_not_empty_success
FAILED tests/unit/test_crawl_options.py::test_filtered_local_link_does_not_abort_valid_research
FAILED tests/unit/test_crawl_options.py::test_operator_page_ceiling_is_enforced_before_browser
FAILED tests/unit/test_crawl_options.py::test_crawl_content_and_frontier_are_bounded_before_cache
FAILED tests/unit/test_crawl_options.py::test_managed_profile_result_is_not_persisted_by_public_crawl
FAILED tests/unit/test_crawl_options.py::test_repeated_cancellation_cannot_abandon_owned_browser_cleanup
7 failed, 2 passed, 7 deselected in 2.90s

```

Exit code: 1.

### Reliability and adjacent regressions GREEN

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/crawl4ai_provider.py tests/unit/test_crawl_options.py; uv run --locked pytest -q tests/unit/test_crawl_options.py tests/unit/test_browser_policy.py tests/unit/test_retrieval_regressions.py
```

```text
2 files reformatted
........................
......                                           [100%]
30 passed in 9.24s

```

Exit code: 0.

### Explicit options, scrolling, deadlines, empty and sensitive results RED

```powershell
uv run --locked pytest -q tests/unit/test_crawl_options.py -k 'unimplemented_option or scroll_is or whole_crawl or empty_render or signed_browser'
```

```text
FFFFFFF                                                                  [100%]
================================== FAILURES ===================================
____ test_unimplemented_option_is_explicit_not_silent_success[interaction] ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1959/test_unimplemented_option_is_e0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002A73CE0D4C0>
option = 'interaction'

    @pytest.mark.parametrize("option", ["interaction", "capture", "mode"])
    async def test_unimplemented_option_is_explicit_not_silent_success(tmp_path, monkeypatch, option):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        value = {"interaction": "site_search", "capture": "pdf", "mode": "undetected"}[option]
        try:
            result = await call(app, url=URL, **{option: value})
>           assert not result["ok"], f"{option} was silently ignored"
E           AssertionError: interaction was silently ignored
E           assert not True

tests\unit\test_crawl_options.py:309: AssertionError
______ test_unimplemented_option_is_explicit_not_silent_success[capture] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1959/test_unimplemented_option_is_e1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002A73CE0D7F0>
option = 'capture'

    @pytest.mark.parametrize("option", ["interaction", "capture", "mode"])
    async def test_unimplemented_option_is_explicit_not_silent_success(tmp_path, monkeypatch, option):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        value = {"interaction": "site_search", "capture": "pdf", "mode": "undetected"}[option]
        try:
            result = await call(app, url=URL, **{option: value})
>           assert not result["ok"], f"{option} was silently ignored"
E           AssertionError: capture was silently ignored
E           assert not True

tests\unit\test_crawl_options.py:309: AssertionError
_______ test_unimplemented_option_is_explicit_not_silent_success[mode] ________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1959/test_unimplemented_option_is_e2')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002A76DC71760>
option = 'mode'

    @pytest.mark.parametrize("option", ["interaction", "capture", "mode"])
    async def test_unimplemented_option_is_explicit_not_silent_success(tmp_path, monkeypatch, option):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        value = {"interaction": "site_search", "capture": "pdf", "mode": "undetected"}[option]
        try:
            result = await call(app, url=URL, **{option: value})
>           assert not result["ok"], f"{option} was silently ignored"
E           AssertionError: mode was silently ignored
E           assert not True

tests\unit\test_crawl_options.py:309: AssertionError
________ test_scroll_is_explicit_and_bounded_not_implied_by_page_count ________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1959/test_scroll_is_explicit_and_bo0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002A76DCCB6B0>

    async def test_scroll_is_explicit_and_bounded_not_implied_by_page_count(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, interaction="scroll")
            assert result["ok"], result
            config = browser.calls[0][1]
>           assert config.scan_full_page is True
E           assert False is True
E            +  where False = <crawl4ai.async_configs.CrawlerRunConfig object at 0x000002A76DD943E0>.scan_full_page

tests\unit\test_crawl_options.py:323: AssertionError
______ test_whole_crawl_deadline_preserves_completed_evidence_and_closes ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1959/test_whole_crawl_deadline_pres0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002A76DD94B00>

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
>           assert "CRAWL_TIMEOUT" in result["warnings"]
E           AssertionError: assert 'CRAWL_TIMEOUT' in ['CRAWL_PAGE_FAILED']

tests\unit\test_crawl_options.py:347: AssertionError
_________________ test_empty_render_is_not_research_evidence __________________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1959/test_empty_render_is_not_resea0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002A76DDEC080>

    async def test_empty_render_is_not_research_evidence(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        install_browser(app, monkeypatch, {URL: ("   ", [])})
        try:
            result = await call(app, url=URL)
>           assert not result["ok"]
E           assert not True

tests\unit\test_crawl_options.py:359: AssertionError
__________ test_signed_browser_result_url_is_redacted_and_not_cached __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1959/test_signed_browser_result_url0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002A76DDDBF80>

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
>               assert "fixture-secret" not in result["items"][0]["url"]
E               AssertionError: assert 'fixture-secret' not in 'https://exa...xture-secret'
E                 
E                 'fixture-secret' is contained here:
E                   https://example.org/start?token=fixture-secret
E                 ?                                 ++++++++++++++

tests\unit\test_crawl_options.py:380: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_crawl_options.py::test_unimplemented_option_is_explicit_not_silent_success[interaction]
FAILED tests/unit/test_crawl_options.py::test_unimplemented_option_is_explicit_not_silent_success[capture]
FAILED tests/unit/test_crawl_options.py::test_unimplemented_option_is_explicit_not_silent_success[mode]
FAILED tests/unit/test_crawl_options.py::test_scroll_is_explicit_and_bounded_not_implied_by_page_count
FAILED tests/unit/test_crawl_options.py::test_whole_crawl_deadline_preserves_completed_evidence_and_closes
FAILED tests/unit/test_crawl_options.py::test_empty_render_is_not_research_evidence
FAILED tests/unit/test_crawl_options.py::test_signed_browser_result_url_is_redacted_and_not_cached
7 failed, 16 deselected in 2.54s

```

Exit code: 1.

### Controls GREEN

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/crawl4ai_provider.py tests/unit/test_crawl_options.py; uv run --locked pytest -q tests/unit/test_crawl_options.py
```

```text
1 file reformatted, 1 file left unchanged
..................
.....                                                  [100%]
23 passed in 11.63s

```

Exit code: 0.

### First native traversal, scrolling, cleanup plus existing browser fixtures

```powershell
uv run --locked ruff format tests/acceptance/test_crawl_traversal_native.py; uv run --locked pytest -q tests/acceptance/test_crawl_traversal_native.py tests/acceptance/test_local_research_browser.py
```

```text
1 file reformatted
...
..                                                                    [100%]
5 passed in 12.98s

```

Exit code: 0.

### SDK logging, option validation and real redirect RED

```powershell
uv run --locked pytest -q tests/unit/test_crawl_options.py -k 'sdk_does_not or profile_and_selector' tests/acceptance/test_crawl_traversal_native.py -k 'sdk_does_not or profile_and_selector or cross_host_redirect'
```

```text
FFFFFF.                                                                  [100%]
================================== FAILURES ===================================
___________ test_browser_sdk_does_not_log_research_urls_by_default ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1962/test_browser_sdk_does_not_log_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000299753E6960>

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
>           assert configs[0].verbose is False
E           assert True is False
E            +  where True = <crawl4ai.async_configs.BrowserConfig object at 0x0000029925B7C8F0>.verbose

tests\unit\test_crawl_options.py:406: AssertionError
_ test_profile_and_selector_options_cannot_be_silently_misinterpreted[options0-BROWSER_PROFILE_REQUIRED] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1962/test_profile_and_selector_opti0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000029925B7F560>
options = {'mode': 'managed_profile'}, code = 'BROWSER_PROFILE_REQUIRED'

    @pytest.mark.parametrize("options,code", [
        ({"mode": "managed_profile"}, "BROWSER_PROFILE_REQUIRED"),
        ({"profile": "research-copy"}, "BROWSER_PROFILE_REQUIRES_MANAGED_MODE"),
        ({"wait_for": "js:() => true"}, "CRAWL_SELECTOR_INVALID"),
        ({"wait_for": "#" + "x" * 1024}, "CRAWL_SELECTOR_INVALID"),
    ])
    async def test_profile_and_selector_options_cannot_be_silently_misinterpreted(tmp_path, monkeypatch, options, code):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, **options)
>           assert not result["ok"], result
E           AssertionError: {'schema_version': '1.5', 'ok': True, 'request_id': '46fbdb77-5764-4c37-9400-ce8b72bb8be7', 'tool': 'web_crawl', ...}
E           assert not True

tests\unit\test_crawl_options.py:422: AssertionError
_ test_profile_and_selector_options_cannot_be_silently_misinterpreted[options1-BROWSER_PROFILE_REQUIRES_MANAGED_MODE] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1962/test_profile_and_selector_opti1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000029925B7D580>
options = {'profile': 'research-copy'}
code = 'BROWSER_PROFILE_REQUIRES_MANAGED_MODE'

    @pytest.mark.parametrize("options,code", [
        ({"mode": "managed_profile"}, "BROWSER_PROFILE_REQUIRED"),
        ({"profile": "research-copy"}, "BROWSER_PROFILE_REQUIRES_MANAGED_MODE"),
        ({"wait_for": "js:() => true"}, "CRAWL_SELECTOR_INVALID"),
        ({"wait_for": "#" + "x" * 1024}, "CRAWL_SELECTOR_INVALID"),
    ])
    async def test_profile_and_selector_options_cannot_be_silently_misinterpreted(tmp_path, monkeypatch, options, code):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, **options)
>           assert not result["ok"], result
E           AssertionError: {'schema_version': '1.5', 'ok': True, 'request_id': 'c40dcaa9-fb76-44f8-bef4-4b5b980260cb', 'tool': 'web_crawl', ...}
E           assert not True

tests\unit\test_crawl_options.py:422: AssertionError
_ test_profile_and_selector_options_cannot_be_silently_misinterpreted[options2-CRAWL_SELECTOR_INVALID] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1962/test_profile_and_selector_opti2')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000029925B7D820>
options = {'wait_for': 'js:() => true'}, code = 'CRAWL_SELECTOR_INVALID'

    @pytest.mark.parametrize("options,code", [
        ({"mode": "managed_profile"}, "BROWSER_PROFILE_REQUIRED"),
        ({"profile": "research-copy"}, "BROWSER_PROFILE_REQUIRES_MANAGED_MODE"),
        ({"wait_for": "js:() => true"}, "CRAWL_SELECTOR_INVALID"),
        ({"wait_for": "#" + "x" * 1024}, "CRAWL_SELECTOR_INVALID"),
    ])
    async def test_profile_and_selector_options_cannot_be_silently_misinterpreted(tmp_path, monkeypatch, options, code):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, **options)
>           assert not result["ok"], result
E           AssertionError: {'schema_version': '1.5', 'ok': True, 'request_id': '5bc0bb5e-32dd-4bca-b1d1-2f4556a310ec', 'tool': 'web_crawl', ...}
E           assert not True

tests\unit\test_crawl_options.py:422: AssertionError
_ test_profile_and_selector_options_cannot_be_silently_misinterpreted[options3-CRAWL_SELECTOR_INVALID] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1962/test_profile_and_selector_opti3')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000299267F2900>
options = {'wait_for': '#xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'}
code = 'CRAWL_SELECTOR_INVALID'

    @pytest.mark.parametrize("options,code", [
        ({"mode": "managed_profile"}, "BROWSER_PROFILE_REQUIRED"),
        ({"profile": "research-copy"}, "BROWSER_PROFILE_REQUIRES_MANAGED_MODE"),
        ({"wait_for": "js:() => true"}, "CRAWL_SELECTOR_INVALID"),
        ({"wait_for": "#" + "x" * 1024}, "CRAWL_SELECTOR_INVALID"),
    ])
    async def test_profile_and_selector_options_cannot_be_silently_misinterpreted(tmp_path, monkeypatch, options, code):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, **options)
>           assert not result["ok"], result
E           AssertionError: {'schema_version': '1.5', 'ok': True, 'request_id': '9223c27f-021f-46dd-95bb-3deed59cf94b', 'tool': 'web_crawl', ...}
E           assert not True

tests\unit\test_crawl_options.py:422: AssertionError
_ test_native_cross_host_redirect_is_blocked_before_request_when_scoped[True] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1962/test_native_cross_host_redirec0')
same_site = True

    @pytest.mark.parametrize("same_site", [True, False])
    async def test_native_cross_host_redirect_is_blocked_before_request_when_scoped(tmp_path, same_site):
        hits = []
    
        async def redirect(request):
            raise web.HTTPFound(f"http://localhost:{port}/destination")
    
        async def destination(request):
            hits.append("destination")
            return web.Response(content_type="text/html", text="<h1>Redirect source evidence</h1><p>This controlled fixture supplies enough useful source text to test whether a cross-host navigation was permitted before the browser made its request.</p>")
    
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
>               with pytest.raises(RuntimeError, match="CRAWL_NO_EVIDENCE"):
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E               Failed: DID NOT RAISE RuntimeError

tests\acceptance\test_crawl_traversal_native.py:180: Failed
---------------------------- Captured stderr call -----------------------------
[INIT].... \u2192 Crawl4AI 0.9.3 \n[FETCH]... \u2193 http://127.0.0.1:50847/redirect                                                                      | \u2713 | \u23f1: 1.24s \n[SCRAPE].. \u25c6 http://127.0.0.1:50847/redirect                                                                      | \u2713 | \u23f1: 0.00s \n[COMPLETE] \u25cf http://127.0.0.1:50847/redirect                                                                      | \u2713 | \u23f1: 1.25s 
=========================== short test summary info ===========================
FAILED tests/unit/test_crawl_options.py::test_browser_sdk_does_not_log_research_urls_by_default
FAILED tests/unit/test_crawl_options.py::test_profile_and_selector_options_cannot_be_silently_misinterpreted[options0-BROWSER_PROFILE_REQUIRED]
FAILED tests/unit/test_crawl_options.py::test_profile_and_selector_options_cannot_be_silently_misinterpreted[options1-BROWSER_PROFILE_REQUIRES_MANAGED_MODE]
FAILED tests/unit/test_crawl_options.py::test_profile_and_selector_options_cannot_be_silently_misinterpreted[options2-CRAWL_SELECTOR_INVALID]
FAILED tests/unit/test_crawl_options.py::test_profile_and_selector_options_cannot_be_silently_misinterpreted[options3-CRAWL_SELECTOR_INVALID]
FAILED tests/acceptance/test_crawl_traversal_native.py::test_native_cross_host_redirect_is_blocked_before_request_when_scoped[True]
6 failed, 1 passed, 26 deselected in 6.07s

```

Exit code: 1.

### Failed ordinary-request redirect fix (not GREEN)

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/crawl4ai_provider.py tests/unit/test_crawl_options.py tests/acceptance/test_crawl_traversal_native.py; uv run --locked pytest -q tests/unit/test_crawl_options.py tests/acceptance/test_crawl_traversal_native.py tests/acceptance/test_local_research_browser.py
```

```text
3 files reformatted
...............
................F...                                      [100%]
================================== FAILURES ===================================
_ test_native_cross_host_redirect_is_blocked_before_request_when_scoped[True] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1963/test_native_cross_host_redirec0')
same_site = True

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
>               with pytest.raises(RuntimeError, match="CRAWL_NO_EVIDENCE"):
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E               Failed: DID NOT RAISE RuntimeError

tests\acceptance\test_crawl_traversal_native.py:183: Failed
---------------------------- Captured stderr call -----------------------------
[FETCH]... \u2193 http://127.0.0.1:65309/redirect                                                                      | \u2713 | \u23f1: 1.24s \n[SCRAPE].. \u25c6 http://127.0.0.1:65309/redirect                                                                      | \u2713 | \u23f1: 0.00s \n[COMPLETE] \u25cf http://127.0.0.1:65309/redirect                                                                      | \u2713 | \u23f1: 1.24s 
=========================== short test summary info ===========================
FAILED tests/acceptance/test_crawl_traversal_native.py::test_native_cross_host_redirect_is_blocked_before_request_when_scoped[True]
1 failed, 34 passed in 27.74s

```

Exit code: 1.

### Actual mode, HTTP errors and redirected citation/base RED

```powershell
uv run --locked pytest -q tests/unit/test_crawl_options.py -k 'scroll_is or http_error_response or redirected_browser'
```

```text
FFF                                                                      [100%]
================================== FAILURES ===================================
________ test_scroll_is_explicit_and_bounded_not_implied_by_page_count ________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1964/test_scroll_is_explicit_and_bo0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002536CE209B0>

    async def test_scroll_is_explicit_and_bounded_not_implied_by_page_count(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", [])})
        try:
            result = await call(app, url=URL, interaction="scroll")
            assert result["ok"], result
            config = browser.calls[0][1]
            assert config.scan_full_page is True
            assert config.max_scroll_steps == 5
>           assert config.verbose is False
E           assert True is False
E            +  where True = <crawl4ai.async_configs.CrawlerRunConfig object at 0x000002536D2D9D00>.verbose

tests\unit\test_crawl_options.py:325: AssertionError
___________ test_browser_http_error_response_is_not_source_success ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1964/test_browser_http_error_respon0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002536D256510>

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
>           assert not result["ok"]
E           assert not True

tests\unit\test_crawl_options.py:446: AssertionError
_________ test_redirected_browser_url_is_the_citation_and_child_base __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1964/test_redirected_browser_url_is0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002531E10DE20>

    async def test_redirected_browser_url_is_the_citation_and_child_base(tmp_path, monkeypatch):
        app = application_at(tmp_path)
        browser = install_browser(app, monkeypatch, {URL: ("Root evidence", ["child"]),
                                                  "https://example.org/docs/child": ("Child evidence", [])})
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
>           assert result["items"][0]["url"] == "https://example.org/docs/index"
E           AssertionError: assert 'https://example.org/start' == 'https://exam...rg/docs/index'
E             
E             - https://example.org/docs/index
E             ?                     --- ^^^^^^
E             + https://example.org/start
E             ?                      ^^^^

tests\unit\test_crawl_options.py:468: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_crawl_options.py::test_scroll_is_explicit_and_bounded_not_implied_by_page_count
FAILED tests/unit/test_crawl_options.py::test_browser_http_error_response_is_not_source_success
FAILED tests/unit/test_crawl_options.py::test_redirected_browser_url_is_the_citation_and_child_base
3 failed, 27 deselected in 2.09s

```

Exit code: 1.

### Response-stage redirect fix GREEN

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/crawl4ai_provider.py tests/unit/test_crawl_options.py; uv run --locked pytest -q tests/acceptance/test_crawl_traversal_native.py tests/acceptance/test_local_research_browser.py tests/unit/test_crawl_options.py
```

```text
2 files reformatted
...
..................................                                    [100%]
37 passed in 26.46s

```

Exit code: 0.

### Initial full gate failed import sorting before tests

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
88 files already formatted
[GATE] lint
I001 [*] Import block is un-sorted or un-formatted
  --> tests\unit\test_crawl_options.py:3:1
   |
 1 |   """Crawl controls must affect real collection, not just tool signatures."""
 2 |
 3 | / from types import SimpleNamespace
 4 | |
 5 | | import asyncio
 6 | |
 7 | | import pytest
 8 | | from mcp.server.mcpserver import Context
 9 | |
10 | | from halo_research_gateway.app import create_application
11 | | from halo_research_gateway.config import GatewayConfig, LocalTargetConfig
12 | | from halo_research_gateway.models import EvidenceItem, ProviderResult
   | |_____________________________________________________________________^
13 |
14 |   URL = "https://example.org/start"
   |
help: Organize imports
  |
2 |
  - from types import SimpleNamespace
  -
3 | import asyncio
4 + from types import SimpleNamespace
5 |
  |

Found 1 error.
[*] 1 fixable with the `--fix` option.
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | lint failed with exit code 1

```

Exit code: 1.

### Native multi-hop fetch redirect falsification (added after fix)

```powershell
uv run --locked ruff format tests/acceptance/test_crawl_traversal_native.py; uv run --locked pytest -q tests/acceptance/test_crawl_traversal_native.py -k 'fetch_redirect_chain'
```

```text
1 file reformatted
.                                                                        [100%]
1 passed, 5 deselected in 2.66s

```

Exit code: 0.

### Shared origin assertion RED and invalid metadata RED

```powershell
uv run --locked pytest -q tests/unit/test_crawl_options.py -k 'shares_the_direct or whole_crawl_deadline'
```

```text
FF                                                                       [100%]
================================== FAILURES ===================================
______ test_whole_crawl_deadline_preserves_completed_evidence_and_closes ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1967/test_whole_crawl_deadline_pres0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001A8E0E26210>

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
>           assert result["items"][0]["metadata"]["attempted_pages"] == 2
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           KeyError: 'attempted_pages'

tests\unit\test_crawl_options.py:352: KeyError
____________ test_public_crawl_shares_the_direct_http_origin_slot _____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1967/test_public_crawl_shares_the_d0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001A891C5BDD0>

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
>               assert not browser.calls, "browser navigation bypassed the direct HTTP origin slot"
E               AssertionError: browser navigation bypassed the direct HTTP origin slot
E               assert not [('https://example.org/start', <crawl4ai.async_configs.CrawlerRunConfig object at 0x000001A891D320F0>)]
E                +  where [('https://example.org/start', <crawl4ai.async_configs.CrawlerRunConfig object at 0x000001A891D320F0>)] = <test_crawl_options.BrowserFixture object at 0x000001A891D31D00>.calls

tests\unit\test_crawl_options.py:495: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_crawl_options.py::test_whole_crawl_deadline_preserves_completed_evidence_and_closes
FAILED tests/unit/test_crawl_options.py::test_public_crawl_shares_the_direct_http_origin_slot
2 failed, 29 deselected in 1.95s

```

Exit code: 1.

### Full targeted GREEN

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/crawl4ai_provider.py src/halo_research_gateway/service.py tests/unit/test_crawl_options.py; uv run --locked pytest -q tests/unit/test_crawl_options.py tests/acceptance/test_crawl_traversal_native.py tests/acceptance/test_local_research_browser.py
```

```text
2 files reformatted, 1 file left unchanged
..............
.........................                                  [100%]
39 passed in 28.32s

```

Exit code: 0.

### Corrected timeout metadata assertion RED

```powershell
uv run --locked pytest -q tests/unit/test_crawl_options.py -k 'whole_crawl_deadline'
```

```text
F                                                                        [100%]
================================== FAILURES ===================================
______ test_whole_crawl_deadline_preserves_completed_evidence_and_closes ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1969/test_whole_crawl_deadline_pres0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002B7D3BE8980>

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
>           assert result["items"][0]["metadata"].get("attempted_pages") == 2
E           AssertionError: assert None == 2
E            +  where None = <built-in method get of dict object at 0x000002B7FFDE0680>('attempted_pages')
E            +    where <built-in method get of dict object at 0x000002B7FFDE0680> = {'mode': 'standard', 'requested_mode': 'auto', 'authenticated_source': False, 'interaction': 'none', ...}.get

tests\unit\test_crawl_options.py:352: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_crawl_options.py::test_whole_crawl_deadline_preserves_completed_evidence_and_closes
1 failed, 30 deselected in 1.74s

```

Exit code: 1.

### Final widened full gate GREEN

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
88 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
.................................................
....................... [ 25%]
........................................................................ [ 50%]
........................................................................ [ 75%]
.........
............................................................... [100%]
288 passed in 60.70s (0:01:00)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)

```

Exit code: 0.
