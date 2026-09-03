# Compact cursor evidence — 2026-09-03

## Outcome and scope

Source/native checkpoint, not full project acceptance. Normally emitted cursors
are now 51 characters instead of the 332–346 characters seen in two failed DSH
runs. A six-case failing regression suite preceded implementation. The full gate
now passes 490 tests. Real native local MCP preserves all fixture text across
two clients and correctly rejects evicted/private-after-restart references. A
public transcript preserves identical 783-character text and 14 timing records
at every supported page budget and after a new native process/client starts.

No installed Gateway reload, new DSH workflow pass, push, merge or release is
claimed by this source checkpoint. Version stays 0.2.0; final target is 0.3.0.
See DSH-RESOLUTION-EVIDENCE-2026-09-03.md for the preceding model failures.

## Decision and implementation

Choices: keep long tokens; alter DSH model/context; shorten opaque authenticated
references. Recommendation followed: shorten references, preserving validation,
source identity and existing cache policy. No new tool, external action,
dependency, database migration, DSH configuration or permission change.

The h1 transport contains an eight-byte expiry, a domain-separated keyed
12-byte state identity, and a 16-byte HMAC-SHA256 tag. It authenticates before
lookup and binds the recovered full signed layout-3 state afterward. The original
state still carries tool, output budget, page position and immutable evidence
SHA-256. No source URL/content is exposed in the short reference. Key file and
legacy signed-state verification are unchanged.

Envelope fitting stages candidates but retains only the returned handle.
Memory metadata has separate count/byte/idle bounds using the existing snapshot
settings; stats expose counts, not tokens or evidence. Public metadata shares
the existing bounded cache; private metadata is never persisted. If metadata
cannot fit, the response is refitted using the original signed inline cursor.
Combined retained metadata/evidence pools can reach twice the snapshot byte cap.
Disk entries include reference metadata; cache pressure/expiry can evict them.
The pre-admission capacity check avoids displacing evidence in the ordinary
single-owner path, not a cross-process no-eviction guarantee. Existing shared
cache limits still enforce atomic total capacity.

## Files read, blast radius and falsification

Read cursor codec, service paging/cache/snapshot paths, envelope fitting, cache,
configuration, scope, unit cursor/retention/transcript tests, native acceptance
scripts, quality gate, lifecycle scripts and affected documentation before edits.

Fifteen compact-cursor tests cover full text, sizes, count/byte/idle caps, close,
private/public restart, tool/output binding, expiry, tampering, malformed encodings,
pre-lookup validation, substituted/non-ASCII/missing mappings, cache pressure,
one persisted fitting candidate, and usable legacy layout-3 cursors. Existing
immutable-source, snippet, Unicode, transcript and metadata-layout rejection
assertions remain. One old test's setup now constructs layout 2 explicitly instead
of assuming all new tokens contain inline JSON; its rejection assertions are
unchanged. The added non-ASCII mapping test exposed a wrong error classification;
it now returns CURSOR_INVALID instead of UPSTREAM_UNAVAILABLE.

No new auth route, unsafe evaluation or deserialization beyond existing JSON;
untrusted tokens are authenticated before disk lookup and recovered state is
revalidated. No new dependencies. Credentials/private source data are not part of
these fixtures. Credential-pattern scan and checkpoint identity are recorded by
the delivery receipt. This is self-review, not independent audit.

Known limits: Python/native peak memory, synchronous cache I/O, original provider
collection caps and wider goal gaps remain. Shorter tokens do not prove the local
model copies them correctly or produces a supported final answer. Required DSH
acceptance, jobs, real login/challenges and installation remain separate.

## Exact verification

Commands ran in C:/Users/scott/Desktop/Code/halo-research-gateway using the existing
locked environment. Raw outputs are retained locally in compact-cursor-verification.json.
The Markdown rendering represents trailing spaces literally as \\x20 so Git does
not treat native terminal padding as a source whitespace error. CR line endings
are normalized; failures, warnings and counts are otherwise retained.

### Baseline

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_cursor.py tests/unit/test_result_retention.py tests/unit/test_envelope.py
```

Output:

```text
........................................                                 [100%]
40 passed in 2.21s

```

### Initial RED

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_compact_cursor.py
```

Output:

```text
FFFFFF                                                                   [100%]
================================== FAILURES ===================================
____ test_model_cursor_is_short_and_continuation_keeps_all_evidence[False] ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2174/test_model_cursor_is_short_and0')
cached = False

    @pytest.mark.parametrize("cached", [False, True])
    async def test_model_cursor_is_short_and_continuation_keeps_all_evidence(tmp_path, cached):
        service = service_at(tmp_path)
        value = source()
        if cached:
            service._cache_result(value, "fixture-public", 3600)
        try:
            first = service._envelope("web_fetch", value, 2000)
            cursor = first["page"]["next_cursor"]
>           assert len(cursor) <= 64, "Local model should not have to copy a 300-character state document"
E           AssertionError: Local model should not have to copy a 300-character state document
E           assert 236 <= 64
E            +  where 236 = len('eyJiIjoyMDAwLCJjIjoyLCJleHAiOjE3ODg0Mjk1NTEsImkiOjIsImsiOiIiLCJuIjoyLCJzIjoiNmI2OTAyNDFhZjVjYjk4NGI3YzQyMzA3MTZlMTM4MWJkMDVjYWE2Y2Q3NzI4Nzg1YTUyZDY3MjAxMWU3YzU3ZCIsInQiOiJ3ZWJfZmV0Y2giLCJ2IjozfTt_8hLDamGAKKOhlcrxFTQMfZSHSAgweVdha3QRjSne')

tests\unit\test_compact_cursor.py:34: AssertionError
____ test_model_cursor_is_short_and_continuation_keeps_all_evidence[True] _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2174/test_model_cursor_is_short_and1')
cached = True

    @pytest.mark.parametrize("cached", [False, True])
    async def test_model_cursor_is_short_and_continuation_keeps_all_evidence(tmp_path, cached):
        service = service_at(tmp_path)
        value = source()
        if cached:
            service._cache_result(value, "fixture-public", 3600)
        try:
            first = service._envelope("web_fetch", value, 2000)
            cursor = first["page"]["next_cursor"]
>           assert len(cursor) <= 64, "Local model should not have to copy a 300-character state document"
E           AssertionError: Local model should not have to copy a 300-character state document
E           assert 255 <= 64
E            +  where 255 = len('eyJiIjoyMDAwLCJjIjoxLCJleHAiOjE3ODg0Mjk1NTIsImkiOjEsImsiOiJmaXh0dXJlLXB1YmxpYyIsIm4iOjIsInMiOiI2YjY5MDI0MWFmNWNiOTg0Y...mQwNWNhYTZjZDc3Mjg3ODVhNTJkNjcyMDExZTdjNTdkIiwidCI6IndlYl9mZXRjaCIsInYiOjN9rLWZYpDMSyMCHqshhTc8AQRpgYngyBKwBjHnMfZ-tjo')

tests\unit\test_compact_cursor.py:34: AssertionError
_____________ test_compact_cursor_metadata_is_bounded_and_visible _____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2174/test_compact_cursor_metadata_i0')

    async def test_compact_cursor_metadata_is_bounded_and_visible(tmp_path):
        service = service_at(tmp_path)
        service.config.output.snapshot_max_entries = 2
        try:
            cursors = [service._envelope("web_fetch", source(i), 2000)["page"]["next_cursor"] for i in range(3)]
            stats = service.stats().get("cursor_handles")
>           assert stats is not None, "Cursor lookup metadata needs visible bounds"
E           AssertionError: Cursor lookup metadata needs visible bounds
E           assert None is not None

tests\unit\test_compact_cursor.py:60: AssertionError
______ test_compact_cursor_restart_respects_original_cache_policy[False] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2174/test_compact_cursor_restart_re0')
cached = False

    @pytest.mark.parametrize("cached", [False, True])
    async def test_compact_cursor_restart_respects_original_cache_policy(tmp_path, cached):
        service = service_at(tmp_path)
        value = source()
        if cached:
            service._cache_result(value, "fixture-public", 3600)
        first = service._envelope("web_fetch", value, 2000)
        cursor = first["page"]["next_cursor"]
        await service.close()
>       assert len(cursor) <= 64
E       AssertionError: assert 236 <= 64
E        +  where 236 = len('eyJiIjoyMDAwLCJjIjoyLCJleHAiOjE3ODg0Mjk1NTIsImkiOjIsImsiOiIiLCJuIjoyLCJzIjoiNmI2OTAyNDFhZjVjYjk4NGI3YzQyMzA3MTZlMTM4MWJkMDVjYWE2Y2Q3NzI4Nzg1YTUyZDY3MjAxMWU3YzU3ZCIsInQiOiJ3ZWJfZmV0Y2giLCJ2Ijozfedro1DLr0CtC19bFFpY2RT8MIQYbXuAGhNBRrSYtDgT')

tests\unit\test_compact_cursor.py:82: AssertionError
______ test_compact_cursor_restart_respects_original_cache_policy[True] _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2174/test_compact_cursor_restart_re1')
cached = True

    @pytest.mark.parametrize("cached", [False, True])
    async def test_compact_cursor_restart_respects_original_cache_policy(tmp_path, cached):
        service = service_at(tmp_path)
        value = source()
        if cached:
            service._cache_result(value, "fixture-public", 3600)
        first = service._envelope("web_fetch", value, 2000)
        cursor = first["page"]["next_cursor"]
        await service.close()
>       assert len(cursor) <= 64
E       AssertionError: assert 255 <= 64
E        +  where 255 = len('eyJiIjoyMDAwLCJjIjoxLCJleHAiOjE3ODg0Mjk1NTIsImkiOjEsImsiOiJmaXh0dXJlLXB1YmxpYyIsIm4iOjIsInMiOiI2YjY5MDI0MWFmNWNiOTg0Y...mQwNWNhYTZjZDc3Mjg3ODVhNTJkNjcyMDExZTdjNTdkIiwidCI6IndlYl9mZXRjaCIsInYiOjN9qjLed57FpfUDh3YQhvwA-RYx8Y0chmehqh7qLTMbgrE')

tests\unit\test_compact_cursor.py:82: AssertionError
_____ test_compact_cursor_keeps_tamper_expiry_tool_and_budget_validation ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2174/test_compact_cursor_keeps_tamp0')

    async def test_compact_cursor_keeps_tamper_expiry_tool_and_budget_validation(tmp_path):
        service = service_at(tmp_path)
        now = [100]
        service.cursors.clock = lambda: now[0]
        try:
            cursor = service._envelope("web_fetch", source(), 2000)["page"]["next_cursor"]
>           assert len(cursor) <= 64
E           AssertionError: assert 228 <= 64
E            +  where 228 = len('eyJiIjoyMDAwLCJjIjoyLCJleHAiOjM3MDAsImkiOjIsImsiOiIiLCJuIjoyLCJzIjoiNmI2OTAyNDFhZjVjYjk4NGI3YzQyMzA3MTZlMTM4MWJkMDVjYWE2Y2Q3NzI4Nzg1YTUyZDY3MjAxMWU3YzU3ZCIsInQiOiJ3ZWJfZmV0Y2giLCJ2IjozfexzAa-w34_znOwhaVyXlsW0pjgDdw8RxJBkJGvKdyTO')

tests\unit\test_compact_cursor.py:101: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_compact_cursor.py::test_model_cursor_is_short_and_continuation_keeps_all_evidence[False]
FAILED tests/unit/test_compact_cursor.py::test_model_cursor_is_short_and_continuation_keeps_all_evidence[True]
FAILED tests/unit/test_compact_cursor.py::test_compact_cursor_metadata_is_bounded_and_visible
FAILED tests/unit/test_compact_cursor.py::test_compact_cursor_restart_respects_original_cache_policy[False]
FAILED tests/unit/test_compact_cursor.py::test_compact_cursor_restart_respects_original_cache_policy[True]
FAILED tests/unit/test_compact_cursor.py::test_compact_cursor_keeps_tamper_expiry_tool_and_budget_validation
6 failed in 1.56s

```

### Initial GREEN

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_compact_cursor.py tests/unit/test_cursor.py tests/unit/test_result_retention.py tests/unit/test_envelope.py
```

Output:

```text
..............................................                           [100%]
46 passed in 3.65s

```

### First full gate (failed)

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

Output:

```text
[GATE] lock check
Resolved 130 packages in 2ms
[GATE] format
110 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 44%]
........................................................................ [ 59%]
........................................................................ [ 74%]
........................................................................ [ 89%]
....................................F............                        [100%]
================================== FAILURES ===================================
___ test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence ____

app = <starlette.applications.Starlette object at 0x000001C1DC5B7D10>

    async def test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence(app):
        result = ProviderResult(
            "fixture",
            [
                EvidenceItem(
                    url="https://media.example/research", retrieved_at="2026-09-03T04:00:00Z", content="text " * 1000
                )
            ],
        )
        service = app.state.halo_service
        page = service._envelope("transcript_fetch", result, 2000)
>       old_state = service.cursors.decode(page["page"]["next_cursor"])
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:141:\x20
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <halo_research_gateway.cursor.CursorCodec object at 0x000001C1FFB3D430>
token = 'h1_AAAAAGqZRsVsmgdUITgQkvqc0mE73FKTHusYO-9_cVf9pMSx'

    def decode(self, token: str) -> dict:
        try:
            raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
            canonical = base64.urlsafe_b64encode(raw).decode().rstrip("=")
            if not hmac.compare_digest(token, canonical):
>               raise CursorError("cursor encoding is non-canonical")
E               halo_research_gateway.cursor.CursorError: cursor encoding is non-canonical

src\halo_research_gateway\cursor.py:84: CursorError
=========================== short test summary info ===========================
FAILED tests/unit/test_transcript_paging.py::test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence
1 failed, 480 passed in 76.46s (0:01:16)
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | unit and fixture tests failed with exit code 1

```

### Falsification (malformed persisted state)

Command:

```powershell
uv run --locked python -m pytest -q tests/unit/test_compact_cursor.py
```

Output:

```text
..........F....                                                          [100%]
================================== FAILURES ===================================
__ test_disk_handle_mapping_cannot_substitute_or_invent_evidence[non_ascii] ___

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2177/test_disk_handle_mapping_canno1')
corrupt = 'non_ascii'

    @pytest.mark.parametrize("corrupt", ["other_signed_state", "non_ascii", "missing"])
    async def test_disk_handle_mapping_cannot_substitute_or_invent_evidence(tmp_path, corrupt):
        service = service_at(tmp_path)
        value = source()
        service._cache_result(value, "fixture-public", 3600)
        token = service._envelope("web_fetch", value, 2000)["page"]["next_cursor"]
        key = "cursor-handle:" + token
        if corrupt == "missing":
            service.cache.delete(key)
        else:
            wrong = service.cursors.encode({"v": 3, "t": "web_fetch", "b": 2000, "s": "wrong"}).encode()
            service.cache.put(key, wrong if corrupt == "other_signed_state" else b"\xff", 3600)
        await service.close()
        restarted = service_at(tmp_path)
        try:
            result = await restarted.web_fetch(cursor=token)
            assert not result["ok"]
>           assert result["error"]["code"] == ("CURSOR_EVICTED" if corrupt == "missing" else "CURSOR_INVALID")
E           AssertionError: assert 'UPSTREAM_UNAVAILABLE' == 'CURSOR_INVALID'
E\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
E             - CURSOR_INVALID
E             + UPSTREAM_UNAVAILABLE

tests\unit\test_compact_cursor.py:182: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_compact_cursor.py::test_disk_handle_mapping_cannot_substitute_or_invent_evidence[non_ascii]
1 failed, 14 passed in 1.88s

```

### Corrected focused run

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/cursor.py src/halo_research_gateway/service.py tests/unit/test_compact_cursor.py tests/unit/test_transcript_paging.py
uv run --locked ruff check --fix tests/unit/test_compact_cursor.py
uv run --locked python -m pytest -q tests/unit/test_compact_cursor.py tests/unit/test_transcript_paging.py tests/unit/test_result_retention.py tests/unit/test_cursor.py tests/unit/test_envelope.py
```

Output:

```text
2 files reformatted, 2 files left unchanged
Found 1 error (1 fixed, 0 remaining).
.......................................................................  [100%]
71 passed in 5.96s

```

### Native local MCP, two clients and restart

Command:

```powershell
uv run --locked python -m pytest -q tests/acceptance/test_result_retention_native.py
```

Output:

```text
.                                                                        [100%]
1 passed in 6.74s

```

### Public transcript, native MCP and restart

Command:

```powershell
uv run --locked python tests/acceptance/transcript_mcp_native_live.py
```

Output:

```text
{"case": "public_transcript", "url": "https://iandevlin.github.io/mdn/video-player-with-captions/", "max_chars": 2000, "pages": 7, "cursor_chars": 51, "content_chars": 783, "segments": 14, "evidence_sha256": "239cce812bb6de2f92bc8fd78c6a8740a934a6e3e288caefe7ac1161d9791843", "warnings": ["RESULT_TRUNCATED"]}
{"case": "public_transcript", "url": "https://iandevlin.github.io/mdn/video-player-with-captions/", "max_chars": 4000, "pages": 2, "cursor_chars": 51, "content_chars": 783, "segments": 14, "evidence_sha256": "239cce812bb6de2f92bc8fd78c6a8740a934a6e3e288caefe7ac1161d9791843", "warnings": ["RESULT_TRUNCATED"]}
{"case": "public_transcript", "url": "https://iandevlin.github.io/mdn/video-player-with-captions/", "max_chars": 6000, "pages": 1, "cursor_chars": 0, "content_chars": 783, "segments": 14, "evidence_sha256": "239cce812bb6de2f92bc8fd78c6a8740a934a6e3e288caefe7ac1161d9791843", "warnings": []}
NATIVE GATEWAY OUTPUT: [09/03/26 03:09:59] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
                             started\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
[09/03/26 03:10:00] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://iandevlin.github.io/mdn/vi\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
                             deo-player-with-captions/\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
                             "HTTP/1.1 200 OK"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
[09/03/26 03:10:01] INFO     HTTP Request: GET                  _client.py:1740
                             https://iandevlin.github.io/mdn/vi\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
                             deo-player-with-captions/subtitles\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
                             /vtt/sintel-en.vtt "HTTP/1.1 200\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
                             OK"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814

{"case": "new_process_and_client_continue_cached_transcript", "remaining_pages": 6, "identical_evidence": true, "warnings": ["RESULT_TRUNCATED"]}
Native transcript text/timestamps at all budgets and restart continuation PASS
NATIVE GATEWAY OUTPUT: [09/03/26 03:10:02] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
                             started\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20
[09/03/26 03:10:03] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814

{"owned_native_process_stopped": true}
Temporary native Gateway state removed

```

### Full gate

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

Output:

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
110 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 14%]
........................................................................ [ 29%]
........................................................................ [ 44%]
........................................................................ [ 58%]
........................................................................ [ 73%]
........................................................................ [ 88%]
..........................................................               [100%]
490 passed in 77.06s (0:01:17)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```
