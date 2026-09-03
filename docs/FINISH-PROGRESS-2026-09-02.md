# Research-only completion work — 2026-09-02

This tracks Scott's full six-part completion goal. No partial checkpoint closes
the goal. The research-only scope remains unchanged.

| Requirement | Current evidence/status |
| --- | --- |
| GitHub fallback pagination | Fixed with a full normalized snapshot and GitHub-bound cursor; regression passes without a second upstream request. |
| Local browser requests | Exact target is passed into immutable per-context guards; host/port/path/method checks and decoded traversal rejection added. Real Chrome fixture passed. |
| WebSocket handling | Async close is awaited; allowed local socket returns evidence and forbidden socket never reaches the server in real Chrome. |
| GitHub discussions and ref support | Implemented; authenticated public-source adapter canary passed for search, exact discussion/replies, and commit-pinned README. Full DSH acceptance still pending. |
| All research source tools and authenticated GitHub | Live MCP search, page/cursor, JS rendering, PDF, captions, Reddit search and HN thread have results. Exa misattribution/filter defects fixed in d9bb096. Reddit thread throttling found and repaired locally; full matrix/DSH proof remains. |
| Document options, tables and local OCR | Table/OCR arguments and cache isolation fixed; generated PDFs prove page-cited tables and actual local English OCR through the MCP dispatcher. Owned native parser cancellation/deadline and bounded input/output/raster/text/table handling have regressions. Final sensitive PDF redirects are redacted and not disk-cached. DSH, arbitrary scan/layout and hard native RAM bounds remain unproved. See DOCUMENT-EXTRACTION-EVIDENCE-2026-09-02.md. |
| Research login/challenge/optional providers | Actual Chrome cookie-only login fixture passes after stale-LOCK and persistent-channel defects were fixed. Real-world profile/site choice, app-bound cookies, challenge flow and provider routing remain. No paid calls authorized. |
| Full DSH workflow and durable-job controls | Fresh DSH rerun still FAILED before tool dispatch; all 119 prior sessions retained. Repair/restart approval remains requested. Native process-crash recovery and live Gateway MCP pause/frozen-state/resume/budget/evidence-pagination canaries passed. DSH jobs and broad stress remain unproved. See DURABLE-JOB-EVIDENCE-2026-09-02.md and LIVE-CHECKPOINT-2026-09-02.md. |
| Reliability and installation | Three coordinator cancellation races and background launcher identity/duplicate-start/configured-port/cleanup defects fixed; 227 unit/fixture tests pass. Real loopback HTTPX cancellation and disposable native launcher tests pass. Foreground/logon, broader provider/browser/recovery/install testing and source-option/resource-bound gaps remain. See COORDINATOR-CANCELLATION-EVIDENCE-2026-09-02.md and LAUNCHER-OWNERSHIP-EVIDENCE-2026-09-02.md. |
| Delivery | Source checkpoints pushed directly to main through b178cbe; exact-SHA CI run 33697543325 passed. Gateway-only idle reload at 2026-09-02T23:59:44.28445Z passed live MCP smoke. The corrected owner-only landing page is Sites version 3. Subsequent evidence-only commits need their own CI receipt. No PR merge or new product tag is claimed. See SITE-CORRECTION-2026-09-02.md and LIVE-CHECKPOINT-2026-09-02.md. |

## First retrieval checkpoint

Baseline command: `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`.
Baseline summary: `131 passed in 4.23s`; `[GATE] PASS (Commit)`.

The installed Playwright API was inspected: `connect_to_server` is synchronous,
`close` is asynchronous. This is consistent with the
[official WebSocketRoute API](https://playwright.dev/python/docs/api/class-websocketroute).

RED command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_retrieval_regressions.py tests/unit/test_browser_policy.py -k 'not operator_defined_local_websocket_mode_can_connect'
```

The excluded case initially needed the new explicit local-policy parameter and
raised TypeError; it is not counted as assertion-based RED evidence. It was
included in the final targeted/full runs. Complete assertion-based RED output:

```text
FFFFFF.FF.                                                               [100%]
================================== FAILURES ===================================
__________ test_github_public_fallback_continues_with_its_own_cursor __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1836/test_github_public_fallback_co0')

    @pytest.mark.asyncio
    async def test_github_public_fallback_continues_with_its_own_cursor(tmp_path):
        service = service_at(tmp_path)
        calls = 0
    
        async def search(query, max_results):
            nonlocal calls
            calls += 1
            return ProviderResult("exa", [EvidenceItem(
                url="https://github.com/acme/widget/blob/main/README.md",
                retrieved_at="2026-09-02T00:00:00Z", content="source evidence " * 900,
            )])
    
        service.exa.search = search
        try:
            first = await service.github_research("widget", max_chars=2000)
            assert first["page"]["next_cursor"]
            second = await service.github_research("", cursor=first["page"]["next_cursor"])
>           assert second["ok"], second
E           AssertionError: {'schema_version': '1.5', 'ok': False, 'request_id': 'f5541905-39cc-4e24-a20a-4b906306e689', 'tool': 'github_research', ...}
E           assert False

tests\unit\test_retrieval_regressions.py:36: AssertionError
_____ test_local_target_path_cannot_escape_its_prefix[/research/../admin] _____

path = '/research/../admin'

    @pytest.mark.parametrize("path", ["/research/../admin", "/research/%2e%2e/admin", "/research/%252e%252e/admin", "/research/..\\admin"])
    def test_local_target_path_cannot_escape_its_prefix(path):
        target = LocalTarget("fixture", "http", "127.0.0.1", 3090, ("/research",), browser_allowed=True)
>       with pytest.raises(ValueError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_retrieval_regressions.py:49: Failed
___ test_local_target_path_cannot_escape_its_prefix[/research/%2e%2e/admin] ___

path = '/research/%2e%2e/admin'

    @pytest.mark.parametrize("path", ["/research/../admin", "/research/%2e%2e/admin", "/research/%252e%252e/admin", "/research/..\\admin"])
    def test_local_target_path_cannot_escape_its_prefix(path):
        target = LocalTarget("fixture", "http", "127.0.0.1", 3090, ("/research",), browser_allowed=True)
>       with pytest.raises(ValueError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_retrieval_regressions.py:49: Failed
_ test_local_target_path_cannot_escape_its_prefix[/research/%252e%252e/admin] _

path = '/research/%252e%252e/admin'

    @pytest.mark.parametrize("path", ["/research/../admin", "/research/%2e%2e/admin", "/research/%252e%252e/admin", "/research/..\\admin"])
    def test_local_target_path_cannot_escape_its_prefix(path):
        target = LocalTarget("fixture", "http", "127.0.0.1", 3090, ("/research",), browser_allowed=True)
>       with pytest.raises(ValueError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_retrieval_regressions.py:49: Failed
____ test_local_target_path_cannot_escape_its_prefix[/research/..\\admin] _____

path = '/research/..\\admin'

    @pytest.mark.parametrize("path", ["/research/../admin", "/research/%2e%2e/admin", "/research/%252e%252e/admin", "/research/..\\admin"])
    def test_local_target_path_cannot_escape_its_prefix(path):
        target = LocalTarget("fixture", "http", "127.0.0.1", 3090, ("/research",), browser_allowed=True)
>       with pytest.raises(ValueError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_retrieval_regressions.py:49: Failed
______________ test_service_passes_exact_target_to_local_browser ______________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1836/test_service_passes_exact_targ0')

    @pytest.mark.asyncio
    async def test_service_passes_exact_target_to_local_browser(tmp_path):
        service = service_at(tmp_path)
        service.config.local_targets["fixture"] = LocalTargetConfig(
            scheme="http", host="127.0.0.1", port=3090, path_prefixes=["/research"], browser_allowed=True,
        )
        captured = {}
    
        async def crawl(url, **kwargs):
            captured.update(kwargs)
            return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-02T00:00:00Z", content="fixture")])
    
        service.crawler.crawl = crawl
        try:
            result = await service.local_crawl("fixture", "/research/page")
            assert result["ok"], result
>           assert "local_target" in captured
E           AssertionError: assert 'local_target' in {'max_pages': 1, 'mode': 'standard', 'profile': None, 'public': False}

tests\unit\test_retrieval_regressions.py:69: AssertionError
_______________ test_local_crawl_uses_separate_operator_policy ________________

    @pytest.mark.asyncio
    async def test_local_crawl_uses_separate_operator_policy():
>       with pytest.raises(ValueError, match="LOCAL_TARGET_REQUIRED"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_browser_policy.py:17: Failed
_______ test_public_websocket_to_loopback_is_blocked_before_connection ________

    @pytest.mark.asyncio
    async def test_public_websocket_to_loopback_is_blocked_before_connection():
        websocket = FakeWebSocket("ws://127.0.0.1/private")
        await Crawl4AIProvider._handle_websocket(websocket, True)
        assert websocket.connected is False
>       assert websocket.closed == {"code": 1008, "reason": "Blocked by Halo egress policy"}
E       AssertionError: assert None == {'code': 1008, 'reason': 'Blocked by Halo egress policy'}
E        +  where None = <test_browser_policy.FakeWebSocket object at 0x00000254B6A25CA0>.closed

tests\unit\test_browser_policy.py:39: AssertionError
============================== warnings summary ===============================
tests/unit/test_browser_policy.py::test_public_websocket_to_loopback_is_blocked_before_connection
  C:\Users\scott\Desktop\Code\halo-research-gateway\src\halo_research_gateway\providers\crawl4ai_provider.py:163: RuntimeWarning: coroutine 'FakeWebSocket.close' was never awaited
    websocket.close(code=1008, reason="Blocked by Halo egress policy")
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ===========================
FAILED tests/unit/test_retrieval_regressions.py::test_github_public_fallback_continues_with_its_own_cursor
FAILED tests/unit/test_retrieval_regressions.py::test_local_target_path_cannot_escape_its_prefix[/research/../admin]
FAILED tests/unit/test_retrieval_regressions.py::test_local_target_path_cannot_escape_its_prefix[/research/%2e%2e/admin]
FAILED tests/unit/test_retrieval_regressions.py::test_local_target_path_cannot_escape_its_prefix[/research/%252e%252e/admin]
FAILED tests/unit/test_retrieval_regressions.py::test_local_target_path_cannot_escape_its_prefix[/research/..\\admin]
FAILED tests/unit/test_retrieval_regressions.py::test_service_passes_exact_target_to_local_browser
FAILED tests/unit/test_browser_policy.py::test_local_crawl_uses_separate_operator_policy
FAILED tests/unit/test_browser_policy.py::test_public_websocket_to_loopback_is_blocked_before_connection
8 failed, 2 passed, 1 deselected, 1 warning in 1.12s
```

GREEN command:

```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/unit/test_retrieval_regressions.py tests/unit/test_browser_policy.py
```

```text
4 files reformatted, 64 files left unchanged
...........                                                              [100%]
11 passed in 0.99s
```

Full gate after code fixes: `137 passed in 4.54s`; `[GATE] PASS (Commit)`.

Explicit real-browser acceptance command:

```powershell
uv run --locked ruff format tests/acceptance/test_local_research_browser.py
uv run --locked python -m pytest -q tests/acceptance/test_local_research_browser.py
```

```text
1 file reformatted
.                                                                        [100%]
1 passed in 5.24s
```

This uses disposable loopback HTTP/WebSocket servers and an isolated Chrome
context through the actual Crawl4AI provider. Allowed dynamic content and socket
messages arrive; out-of-prefix HTTP, another port, POST, and out-of-prefix socket
requests do not reach the fixture servers. It uses no personal profile and is
not a replacement for live login, general provider, or DSH acceptance.
## GitHub discussion and ref checkpoint

Read and changed the GitHub provider, community adapter, related tests, README, changelog, and manual. Existing operator sign-in was used only in memory; no token, private repository content, connection, or changed scope was saved.

Baseline command: `uv run --locked python -m pytest -q tests/unit/test_github_provider.py tests/unit/test_transcript_community.py`.
Baseline: `19 passed in 1.45s` (after the initial support changes; original support RED below).

Initial support RED command: `uv run --locked python -m pytest -q tests/unit/test_github_provider.py`.

```text
See prior execution record; not available in persistent tool store.
```

Falsification RED command: `uv run --locked python -m pytest -q tests/unit/test_github_provider.py -k 'nested_replies or actual_size'`.

```text
FF                                                                       [100%]
================================== FAILURES ===================================
______ test_discussion_follows_nested_replies_within_total_reply_budget _______

    @pytest.mark.asyncio
    async def test_discussion_follows_nested_replies_within_total_reply_budget():
        calls = []
    
        def reply(number):
            return {"id": f"R{number}", "url": f"https://github.com/acme/widgets/discussions/7#discussioncomment-{number}", "bodyText": f"Evidence {number}"}
    
        async def request(method, path, headers, body):
            calls.append(body)
            if body["variables"].get("id"):
                assert body["variables"] == {"id": "C1", "after": "cursor-1", "limit": 2}
                return {"data": {"node": {"replies": {"nodes": [reply(2), reply(3)], "pageInfo": {"hasNextPage": False}}}}}
            return {"data": {"repository": {"discussion": {
                "url": "https://github.com/acme/widgets/discussions/7", "bodyText": "Root",
                "comments": {"nodes": [{"id": "C1", "url": "https://github.com/acme/widgets/discussions/7#discussioncomment-0", "bodyText": "Parent",
                    "replies": {"nodes": [reply(1)], "pageInfo": {"hasNextPage": True, "endCursor": "cursor-1"}}}], "pageInfo": {"hasNextPage": False}},
            }}}}
    
        provider = GitHubProvider(Connections({"token": "fixture-token"}), FixedClock(), request)
        result = await provider.discussion_thread("acme/widgets", 7, 4)
>       assert [item.content for item in result.items] == ["Root", "Parent", "Evidence 1", "Evidence 2", "Evidence 3"]
E       AssertionError: assert ['Root', 'Par... 'Evidence 1'] == ['Root', 'Par... 'Evidence 3']
E         
E         Right contains 2 more items, first extra item: 'Evidence 2'
E         Use -v to get more diff

tests\unit\test_github_provider.py:359: AssertionError
______ test_ref_blob_actual_size_is_checked_even_when_tree_size_is_wrong ______

    @pytest.mark.asyncio
    async def test_ref_blob_actual_size_is_checked_even_when_tree_size_is_wrong():
        async def request(method, path, headers, body):
            if "/commits/" in path:
                return {"sha": "a" * 40, "commit": {"tree": {"sha": "b" * 40}}}
            if "/git/trees/" in path:
                return {"tree": [{"type": "blob", "path": "README.md", "sha": "c" * 40, "size": 1}]}
            return {"encoding": "base64", "content": base64.b64encode(b"x" * 250_001).decode()}
    
        result = await GitHubProvider(Connections({"token": "fixture-token"}), FixedClock(), request).research("README", "acme/widgets", ["docs"], "main", 1)
>       assert result.items == []
E       AssertionError: assert [EvidenceItem...ef': 'main'})] == []
E         
E         Left contains one more item: EvidenceItem(url='https://github.com/acme/widgets/blob/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/README.md', retrieved_...a': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'blob_sha': 'cccccccccccccccccccccccccccccccccccccccc', 'ref': 'main'})
E         Use -v to get more diff

tests\unit\test_github_provider.py:374: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_github_provider.py::test_discussion_follows_nested_replies_within_total_reply_budget
FAILED tests/unit/test_github_provider.py::test_ref_blob_actual_size_is_checked_even_when_tree_size_is_wrong
2 failed, 10 deselected in 1.00s

```

GREEN commands:

```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/unit/test_github_provider.py tests/unit/test_transcript_community.py
```

```text
1 file reformatted, 69 files left unchanged
.....................                                                    [100%]
21 passed in 1.39s
```

Live command: `uv run --locked python tests/acceptance/github_live.py` (preceded by `uv run --locked ruff format tests/acceptance/github_live.py`).

```text
1 file reformatted
{"discussion_search": {"provider": "github-api", "urls": ["https://github.com/deepseek-ai/deepseek-harness/discussions/1468", "https://github.com/lfnovo/open-notebook/discussions/1243"], "warnings": ["GITHUB_RESULTS_LIMIT_REACHED"]}}
{"discussion_thread": {"items": 2, "urls": ["https://github.com/deepseek-ai/deepseek-harness/discussions/1468", "https://github.com/deepseek-ai/deepseek-harness/discussions/1468#discussioncomment-18036509"], "warnings": []}}
{"ref_pinned_docs": {"url": "https://github.com/microsoft/playwright/blob/855c734916c244533748f1b4dbfa6e231329ea54/README.md", "sha": "855c734916c244533748f1b4dbfa6e231329ea54", "chars": 11261, "warnings": ["GITHUB_REF_LITERAL_SEARCH", "GITHUB_REF_SCAN_LIMIT_REACHED"]}}
Authenticated GitHub read-only canary PASS

```

The live canary uses authenticated GitHub APIs against public sources, not a connected production Gateway account or DSH. HTTP reads and constant GraphQL queries only; no GitHub mutation. Ref scanning has explicit limits; this does not claim exhaustive repository search. No dependency added. Transport response-byte and total-duration limits remain part of the broader reliability work.

First full-gate attempt found the following canary lint error (no tests ran):

```text
ASYNC221 Async functions should not run processes with blocking methods
  --> tests\acceptance\github_live.py:15:18
   |
14 | async def main():
15 |     credential = subprocess.run(
   |                  ^^^^^^^^^^^^^^
16 |         ["gh", "auth", "token", "--hostname", "github.com"], capture_output=True, text=True, check=False
17 |     )
   |

Found 1 error.
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | lint failed with exit code 1
```

Moved the existing keyring subprocess read to `asyncio.to_thread`; no authentication behavior changed. Reran `uv run --locked ruff format tests/acceptance/github_live.py`, `pwsh -NoProfile -File scripts/Update-BuildManifest.ps1`, and `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`:

```text
1 file left unchanged
Wrote BUILD-MANIFEST.json with 192 files.
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
70 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 50%]
.......................................................................  [100%]
143 passed in 5.52s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```
