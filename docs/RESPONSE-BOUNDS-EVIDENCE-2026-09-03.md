# Research response bounds — September 3, 2026

## Outcome and identity

Source checkpoint based on clean main `07c68aa4444177fa83b1f08287937441933b4351`.
Product remains 0.2.0; fourteen research tools, no account-action additions.

Local fetch and the default GitHub API requester previously buffered entire
responses. GitHub used per-I/O timeouts rather than a deadline covering DNS and
the response. Local fetch bypassed shared HTTP admission and origin pacing.

Both now stream with `http.max_decompressed_bytes` (default 20 MiB) and active
request timeouts from `http.total_timeout_seconds` (default 30 seconds). GitHub
DNS is included; local origin waiting is included. Shared-queue waiting is not.
Checks reject an overflowing decoded chunk before appending it to the retained
body, close the response and return an explicit error rather than partial evidence.
GitHub accepts JSON objects or arrays and returns a controlled invalid-response
error for malformed/other JSON values. Local redirects are denied before reading
their bodies. Public GitHub URL/DNS pinning and no-redirect policy are unchanged.

Local reads now share the existing HTTP coordinator and origin gate. Singleflight
keys hash the exact target name and URL, not raw private paths. Cursor continuation
does not fetch again; no local or authenticated disk cache is introduced.

## What was actually proved

Baseline: `423 passed in 79.38s (0:01:19)`.
Eighteen new unit cases; final gate: `441 passed in 80.40s (0:01:20)`.
Nine response assertions and two queue/origin assertions failed before their
corresponding fixes. No existing test was weakened, skipped or deleted.

Focused checks cover oversized decoded chunks, unread remainder, gzip inflation,
slow streams, DNS deadline, malformed/scalar JSON, exact local byte boundary,
normal JSON objects/arrays, shared admission saturation/recovery, origin gate use,
caller cancellation, and local redirect rejection without body/destination access.

Native check: a separate Windows Gateway process on a disposable port/state,
two actual network MCP clients and a loopback source. It preserved 3200 characters
across 12 pages, initially admitted one concurrent source request, rejected
oversize/compressed/redirect/timeout cases, then returned subsequent evidence.
Cache remained empty and shared HTTP pending returned to zero.
A separate real unauthenticated api.github.com/rate_limit check rejected its
response under a one-byte test limit, then decoded normal JSON under the normal cap.
Native result: `2 passed in 5.29s`.

The first queue implementation used the wrong LocalTarget field; three tests
caught it. Fixed `name` to existing `target_id` without changing assertions.
The first native fixture used the wrong statistics path; corrected its lookup
from providers.http to queues.http after inspecting the actual service.
The first full gate stopped on test import ordering; sorted imports and reran.
All failures and warnings remain below, not counted as successful evidence.

## Deployment and remaining limitations

This is a source-only checkpoint. No installed Gateway or DSH restart, scheduler
repair, account connection, cookie import, paid API call, config edit, scope-copy
overwrite, Site deployment, package release or version bump was performed.
Installed runtime remains the prior 7cdfe72 checkpoint until a verified reload;
the owner-only published Site v4 intentionally still describes that runtime.
CI/commit/delivery identity belongs in the later operator delivery receipt.

These are decoded retained-body and cooperative asynchronous I/O bounds, not
compressed-wire, decompressor, JSON object allocation, native peak-memory or
uninterruptible-cleanup guarantees. A decoded chunk exists before checking its
size. JSON parsing/encoding is synchronous after the request. Complete GitHub
research can make multiple individually bounded API requests; there is no new
whole-operation deadline or total-response-byte budget. GitHub/community origin
pacing is not added by this repair. Direct public HTTP overall deadlines and
other source-provider/resource limits remain separate work.

Existing local_fetch also does not enforce a configured HEAD-only methods list
and returns its source URL without the public reader's sensitive-query redaction.
These pre-existing adjacent policy gaps were noticed during review and are not
fixed by the response-bound change. No personal URLs were used in evidence.

DSH dispatch repair/restart still needs Scott's decision. Full DSH research/job
workflow, chosen real login/profile, human challenge handoff, solver token
application, app-bound cookies, broad stress/installation, metadata/licensing and
final delivery acceptance remain open. This checkpoint does not finish the goal.

## Verification and security review

Read before changing: GitHub requester/call sites, HaloService construction and
local reader/error/stats paths, HTTP transport/origin gate, Coordinator, local
target/config models, existing unit/native test patterns, quality/build-manifest
scripts, and current scope/README/manual/operations/progress documentation.
Blast radius: default GitHub REST/GraphQL/token responses and local source reads;
requester injection, tool schemas, browser paths and DSH settings are unchanged.

- Trust-boundary checks: existing named-target validation/public GitHub URL/DNS
  checks retained; decoded byte limits and controlled JSON failures added.
- New endpoints/authn/authz: none; fourteen tools and existing operator routes.
- Secrets: no account credential used in this turn; fixture values are synthetic.
  Errors do not include response bodies. No local-source content goes to disk cache.
- Unsafe rendering/eval/deserialization: no new rendering or executable content;
  bounded JSON parsing only, not pickle/eval.
- Dependencies: none added or changed. Existing metadata constraints are unfinished.
- Performance: per-request streaming avoids collecting complete oversized bodies;
  local queue/origin limits intentionally serialize/pace according to existing config.
- Self-falsification only, not independent review: edge/error/cancel paths above;
  native fixture is not proof of installed service/real authenticated GitHub/DSH.
- Documentation: README, CHANGELOG, manual, operations, current scope/progress/status
  updated; raw evidence below. Existing historical receipts remain unchanged.

## Exact commands and full recorded output

### Documentation synchronization caught by the commit hook

The full code gate above preceded the finish-list edit. The later commit hook
correctly rejected the missed repository-bundled scope copy. No commit or push
occurred from that attempt. Synchronize only the repository copy; previously
denied installed copies remain untouched. The subsequent successful commit/CI
receipts are recorded in the operator delivery document.

```powershell
$taskEvidence=Join-Path (Get-Location) 'docs/RESPONSE-BOUNDS-EVIDENCE-2026-09-03.md'
$taskText=(Get-Content -LiteralPath $taskEvidence -Raw).TrimEnd()+"`n"
[System.IO.File]::WriteAllText($taskEvidence,$taskText,[System.Text.UTF8Encoding]::new($false))
$env:GIT_CONFIG_COUNT='1'
$env:GIT_CONFIG_KEY_0='safe.directory'
$env:GIT_CONFIG_VALUE_0='C:/Users/scott/Desktop/Code/halo-research-gateway'
pwsh -NoProfile -File scripts/Update-BuildManifest.ps1
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway add -- BUILD-MANIFEST.json docs/RESPONSE-BOUNDS-EVIDENCE-2026-09-03.md
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway diff --cached --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway commit -m "Bound research HTTP responses and share local fetch admission"
```

```text
Wrote BUILD-MANIFEST.json with 246 files.
warning: in the working copy of 'docs/RESPONSE-BOUNDS-EVIDENCE-2026-09-03.md', LF will be replaced by CRLF the next time Git touches it
[GATE] lock check
Resolved 130 packages in 2ms
[GATE] format
104 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 16%]
........................................................................ [ 32%]
........................................................................ [ 48%]
........................................................................ [ 65%]
........................................................................ [ 81%]
........................................................................ [ 97%]
.........                                                                [100%]
441 passed in 84.69s (0:01:24)
[GATE] skill package
skill-bundled research-only scope differs from current contract
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | skill package failed with exit code 1
```


### Unchanged baseline

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 2ms
[GATE] format
102 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 17%]
........................................................................ [ 34%]
........................................................................ [ 51%]
........................................................................ [ 68%]
........................................................................ [ 85%]
...............................................................          [100%]
423 passed in 79.38s (0:01:19)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

### Assertion-based response RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_research_response_bounds.py
```

```text
FFFFFFFFF....                                                            [100%]
================================== FAILURES ===================================
___________ test_overflow_stops_before_next_chunk_and_closes[local] ___________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D2117800>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D1E25F70>
kind = 'local'

    @pytest.mark.parametrize("kind", ["local", "github"])
    async def test_overflow_stops_before_next_chunk_and_closes(monkeypatch, service, kind):
        stream = Payload([b"x" * 65, b"must not be read"])
        install(monkeypatch, stream)
        if kind == "local":
            result = await service.local_fetch("fixture", "/research/source")
>           assert not result["ok"] and result["error"]["code"] == "LOCAL_RESPONSE_TOO_LARGE"
E           assert (not True)

tests\unit\test_research_response_bounds.py:77: AssertionError
__________ test_overflow_stops_before_next_chunk_and_closes[github] ___________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D21178F0>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D2142870>
kind = 'github'

    @pytest.mark.parametrize("kind", ["local", "github"])
    async def test_overflow_stops_before_next_chunk_and_closes(monkeypatch, service, kind):
        stream = Payload([b"x" * 65, b"must not be read"])
        install(monkeypatch, stream)
        if kind == "local":
            result = await service.local_fetch("fixture", "/research/source")
            assert not result["ok"] and result["error"]["code"] == "LOCAL_RESPONSE_TOO_LARGE"
        else:
            error = None
            try:
                await service.github._request_json("GET", "/search/issues", {}, None)
            except Exception as exc:
                error = exc
>           assert isinstance(error, ValueError) and str(error) == "GITHUB_RESPONSE_TOO_LARGE"
E           AssertionError: assert (True and 'Expecting va...mn 1 (char 0)' == 'GITHUB_RESPONSE_TOO_LARGE'
E            +  where True = isinstance(JSONDecodeError('Expecting value: line 1 column 1 (char 0)'), ValueError)
E
E             - GITHUB_RESPONSE_TOO_LARGE
E             + Expecting value: line 1 column 1 (char 0))

tests\unit\test_research_response_bounds.py:84: AssertionError
__________ test_compressed_response_is_limited_after_decoding[local] __________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D2143DA0>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D2142B40>
kind = 'local'

    @pytest.mark.parametrize("kind", ["local", "github"])
    async def test_compressed_response_is_limited_after_decoding(monkeypatch, service, kind):
        stream = Payload([gzip.compress(b'"' + b"x" * 1000 + b'"')])
        install(monkeypatch, stream, {"content-encoding": "gzip"})
        if kind == "local":
            result = await service.local_fetch("fixture", "/research/source")
>           assert not result["ok"] and result["error"]["code"] == "LOCAL_RESPONSE_TOO_LARGE"
E           assert (not True)

tests\unit\test_research_response_bounds.py:94: AssertionError
_________ test_compressed_response_is_limited_after_decoding[github] __________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D2143410>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D2143350>
kind = 'github'

    @pytest.mark.parametrize("kind", ["local", "github"])
    async def test_compressed_response_is_limited_after_decoding(monkeypatch, service, kind):
        stream = Payload([gzip.compress(b'"' + b"x" * 1000 + b'"')])
        install(monkeypatch, stream, {"content-encoding": "gzip"})
        if kind == "local":
            result = await service.local_fetch("fixture", "/research/source")
            assert not result["ok"] and result["error"]["code"] == "LOCAL_RESPONSE_TOO_LARGE"
        else:
            error = None
            try:
                await service.github._request_json("GET", "/search/issues", {}, None)
            except Exception as exc:
                error = exc
>           assert isinstance(error, ValueError) and str(error) == "GITHUB_RESPONSE_TOO_LARGE"
E           assert (False)
E            +  where False = isinstance(None, ValueError)

tests\unit\test_research_response_bounds.py:101: AssertionError
_______________ test_total_deadline_stops_slow_response[local] ________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D21439E0>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D21F7C20>
kind = 'local'

    @pytest.mark.parametrize("kind", ["local", "github"])
    async def test_total_deadline_stops_slow_response(monkeypatch, service, kind):
        stream = Payload([b"{}"], delay=0.1)
        install(monkeypatch, stream)
        if kind == "local":
            service.config.http.total_timeout_seconds = 0.02
            result = await service.local_fetch("fixture", "/research/source")
>           assert not result["ok"] and result["error"]["code"] == "LOCAL_REQUEST_TIMEOUT"
E           assert (not True)

tests\unit\test_research_response_bounds.py:112: AssertionError
_______________ test_total_deadline_stops_slow_response[github] _______________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D21F5A30>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D21F5970>
kind = 'github'

    @pytest.mark.parametrize("kind", ["local", "github"])
    async def test_total_deadline_stops_slow_response(monkeypatch, service, kind):
        stream = Payload([b"{}"], delay=0.1)
        install(monkeypatch, stream)
        if kind == "local":
            service.config.http.total_timeout_seconds = 0.02
            result = await service.local_fetch("fixture", "/research/source")
            assert not result["ok"] and result["error"]["code"] == "LOCAL_REQUEST_TIMEOUT"
        else:
            service.github.timeout_seconds = 0.02
            error = None
            try:
                await service.github._request_json("GET", "/search/issues", {}, None)
            except Exception as exc:
                error = exc
>           assert isinstance(error, TimeoutError) and str(error) == "GITHUB_REQUEST_TIMEOUT"
E           assert (False)
E            +  where False = isinstance(None, TimeoutError)

tests\unit\test_research_response_bounds.py:120: AssertionError
______________________ test_github_deadline_includes_dns ______________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D21437D0>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D21433B0>

    async def test_github_deadline_includes_dns(monkeypatch, service):
        stream = Payload([b"{}"])
        calls = install(monkeypatch, stream)

        async def slow_dns(target):
            await asyncio.sleep(0.1)
            return "93.184.216.34"

        monkeypatch.setattr(github, "resolve_public", slow_dns)
        service.github.timeout_seconds = 0.02
        error = None
        try:
            await service.github._request_json("GET", "/search/issues", {}, None)
        except Exception as exc:
            error = exc
>       assert isinstance(error, TimeoutError) and str(error) == "GITHUB_REQUEST_TIMEOUT"
E       assert (False)
E        +  where False = isinstance(None, TimeoutError)

tests\unit\test_research_response_bounds.py:139: AssertionError
___ test_github_rejects_invalid_json_shape_without_body["fixture-private"] ____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D2142DE0>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D21415B0>
body = b'"fixture-private"'

    @pytest.mark.parametrize("body", [b'"fixture-private"', b'{"secret":"fixture-private"'])
    async def test_github_rejects_invalid_json_shape_without_body(monkeypatch, service, body):
        stream = Payload([body])
        install(monkeypatch, stream)
        error = None
        try:
            await service.github._request_json("GET", "/search/issues", {}, None)
        except Exception as exc:
            error = exc
>       assert isinstance(error, ValueError) and str(error) == "GITHUB_RESPONSE_INVALID"
E       assert (False)
E        +  where False = isinstance(None, ValueError)

tests\unit\test_research_response_bounds.py:152: AssertionError
_ test_github_rejects_invalid_json_shape_without_body[{"secret":"fixture-private"] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001D6D2140BC0>
service = <halo_research_gateway.service.HaloService object at 0x000001D6D21424E0>
body = b'{"secret":"fixture-private"'

    @pytest.mark.parametrize("body", [b'"fixture-private"', b'{"secret":"fixture-private"'])
    async def test_github_rejects_invalid_json_shape_without_body(monkeypatch, service, body):
        stream = Payload([body])
        install(monkeypatch, stream)
        error = None
        try:
            await service.github._request_json("GET", "/search/issues", {}, None)
        except Exception as exc:
            error = exc
>       assert isinstance(error, ValueError) and str(error) == "GITHUB_RESPONSE_INVALID"
E       assert (True and "Expecting ',... 28 (char 27)" == 'GITHUB_RESPONSE_INVALID'
E        +  where True = isinstance(JSONDecodeError("Expecting ',' delimiter: line 1 column 28 (char 27)"), ValueError)
E
E         - GITHUB_RESPONSE_INVALID
E         + Expecting ',' delimiter: line 1 column 28 (char 27))

tests\unit\test_research_response_bounds.py:152: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_research_response_bounds.py::test_overflow_stops_before_next_chunk_and_closes[local]
FAILED tests/unit/test_research_response_bounds.py::test_overflow_stops_before_next_chunk_and_closes[github]
FAILED tests/unit/test_research_response_bounds.py::test_compressed_response_is_limited_after_decoding[local]
FAILED tests/unit/test_research_response_bounds.py::test_compressed_response_is_limited_after_decoding[github]
FAILED tests/unit/test_research_response_bounds.py::test_total_deadline_stops_slow_response[local]
FAILED tests/unit/test_research_response_bounds.py::test_total_deadline_stops_slow_response[github]
FAILED tests/unit/test_research_response_bounds.py::test_github_deadline_includes_dns
FAILED tests/unit/test_research_response_bounds.py::test_github_rejects_invalid_json_shape_without_body["fixture-private"]
FAILED tests/unit/test_research_response_bounds.py::test_github_rejects_invalid_json_shape_without_body[{"secret":"fixture-private"]
9 failed, 4 passed in 2.71s
```

### Initial response GREEN

```powershell
uv run --locked python -m pytest -q tests/unit/test_research_response_bounds.py tests/unit/test_github_provider.py tests/unit/test_retrieval_regressions.py
```

```text
..................................                                       [100%]
34 passed in 2.27s
```

### Assertion-based shared-queue RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_research_response_bounds.py
```

```text
.............FF...                                                       [100%]
================================== FAILURES ===================================
_________________ test_local_read_obeys_shared_http_admission _________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001B427A21280>
service = <halo_research_gateway.service.HaloService object at 0x000001B427A22900>

    async def test_local_read_obeys_shared_http_admission(monkeypatch, service):
        stream = Payload([b"evidence"])
        calls = install(monkeypatch, stream)
        service.coordinator.policies["http"] = QueuePolicy(1, 1, 1, 0)
        started, release = asyncio.Event(), asyncio.Event()

        async def occupied():
            started.set()
            await release.wait()

        task = asyncio.create_task(service.coordinator.run("http", "other-client", "occupied", occupied))
        try:
            await started.wait()
            result = await service.local_fetch("fixture", "/research/source", client="local-client")
>           assert not result["ok"] and result["error"]["code"] == "QUEUE_FULL"
E           assert (not True)

tests\unit\test_research_response_bounds.py:184: AssertionError
_________________ test_local_read_uses_the_shared_origin_gate _________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001B427A21220>
service = <halo_research_gateway.service.HaloService object at 0x000001B427A23D70>

    async def test_local_read_uses_the_shared_origin_gate(monkeypatch, service):
        stream = Payload([b"evidence"])
        install(monkeypatch, stream)
        origins = []

        @asynccontextmanager
        async def gate(target):
            origins.append((target.scheme, target.host, target.port))
            yield

        monkeypatch.setattr(service.http, "_origin_gate", gate)
        result = await service.local_fetch("fixture", "/research/source")
        assert result["ok"]
>       assert origins == [("http", "127.0.0.1", 3090)]
E       AssertionError: assert [] == [('http', '127.0.0.1', 3090)]
E
E         Right contains one more item: ('http', '127.0.0.1', 3090)
E         Use -v to get more diff

tests\unit\test_research_response_bounds.py:206: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_research_response_bounds.py::test_local_read_obeys_shared_http_admission
FAILED tests/unit/test_research_response_bounds.py::test_local_read_uses_the_shared_origin_gate
2 failed, 16 passed in 1.94s
```

### Implementation mistake caught by unchanged new tests

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/github.py src/halo_research_gateway/service.py tests/unit/test_research_response_bounds.py
uv run --locked python -m pytest -q tests/unit/test_research_response_bounds.py tests/unit/test_github_provider.py tests/unit/test_retrieval_regressions.py
```

```text
1 file reformatted, 2 files left unchanged
............FFF........................                                  [100%]
================================== FAILURES ===================================
_ test_exact_cap_and_normal_evidence_remain_readable["xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"] _

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001A0ECE83560>
service = <halo_research_gateway.service.HaloService object at 0x000001A0ECE82330>
body = b'"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"'

    @pytest.mark.parametrize("body", [b"{}", b"[]", b'{"ok":true}', b'"' + b"x" * 62 + b'"'])
    async def test_exact_cap_and_normal_evidence_remain_readable(monkeypatch, service, body):
        stream = Payload([body[:1], body[1:]])
        install(monkeypatch, stream)
        if body.startswith(b'"'):
            result = await service.local_fetch("fixture", "/research/source")
>           assert result["ok"] and result["items"][0]["content"] == body.decode()
E           assert (False)

tests\unit\test_research_response_bounds.py:164: AssertionError
_________________ test_local_read_obeys_shared_http_admission _________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001A0ECE4F320>
service = <halo_research_gateway.service.HaloService object at 0x000001A0ECEB4530>

    async def test_local_read_obeys_shared_http_admission(monkeypatch, service):
        stream = Payload([b"evidence"])
        calls = install(monkeypatch, stream)
        service.coordinator.policies["http"] = QueuePolicy(1, 1, 1, 0)
        started, release = asyncio.Event(), asyncio.Event()

        async def occupied():
            started.set()
            await release.wait()

        task = asyncio.create_task(service.coordinator.run("http", "other-client", "occupied", occupied))
        try:
            await started.wait()
            result = await service.local_fetch("fixture", "/research/source", client="local-client")
            assert not result["ok"] and result["error"]["code"] == "QUEUE_FULL"
            assert calls == []
        finally:
            release.set()
            await task
        result = await service.local_fetch("fixture", "/research/source", client="local-client")
>       assert result["ok"] and len(calls) == 1
E       assert (False)

tests\unit\test_research_response_bounds.py:190: AssertionError
_________________ test_local_read_uses_the_shared_origin_gate _________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001A0ECEB7EC0>
service = <halo_research_gateway.service.HaloService object at 0x000001A0ECEB4C20>

    async def test_local_read_uses_the_shared_origin_gate(monkeypatch, service):
        stream = Payload([b"evidence"])
        install(monkeypatch, stream)
        origins = []

        @asynccontextmanager
        async def gate(target):
            origins.append((target.scheme, target.host, target.port))
            yield

        monkeypatch.setattr(service.http, "_origin_gate", gate)
        result = await service.local_fetch("fixture", "/research/source")
>       assert result["ok"]
E       assert False

tests\unit\test_research_response_bounds.py:205: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_research_response_bounds.py::test_exact_cap_and_normal_evidence_remain_readable["xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"]
FAILED tests/unit/test_research_response_bounds.py::test_local_read_obeys_shared_http_admission
FAILED tests/unit/test_research_response_bounds.py::test_local_read_uses_the_shared_origin_gate
3 failed, 36 passed in 3.06s
```

### Corrected target identifier GREEN

```powershell
uv run --locked python -m pytest -q tests/unit/test_research_response_bounds.py tests/unit/test_github_provider.py tests/unit/test_retrieval_regressions.py
```

```text
.......................................                                  [100%]
39 passed in 2.68s
```

### Native fixture diagnostic-path mistake

```powershell
uv run --locked ruff format tests/acceptance/test_response_bounds_native.py
uv run --locked python -m pytest -q -s tests/acceptance/test_response_bounds_native.py
```

```text
1 file left unchanged
F
================================== FAILURES ===================================
___________ test_native_local_bounds_queue_pagination_and_recovery ____________
  + Exception Group Traceback (most recent call last):
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_response_bounds_native.py", line 92, in test_native_local_bounds_queue_pagination_and_recovery
  |     async with mcp_at(port) as first, mcp_at(port) as second:
  |                ^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 231, in __aexit__
  |     await self.gen.athrow(value)
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_result_retention_native.py", line 23, in mcp_at
  |     async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
  |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 231, in __aexit__
  |     await self.gen.athrow(value)
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 688, in streamable_http_client
  |     anyio.create_task_group() as tg,
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
  |     raise BaseExceptionGroup(
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Exception Group Traceback (most recent call last):
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 705, in streamable_http_client
    |     yield read_stream, write_stream
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_result_retention_native.py", line 24, in mcp_at
    |     async with ClientSession(streams[0], streams[1]) as session:
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\session.py", line 521, in __aexit__
    |     result = await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
    |     raise BaseExceptionGroup(
    | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
    +-+---------------- 1 ----------------
      | Exception Group Traceback (most recent call last):
      |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_result_retention_native.py", line 26, in mcp_at
      |     yield session
      |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_response_bounds_native.py", line 92, in test_native_local_bounds_queue_pagination_and_recovery
      |     async with mcp_at(port) as first, mcp_at(port) as second:
      |                                       ^^^^^^^^^^^^
      |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 231, in __aexit__
      |     await self.gen.athrow(value)
      |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_result_retention_native.py", line 23, in mcp_at
      |     async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
      |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 231, in __aexit__
      |     await self.gen.athrow(value)
      |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 688, in streamable_http_client
      |     anyio.create_task_group() as tg,
      |     ^^^^^^^^^^^^^^^^^^^^^^^^^
      |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
      |     raise BaseExceptionGroup(
      | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
      +-+---------------- 1 ----------------
        | Exception Group Traceback (most recent call last):
        |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 705, in streamable_http_client
        |     yield read_stream, write_stream
        |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_result_retention_native.py", line 24, in mcp_at
        |     async with ClientSession(streams[0], streams[1]) as session:
        |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\session.py", line 521, in __aexit__
        |     result = await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
        |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
        |     raise BaseExceptionGroup(
        | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
        +-+---------------- 1 ----------------
          | Traceback (most recent call last):
          |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_result_retention_native.py", line 26, in mcp_at
          |     yield session
          |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_response_bounds_native.py", line 122, in test_native_local_bounds_queue_pagination_and_recovery
          |     assert stats["providers"]["http"]["pending"] == 0
          |            ~~~~~~~~~~~~~~~~~~^^^^^^^^
          | KeyError: 'http'
          +------------------------------------
=========================== short test summary info ===========================
FAILED tests/acceptance/test_response_bounds_native.py::test_native_local_bounds_queue_pagination_and_recovery
1 failed in 4.54s
```

### Corrected native fixture and real public GitHub

```powershell
uv run --locked ruff format tests/acceptance/test_response_bounds_native.py
uv run --locked python -m pytest -q -s tests/acceptance/test_response_bounds_native.py
```

```text
1 file left unchanged
NATIVE local bounds: two MCP clients; 3200 characters/12 pages; initial source peak=1; overflow/compression/redirect/timeout rejected; subsequent read passed; cache entries=0; HTTP pending=0.
.NATIVE public GitHub: one-byte cap rejected real API response; normal-cap followup decoded resources.
.
2 passed in 5.29s
```

### First full gate stopped on import ordering

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
104 files already formatted
[GATE] lint
I001 [*] Import block is un-sorted or un-formatted
  --> tests\acceptance\test_response_bounds_native.py:6:1
   |
 4 |   """
 5 |
 6 | / import asyncio
 7 | | import os
 8 | | import socket
 9 | | import subprocess
10 | | import sys
11 | |
12 | | import httpx
13 | | import pytest
14 | | from aiohttp import web
15 | |
16 | | from halo_research_gateway.providers.github import GitHubProvider
17 | |
18 | | from test_result_retention_native import mcp_at, read
   | |_____________________________________________________^
help: Organize imports
   |
14 | from aiohttp import web
15 + from test_result_retention_native import mcp_at, read
16 |
17 | from halo_research_gateway.providers.github import GitHubProvider
   -
   - from test_result_retention_native import mcp_at, read
18 |
   |

Found 1 error.
[*] 1 fixable with the `--fix` option.
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | lint failed with exit code 1
```

### Final full gate

```powershell
uv run --locked ruff check --select I --fix tests/acceptance/test_response_bounds_native.py
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
Found 1 error (1 fixed, 0 remaining).
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
104 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 16%]
........................................................................ [ 32%]
........................................................................ [ 48%]
........................................................................ [ 65%]
........................................................................ [ 81%]
........................................................................ [ 97%]
.........                                                                [100%]
441 passed in 80.40s (0:01:20)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```
