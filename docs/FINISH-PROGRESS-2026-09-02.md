# Research-only completion work — 2026-09-02

This tracks Scott's full six-part completion goal. No partial checkpoint closes
the goal. The research-only scope remains unchanged.

| Requirement | Current evidence/status |
| --- | --- |
| GitHub fallback pagination | Fixed with a full normalized snapshot and GitHub-bound cursor; regression passes without a second upstream request. |
| Local browser requests | Exact target is passed into immutable per-context guards; host/port/path/method checks and decoded traversal rejection added. Real Chrome fixture passed. |
| WebSocket handling | Async close is awaited; allowed local socket returns evidence and forbidden socket never reaches the server in real Chrome. |
| GitHub discussions and ref support | Pending implementation and source-specific proof. |
| All research source tools and authenticated GitHub | Pending complete live evidence matrix. |
| Research login/challenge/optional providers | Pending implementation/verification; user asked to select a dedicated research profile/site. No paid calls authorized. |
| Full DSH workflow and durable-job controls | Pending end-to-end evidence. |
| Reliability and installation | Existing unit coverage is not full acceptance; startup discrepancy, broader concurrency/process/recovery/install tests remain. |
| Delivery | Prior removal commits local; push/CI/merge and corrected hosted-page publication remain. Authorized by the full finish request. |

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
