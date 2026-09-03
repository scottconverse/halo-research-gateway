# Result retention and lossless pagination evidence — 2026-09-02

## Scope and outcome

Private development checkpoint based on ddcd58c178604ed735da49446e9d3771c2e37ad3.
Product version remains 0.2.0; result schema remains 1.5; database schema is unchanged.
This fixes existing research evidence handling, not a new action or personal-assistant feature.
Commit, remote CI and deployed process identity belong in the separate operator delivery receipt.

- Cursors bind a serialized, immutable evidence hash rather than a mutable query-key result.
- Retained snapshots share bounded count (default 128), serialized UTF-8 bytes (64 MiB)
  and idle age (cursor TTL). Statistics report actual retained payload usage.
- Changed/expired/evicted evidence cannot silently substitute a newer upstream result.
  Restart recovery uses only a matching public disk-cache hash; private results have no disk key.
- The formatter measures actual MCP JSON including the signed cursor and carries
  unreturned snippet/content text to subsequent pages. It does not discard prose to fit.
- Non-prose fields that cannot fit fail with OUTPUT_ITEM_TOO_LARGE. Payloads exceeding
  the retention ceiling fail with SNAPSHOT_TOO_LARGE.
- Recognized sensitive final HTTP redirect citations and non-PDF document fallback
  citations are redacted and not persisted. New fetch/document cache namespaces bypass
  historical rows; existing historical state is preserved, not scrubbed.
- GitHub public fallback consumes normalized search results directly, avoiding reliance
  on a mutable or already-evicted snapshot side effect.

## What the tests prove

Baseline: 288 tests. Final deterministic gate: 314 tests.
The 26 new unit cases cover count/byte/TTL validation, eviction, expiry/close,
oversized payloads, redirect sensitivity, legacy caches/cursors, refresh/object-mutation
immutability, all content at 2000/4000/6000-character budgets, matching versus changed
restart cache, private cache isolation, snippet-only/mixed/Unicode text, oversized metadata
and UTF-8 accounting/deduplication. Existing envelope tests were not weakened.

The separate native test starts disposable real Gateway processes, uses two actual
HTTP MCP clients and an exact configured loopback HTTP source, checks every returned
character and wire-page size, forces shared eviction, verifies no upstream request per
continuation, restarts, and confirms private results cannot recover from disk.
The final native collection also reruns real Chrome traversal, cookie/HTTP/WebSocket
fixtures and native document extraction. These are controlled fixtures, not real-account,
public-upstream, complete DSH or clean-machine installation acceptance.

Files read before changes: config, envelope, HTTP/document/search/GitHub paths in service,
models/cache/cursor/clock and adjacent tests, native fixture patterns, config example,
README, manual, operations/status/scope/progress/changelog and repository skill scope.
Search behavior is preserved; extraction into a private helper was required because the
old GitHub fallback relied on mutable snapshot internals.

## Security and bounds review

- Trust-boundary inputs: signed cursor validation and tool/budget binding retained;
  new TTL/count/byte fields have explicit positive bounds. URL security checks retained.
- Routes/authentication: no new route or authorization policy. Existing localhost-only
  /stats adds aggregate counts only. No DSH permission/model/preset changes.
- Secrets: test redirect values are explicit synthetic fixture markers. No account keys,
  actual cookies, private source text or live signed URLs are used in this receipt.
  Whole-repository credential-pattern review is recorded separately before push.
- Rendering/deserialization: no eval or pickle; immutable payloads use existing JSON
  normalization. Existing MCP JSON rendering contract is tested byte-for-character.
- Dependencies: none added or changed, so no new dependency vulnerability review applies.
- Performance: retention is bounded, but serialization, copies, pre-chunking and browser/
  parser allocation can exceed this retained-payload number. It is not a hard process RAM cap.

## Limits and upgrade behavior

Old-format cursors require a fresh request (CURSOR_EVICTED); no schema/database migration
or runtime config rewrite occurs. Snapshot pruning is activity-driven, not a background
timer; continued use renews retention. Normal close clears snapshots, but a hung crawler
shutdown is not proved here. Coverage counts are evidence fragments, not unique URLs.
Existing link-summary truncation remains; losslessness refers to collected snippet/content.

Sensitive intermediate-hop-only URLs, arbitrary embedded URLs and source prose are not
universally sanitized. Non-PDF document fallback still downloads twice. Ordinary disk-cache
eviction, local/GitHub response/shared limits, arbitrary job fields, native peak memory,
browser DNS/OOPIF/subresource limits, broad stress, startup/logon/install and DSH workflow
remain open. Installed cross-project skill scope copies are not overwritten without the
separately requested approval.

## Exact verification evidence

The first two sandbox failures below ran no tests and are not valid RED evidence.
Configuration fields were restored before the subsequent successful assertion-RED run.
The first implementation and later falsification failures are retained, not relabeled green.
Pytest's own abbreviated value representations are preserved as emitted; verbose initial
RED output is used below. No tool-output truncation is introduced in this file.

### Unchanged baseline

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

## Pre-push repository review

Private remote verified with `gh repo view scottconverse/halo-research-gateway --json nameWithOwner,isPrivate,url`: isPrivate=true.
The six matches below were read and are existing synthetic userinfo redaction/rejection cases, not credentials. Ignore checks cover local config, environment, runtime, vault, private evidence, dependency and build artifacts. This is a limited pattern scan, not a guarantee against every possible secret format. README/manual/changelog and tests pass for this private development checkpoint. LICENSE and CONTRIBUTING remain missing; package/public-release readiness is not claimed. No package release, version bump, tag, personal profile or DSH mutation is included.

Command:

```powershell
$taskPaths=@(git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway ls-files --cached --others --exclude-standard | Sort-Object -Unique) + @('AGENTS.md')
$taskSecretPattern='(gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----|https?://[^\s/@]+:[^\s/@]+@)'
$taskFindings=@(foreach($taskPath in $taskPaths) { Select-String -LiteralPath $taskPath -Pattern $taskSecretPattern | ForEach-Object { [pscustomobject]@{Path=$taskPath;Line=$_.LineNumber} } })
$taskFindings | ConvertTo-Json -Compress
[pscustomobject]@{scanned_files=$taskPaths.Count;credential_pattern_matches=$taskFindings.Count;license_present=(Test-Path LICENSE);contributing_present=(Test-Path CONTRIBUTING.md)} | ConvertTo-Json -Compress
git -c safe.directory=C:/Users/scott/Desktop/Code/halo-research-gateway check-ignore .env config/config.toml runtime/test.db vault/test.key evidence/private/sample.txt .venv/test dist/test
```

Output:

```text
[{"Path":"debug_redaction.py","Line":7},{"Path":"tests/unit/test_redaction.py","Line":11},{"Path":"tests/unit/test_redaction.py","Line":48},{"Path":"tests/unit/test_security.py","Line":35},{"Path":"tests/unit/test_security.py","Line":106},{"Path":"verify_implementation.py","Line":8}]
{"scanned_files":228,"credential_pattern_matches":6,"license_present":false,"contributing_present":false}
.env
config/config.toml
runtime/test.db
vault/test.key
evidence/private/sample.txt
.venv/test
dist/test
```


Output:

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
288 passed in 60.46s (0:01:00)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

### Initial assertion failures (verbose rerun)

Command:

```powershell
uv run --locked pytest -vv tests/unit/test_result_retention.py
```

Output:

```text
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\scott\Desktop\Code\halo-research-gateway
configfile: pyproject.toml
plugins: anyio-4.14.2, asyncio-1.4.0, respx-0.23.1
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 5 items

tests/unit/test_result_retention.py::test_sensitive_final_http_url_is_redacted_and_never_cached[web_fetch] FAILED [ 20%]
tests/unit/test_result_retention.py::test_sensitive_final_http_url_is_redacted_and_never_cached[document_extract] FAILED [ 40%]
tests/unit/test_result_retention.py::test_fetch_ignores_legacy_cache_that_predates_redirect_redaction FAILED [ 60%]
tests/unit/test_result_retention.py::test_cursor_keeps_original_evidence_after_same_url_refresh FAILED [ 80%]
tests/unit/test_result_retention.py::test_cursor_snapshot_cannot_be_mutated_by_provider_after_return FAILED [100%]

================================== FAILURES ===================================
____ test_sensitive_final_http_url_is_redacted_and_never_cached[web_fetch] ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1975/test_sensitive_final_http_url_0')
tool = 'web_fetch'

    @pytest.mark.parametrize("tool", ["web_fetch", "document_extract"])
    async def test_sensitive_final_http_url_is_redacted_and_never_cached(tmp_path, tool):
        service = service_at(tmp_path)
        calls = []
        start = "https://example.org/research"
        final = start + "?token=fixture-redirect-secret&q=public"
    
        async def download(url, *args):
            calls.append(url)
            return final, SimpleNamespace(host="example.org"), {"content-type": "text/plain"}, b"Public research evidence. " * 10
    
        service.http.download = download
        try:
            for _ in range(2):
                result = await getattr(service, tool)(start)
                assert result["ok"], result
>               assert "fixture-redirect-secret" not in json.dumps(result), "signed redirect leaked into research output"
E               AssertionError: signed redirect leaked into research output
E               assert 'fixture-redirect-secret' not in '{"schema_version": "1.5", "ok": true, "request_id": "e8dc6546-6a45-4525-a36b-524e95b98d1c", "tool": "web_fetch", "provider": "direct-http", "requested_at": "2026-09-03T02:53:40.066550Z", "completed_at": "2026-09-03T02:53:40.066550Z", "cache": {"hit": false, "age_seconds": 0, "key": "fetch:018054d8a52a281a00611c94e0aa80d2f544c4302d8aa4dee4615a35a6b75c9b"}, "coverage": {"requested": 1, "available": 1, "returned_this_page": 1, "returned_cumulative": 1, "complete": true}, "page": {"number": 1, "serialized_chars": 1425, "next_cursor": null, "snapshot_expires_at": null}, "retry_after_seconds": null, "items": [{"title": null, "url": "https://example.org/research?token=fixture-redirect-secret&q=public", "published_at": null, "retrieved_at": "2026-09-03T02:53:40.063758Z", "source": "example.org", "snippet": null, "content": "Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. ", "metadata": {"content_type": "text/plain", "links": [], "sha256": "54e32383c935cc295ddfe2665fcc2a4996a27bb61cfc2fd41ba2b8ba0e7df97c"}}], "warnings": []}'
E                 
E                 'fixture-redirect-secret' is contained here:
E                   {"schema_version": "1.5", "ok": true, "request_id": "e8dc6546-6a45-4525-a36b-524e95b98d1c", "tool": "web_fetch", "provider": "direct-http", "requested_at": "2026-09-03T02:53:40.066550Z", "completed_at": "2026-09-03T02:53:40.066550Z", "cache": {"hit": false, "age_seconds": 0, "key": "fetch:018054d8a52a281a00611c94e0aa80d2f544c4302d8aa4dee4615a35a6b75c9b"}, "coverage": {"requested": 1, "available": 1, "returned_this_page": 1, "returned_cumulative": 1, "complete": true}, "page": {"number": 1, "serialized_chars": 1425, "next_cursor": null, "snapshot_expires_at": null}, "retry_after_seconds": null, "items": [{"title": null, "url": "https://example.org/research?token=fixture-redirect-secret&q=public", "published_at": null, "retrieved_at": "2026-09-03T02:53:40.063758Z", "source": "example.org", "snippet": null, "content": "Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. ", "metadata": {"content_type": "text/plain", "links": [], "sha256": "54e32383c935cc295ddfe2665fcc2a4996a27bb61cfc2fd41ba2b8ba0e7df97c"}}], "warnings": []}
E                 ?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               +++++++++++++++++++++++

tests\unit\test_result_retention.py:38: AssertionError
_ test_sensitive_final_http_url_is_redacted_and_never_cached[document_extract] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1975/test_sensitive_final_http_url_1')
tool = 'document_extract'

    @pytest.mark.parametrize("tool", ["web_fetch", "document_extract"])
    async def test_sensitive_final_http_url_is_redacted_and_never_cached(tmp_path, tool):
        service = service_at(tmp_path)
        calls = []
        start = "https://example.org/research"
        final = start + "?token=fixture-redirect-secret&q=public"
    
        async def download(url, *args):
            calls.append(url)
            return final, SimpleNamespace(host="example.org"), {"content-type": "text/plain"}, b"Public research evidence. " * 10
    
        service.http.download = download
        try:
            for _ in range(2):
                result = await getattr(service, tool)(start)
                assert result["ok"], result
>               assert "fixture-redirect-secret" not in json.dumps(result), "signed redirect leaked into research output"
E               AssertionError: signed redirect leaked into research output
E               assert 'fixture-redirect-secret' not in '{"schema_version": "1.5", "ok": true, "request_id": "77d46db5-fa54-406c-9fd5-5307e79916ff", "tool": "document_extract", "provider": "direct-http", "requested_at": "2026-09-03T02:53:40.264943Z", "completed_at": "2026-09-03T02:53:40.264943Z", "cache": {"hit": false, "age_seconds": 0, "key": "document:v2:25595069933521ff3b7cb28069bb31d0ac2bf259c59d4749980096956726a3ec"}, "coverage": {"requested": 1, "available": 1, "returned_this_page": 1, "returned_cumulative": 1, "complete": true}, "page": {"number": 1, "serialized_chars": 1470, "next_cursor": null, "snapshot_expires_at": null}, "retry_after_seconds": null, "items": [{"title": null, "url": "https://example.org/research?token=fixture-redirect-secret&q=public", "published_at": null, "retrieved_at": "2026-09-03T02:53:40.261927Z", "source": "example.org", "snippet": null, "content": "Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. ", "metadata": {"content_type": "text/plain", "links": [], "sha256": "54e32383c935cc295ddfe2665fcc2a4996a27bb61cfc2fd41ba2b8ba0e7df97c"}}], "warnings": ["DOCUMENT_TEXT_FALLBACK"]}'
E                 
E                 'fixture-redirect-secret' is contained here:
E                   {"schema_version": "1.5", "ok": true, "request_id": "77d46db5-fa54-406c-9fd5-5307e79916ff", "tool": "document_extract", "provider": "direct-http", "requested_at": "2026-09-03T02:53:40.264943Z", "completed_at": "2026-09-03T02:53:40.264943Z", "cache": {"hit": false, "age_seconds": 0, "key": "document:v2:25595069933521ff3b7cb28069bb31d0ac2bf259c59d4749980096956726a3ec"}, "coverage": {"requested": 1, "available": 1, "returned_this_page": 1, "returned_cumulative": 1, "complete": true}, "page": {"number": 1, "serialized_chars": 1470, "next_cursor": null, "snapshot_expires_at": null}, "retry_after_seconds": null, "items": [{"title": null, "url": "https://example.org/research?token=fixture-redirect-secret&q=public", "published_at": null, "retrieved_at": "2026-09-03T02:53:40.261927Z", "source": "example.org", "snippet": null, "content": "Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. ", "metadata": {"content_type": "text/plain", "links": [], "sha256": "54e32383c935cc295ddfe2665fcc2a4996a27bb61cfc2fd41ba2b8ba0e7df97c"}}], "warnings": ["DOCUMENT_TEXT_FALLBACK"]}
E                 ?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            +++++++++++++++++++++++

tests\unit\test_result_retention.py:38: AssertionError
______ test_fetch_ignores_legacy_cache_that_predates_redirect_redaction _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1975/test_fetch_ignores_legacy_cach0')

    async def test_fetch_ignores_legacy_cache_that_predates_redirect_redaction(tmp_path):
        service = service_at(tmp_path)
        url = "https://example.org/research"
        legacy = ProviderResult("legacy", [EvidenceItem(url=url + "?token=legacy-fixture-secret", retrieved_at="2026-09-03T00:00:00Z", content="old")])
        service.cache.put("fetch:" + hashlib.sha256(url.encode()).hexdigest(), service._encode_result(legacy), 3600)
    
        async def fetch(url):
            return ProviderResult("fresh", [EvidenceItem(url=url, retrieved_at="2026-09-03T01:00:00Z", content="new")])
    
        service.http.fetch = fetch
        try:
            result = await service.web_fetch(url)
>           assert result["provider"] == "fresh", "legacy unsafe cache was served without revalidation"
E           AssertionError: legacy unsafe cache was served without revalidation
E           assert 'legacy' == 'fresh'
E             
E             - fresh
E             + legacy

tests\unit\test_result_retention.py:58: AssertionError
_________ test_cursor_keeps_original_evidence_after_same_url_refresh __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1975/test_cursor_keeps_original_evi0')

    async def test_cursor_keeps_original_evidence_after_same_url_refresh(tmp_path):
        service = service_at(tmp_path)
        calls = 0
    
        async def fetch(url):
            nonlocal calls
            calls += 1
            return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content=("ORIGINAL " if calls == 1 else "REPLACEMENT ") * 1200)])
    
        service.http.fetch = fetch
        try:
            first = await service.web_fetch("https://example.org/research", max_chars=2000)
            cursor = first["page"]["next_cursor"]
            assert cursor
            refreshed = await service.web_fetch("https://example.org/research", max_chars=2000, max_age_seconds=0)
            assert refreshed["ok"] and calls == 2
            continued = await service.web_fetch(cursor=cursor)
            assert continued["ok"], continued
>           assert "ORIGINAL" in continued["items"][0]["content"], "cursor silently switched to replacement evidence"
E           AssertionError: cursor silently switched to replacement evidence
E           assert 'ORIGINAL' in 'ENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT RE'

tests\unit\test_result_retention.py:82: AssertionError
_______ test_cursor_snapshot_cannot_be_mutated_by_provider_after_return _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1975/test_cursor_snapshot_cannot_be0')

    async def test_cursor_snapshot_cannot_be_mutated_by_provider_after_return(tmp_path):
        service = service_at(tmp_path)
        source = ProviderResult("fixture", [EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T00:00:00Z", content="ORIGINAL " * 1200)])
    
        async def fetch(url):
            return source
    
        service.http.fetch = fetch
        try:
            first = await service.web_fetch(source.items[0].url, max_chars=2000)
            source.items[0].content = "MUTATED " * 1200
            continued = await service.web_fetch(cursor=first["page"]["next_cursor"])
            assert continued["ok"], continued
>           assert "ORIGINAL" in continued["items"][0]["content"], "stored snapshot retained mutable provider objects"
E           AssertionError: stored snapshot retained mutable provider objects
E           assert 'ORIGINAL' in 'TED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MU'

tests\unit\test_result_retention.py:101: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_result_retention.py::test_sensitive_final_http_url_is_redacted_and_never_cached[web_fetch] - AssertionError: signed redirect leaked into research output
assert 'fixture-redirect-secret' not in '{"schema_version": "1.5", "ok": true, "request_id": "e8dc6546-6a45-4525-a36b-524e95b98d1c", "tool": "web_fetch", "provider": "direct-http", "requested_at": "2026-09-03T02:53:40.066550Z", "completed_at": "2026-09-03T02:53:40.066550Z", "cache": {"hit": false, "age_seconds": 0, "key": "fetch:018054d8a52a281a00611c94e0aa80d2f544c4302d8aa4dee4615a35a6b75c9b"}, "coverage": {"requested": 1, "available": 1, "returned_this_page": 1, "returned_cumulative": 1, "complete": true}, "page": {"number": 1, "serialized_chars": 1425, "next_cursor": null, "snapshot_expires_at": null}, "retry_after_seconds": null, "items": [{"title": null, "url": "https://example.org/research?token=fixture-redirect-secret&q=public", "published_at": null, "retrieved_at": "2026-09-03T02:53:40.063758Z", "source": "example.org", "snippet": null, "content": "Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. ", "metadata": {"content_type": "text/plain", "links": [], "sha256": "54e32383c935cc295ddfe2665fcc2a4996a27bb61cfc2fd41ba2b8ba0e7df97c"}}], "warnings": []}'
  
  'fixture-redirect-secret' is contained here:
    {"schema_version": "1.5", "ok": true, "request_id": "e8dc6546-6a45-4525-a36b-524e95b98d1c", "tool": "web_fetch", "provider": "direct-http", "requested_at": "2026-09-03T02:53:40.066550Z", "completed_at": "2026-09-03T02:53:40.066550Z", "cache": {"hit": false, "age_seconds": 0, "key": "fetch:018054d8a52a281a00611c94e0aa80d2f544c4302d8aa4dee4615a35a6b75c9b"}, "coverage": {"requested": 1, "available": 1, "returned_this_page": 1, "returned_cumulative": 1, "complete": true}, "page": {"number": 1, "serialized_chars": 1425, "next_cursor": null, "snapshot_expires_at": null}, "retry_after_seconds": null, "items": [{"title": null, "url": "https://example.org/research?token=fixture-redirect-secret&q=public", "published_at": null, "retrieved_at": "2026-09-03T02:53:40.063758Z", "source": "example.org", "snippet": null, "content": "Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. ", "metadata": {"content_type": "text/plain", "links": [], "sha256": "54e32383c935cc295ddfe2665fcc2a4996a27bb61cfc2fd41ba2b8ba0e7df97c"}}], "warnings": []}
  ?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               +++++++++++++++++++++++
FAILED tests/unit/test_result_retention.py::test_sensitive_final_http_url_is_redacted_and_never_cached[document_extract] - AssertionError: signed redirect leaked into research output
assert 'fixture-redirect-secret' not in '{"schema_version": "1.5", "ok": true, "request_id": "77d46db5-fa54-406c-9fd5-5307e79916ff", "tool": "document_extract", "provider": "direct-http", "requested_at": "2026-09-03T02:53:40.264943Z", "completed_at": "2026-09-03T02:53:40.264943Z", "cache": {"hit": false, "age_seconds": 0, "key": "document:v2:25595069933521ff3b7cb28069bb31d0ac2bf259c59d4749980096956726a3ec"}, "coverage": {"requested": 1, "available": 1, "returned_this_page": 1, "returned_cumulative": 1, "complete": true}, "page": {"number": 1, "serialized_chars": 1470, "next_cursor": null, "snapshot_expires_at": null}, "retry_after_seconds": null, "items": [{"title": null, "url": "https://example.org/research?token=fixture-redirect-secret&q=public", "published_at": null, "retrieved_at": "2026-09-03T02:53:40.261927Z", "source": "example.org", "snippet": null, "content": "Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. ", "metadata": {"content_type": "text/plain", "links": [], "sha256": "54e32383c935cc295ddfe2665fcc2a4996a27bb61cfc2fd41ba2b8ba0e7df97c"}}], "warnings": ["DOCUMENT_TEXT_FALLBACK"]}'
  
  'fixture-redirect-secret' is contained here:
    {"schema_version": "1.5", "ok": true, "request_id": "77d46db5-fa54-406c-9fd5-5307e79916ff", "tool": "document_extract", "provider": "direct-http", "requested_at": "2026-09-03T02:53:40.264943Z", "completed_at": "2026-09-03T02:53:40.264943Z", "cache": {"hit": false, "age_seconds": 0, "key": "document:v2:25595069933521ff3b7cb28069bb31d0ac2bf259c59d4749980096956726a3ec"}, "coverage": {"requested": 1, "available": 1, "returned_this_page": 1, "returned_cumulative": 1, "complete": true}, "page": {"number": 1, "serialized_chars": 1470, "next_cursor": null, "snapshot_expires_at": null}, "retry_after_seconds": null, "items": [{"title": null, "url": "https://example.org/research?token=fixture-redirect-secret&q=public", "published_at": null, "retrieved_at": "2026-09-03T02:53:40.261927Z", "source": "example.org", "snippet": null, "content": "Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. Public research evidence. ", "metadata": {"content_type": "text/plain", "links": [], "sha256": "54e32383c935cc295ddfe2665fcc2a4996a27bb61cfc2fd41ba2b8ba0e7df97c"}}], "warnings": ["DOCUMENT_TEXT_FALLBACK"]}
  ?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            +++++++++++++++++++++++
FAILED tests/unit/test_result_retention.py::test_fetch_ignores_legacy_cache_that_predates_redirect_redaction - AssertionError: legacy unsafe cache was served without revalidation
assert 'legacy' == 'fresh'
  
  - fresh
  + legacy
FAILED tests/unit/test_result_retention.py::test_cursor_keeps_original_evidence_after_same_url_refresh - AssertionError: cursor silently switched to replacement evidence
assert 'ORIGINAL' in 'ENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT REPLACEMENT RE'
FAILED tests/unit/test_result_retention.py::test_cursor_snapshot_cannot_be_mutated_by_provider_after_return - AssertionError: stored snapshot retained mutable provider objects
assert 'ORIGINAL' in 'TED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MUTATED MU'
============================== 5 failed in 1.39s ==============================
```

### First incomplete fix

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/service.py src/halo_research_gateway/providers/http_fetch.py tests/unit/test_result_retention.py; uv run --locked pytest -q tests/unit/test_result_retention.py tests/unit/test_retrieval_regressions.py tests/unit/test_v15_state.py
```

Output:

```text
2 files reformatted, 1 file left unchanged
...FF.....................                                               [100%]
================================== FAILURES ===================================
_________ test_cursor_keeps_original_evidence_after_same_url_refresh __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1976/test_cursor_keeps_original_evi0')

    async def test_cursor_keeps_original_evidence_after_same_url_refresh(tmp_path):
        service = service_at(tmp_path)
        calls = 0
    
        async def fetch(url):
            nonlocal calls
            calls += 1
            return ProviderResult(
                "fixture",
                [
                    EvidenceItem(
                        url=url,
                        retrieved_at="2026-09-03T00:00:00Z",
                        content=("ORIGINAL " if calls == 1 else "REPLACEMENT ") * 1200,
                    )
                ],
            )
    
        service.http.fetch = fetch
        try:
            first = await service.web_fetch("https://example.org/research", max_chars=2000)
            cursor = first["page"]["next_cursor"]
            assert cursor
            refreshed = await service.web_fetch("https://example.org/research", max_chars=2000, max_age_seconds=0)
            assert refreshed["ok"] and calls == 2
            continued = await service.web_fetch(cursor=cursor)
            assert continued["ok"], continued
>           assert "ORIGINAL" in continued["items"][0]["content"], "cursor silently switched to replacement evidence"
E           AssertionError: cursor silently switched to replacement evidence
E           assert 'ORIGINAL' in ''

tests\unit\test_result_retention.py:99: AssertionError
_______ test_cursor_snapshot_cannot_be_mutated_by_provider_after_return _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1976/test_cursor_snapshot_cannot_be0')

    async def test_cursor_snapshot_cannot_be_mutated_by_provider_after_return(tmp_path):
        service = service_at(tmp_path)
        source = ProviderResult(
            "fixture",
            [
                EvidenceItem(
                    url="https://example.org/research", retrieved_at="2026-09-03T00:00:00Z", content="ORIGINAL " * 1200
                )
            ],
        )
    
        async def fetch(url):
            return source
    
        service.http.fetch = fetch
        try:
            first = await service.web_fetch(source.items[0].url, max_chars=2000)
            source.items[0].content = "MUTATED " * 1200
            continued = await service.web_fetch(cursor=first["page"]["next_cursor"])
            assert continued["ok"], continued
>           assert "ORIGINAL" in continued["items"][0]["content"], "stored snapshot retained mutable provider objects"
E           AssertionError: stored snapshot retained mutable provider objects
E           assert 'ORIGINAL' in ''

tests\unit\test_result_retention.py:125: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_result_retention.py::test_cursor_keeps_original_evidence_after_same_url_refresh
FAILED tests/unit/test_result_retention.py::test_cursor_snapshot_cannot_be_mutated_by_provider_after_return
2 failed, 24 passed in 1.98s
```

### Compact cursor interim check

Command:

```powershell
uv run --locked pytest -q tests/unit/test_result_retention.py tests/unit/test_retrieval_regressions.py tests/unit/test_v15_state.py
```

Output:

```text
..........................                                               [100%]
26 passed in 1.68s
```

### Configuration probe blocked before tests (not RED evidence)

Command:

```powershell
uv run --locked pytest -q tests/unit/test_result_retention.py -k 'operator_configurable or budgets_reject_zero'
```

Output:

```text
error: Failed to initialize cache at `C:\Users\scott\AppData\Local\uv\cache`
  Caused by: failed to open file `C:\Users\scott\AppData\Local\uv\cache\sdists-v9\.git`: Access is denied. (os error 5)
```

### Retention probe blocked before tests (not RED evidence)

Command:

```powershell
uv run --locked pytest -q tests/unit/test_result_retention.py -k 'snapshot_store or expired_snapshots or single_result'
```

Output:

```text
error: Failed to initialize cache at `C:\Users\scott\AppData\Local\uv\cache`
  Caused by: failed to open file `C:\Users\scott\AppData\Local\uv\cache\sdists-v9\.git`: Access is denied. (os error 5)
```

### Configuration assertion RED after restoring baseline fields

Command:

```powershell
uv run --locked pytest -q tests/unit/test_result_retention.py -k 'operator_configurable or budgets_reject_zero'
```

Output:

```text
FF..                                                                     [100%]
================================== FAILURES ===================================
_______________ test_snapshot_limits_are_operator_configurable ________________

    def test_snapshot_limits_are_operator_configurable():
        fields = OutputConfig.model_fields
>       assert "snapshot_max_entries" in fields and "snapshot_max_bytes" in fields, "snapshot budgets are missing"
E       AssertionError: snapshot budgets are missing
E       assert ('snapshot_max_entries' in {'unidentified_default_chars': FieldInfo(annotation=int, required=False, default=6000), 'unidentified_ceiling_chars': ... required=False, default=3600), 'profiles': FieldInfo(annotation=dict[str, OutputProfile], required=False, default={})})

tests\unit\test_result_retention.py:24: AssertionError
____________ test_snapshot_budgets_reject_zero[cursor_ttl_seconds] ____________

field = 'cursor_ttl_seconds'

    @pytest.mark.parametrize("field", ["cursor_ttl_seconds", "snapshot_max_entries", "snapshot_max_bytes"])
    def test_snapshot_budgets_reject_zero(field):
        accepted = True
        try:
            OutputConfig.model_validate({field: 0})
        except ValueError:
            accepted = False
>       assert not accepted, f"{field}=0 was accepted"
E       AssertionError: cursor_ttl_seconds=0 was accepted
E       assert not True

tests\unit\test_result_retention.py:34: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_result_retention.py::test_snapshot_limits_are_operator_configurable
FAILED tests/unit/test_result_retention.py::test_snapshot_budgets_reject_zero[cursor_ttl_seconds]
2 failed, 2 passed, 9 deselected in 0.82s
```

### Retention assertion RED

Command:

```powershell
uv run --locked pytest -q tests/unit/test_result_retention.py -k 'snapshot_store or expired_snapshots or single_result'
```

Output:

```text
FFFF                                                                     [100%]
================================== FAILURES ===================================
___ test_snapshot_store_evicts_old_non_disk_results_within_budgets[entries] ___

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1978/test_snapshot_store_evicts_old0')
limit = 'entries'

    @pytest.mark.parametrize("limit", ["entries", "bytes"])
    async def test_snapshot_store_evicts_old_non_disk_results_within_budgets(tmp_path, limit):
        service = service_at(tmp_path)
        service.config.output.snapshot_max_entries = 2 if limit == "entries" else 100
        service.config.output.snapshot_max_bytes = 50_000 if limit == "entries" else 15_000
        cursors = []
        try:
            for number in range(3):
                value = ProviderResult("private-fixture", [EvidenceItem(url=f"https://example.org/{number}", retrieved_at="2026-09-03T00:00:00Z", content=str(number) * 9000)])
                result = service._envelope("web_crawl", value, 2000)
                cursors.append(result["page"]["next_cursor"])
            expired = service._resume("web_crawl", cursors[0], None)
>           assert not expired["ok"], "old non-cacheable result survived its retention budget"
E           AssertionError: old non-cacheable result survived its retention budget
E           assert not True

tests\unit\test_result_retention.py:49: AssertionError
____ test_snapshot_store_evicts_old_non_disk_results_within_budgets[bytes] ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1978/test_snapshot_store_evicts_old1')
limit = 'bytes'

    @pytest.mark.parametrize("limit", ["entries", "bytes"])
    async def test_snapshot_store_evicts_old_non_disk_results_within_budgets(tmp_path, limit):
        service = service_at(tmp_path)
        service.config.output.snapshot_max_entries = 2 if limit == "entries" else 100
        service.config.output.snapshot_max_bytes = 50_000 if limit == "entries" else 15_000
        cursors = []
        try:
            for number in range(3):
                value = ProviderResult("private-fixture", [EvidenceItem(url=f"https://example.org/{number}", retrieved_at="2026-09-03T00:00:00Z", content=str(number) * 9000)])
                result = service._envelope("web_crawl", value, 2000)
                cursors.append(result["page"]["next_cursor"])
            expired = service._resume("web_crawl", cursors[0], None)
>           assert not expired["ok"], "old non-cacheable result survived its retention budget"
E           AssertionError: old non-cacheable result survived its retention budget
E           assert not True

tests\unit\test_result_retention.py:49: AssertionError
__________ test_expired_snapshots_are_pruned_and_close_releases_all ___________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1978/test_expired_snapshots_are_pru0')

    async def test_expired_snapshots_are_pruned_and_close_releases_all(tmp_path):
        service = service_at(tmp_path)
        clock = [10.0]
        service.clock.monotonic = lambda: clock[0]
        service.config.output.cursor_ttl_seconds = 5
        source = ProviderResult("fixture", [EvidenceItem(url="https://example.org/", retrieved_at="2026-09-03T00:00:00Z", content="original" * 1000)])
        try:
            first = service._envelope("web_crawl", source, 2000)
            clock[0] = 16.0
            gone = service._resume("web_crawl", first["page"]["next_cursor"], None)
>           assert not gone["ok"], "expired non-disk snapshot still resumed"
E           AssertionError: expired non-disk snapshot still resumed
E           assert not True

tests\unit\test_result_retention.py:72: AssertionError
_______ test_single_result_larger_than_snapshot_budget_fails_explicitly _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1978/test_single_result_larger_than0')

    async def test_single_result_larger_than_snapshot_budget_fails_explicitly(tmp_path):
        service = service_at(tmp_path)
        service.config.output.snapshot_max_bytes = 2000
    
        async def fetch(url):
            return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="x" * 9000)])
    
        service.http.fetch = fetch
        try:
            result = await service.web_fetch("https://example.org/huge")
>           assert not result["ok"], "oversized result exceeded snapshot budget"
E           AssertionError: oversized result exceeded snapshot budget
E           assert not True

tests\unit\test_result_retention.py:92: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_result_retention.py::test_snapshot_store_evicts_old_non_disk_results_within_budgets[entries]
FAILED tests/unit/test_result_retention.py::test_snapshot_store_evicts_old_non_disk_results_within_budgets[bytes]
FAILED tests/unit/test_result_retention.py::test_expired_snapshots_are_pruned_and_close_releases_all
FAILED tests/unit/test_result_retention.py::test_single_result_larger_than_snapshot_budget_fails_explicitly
4 failed, 9 deselected in 1.01s
```

### Retention/configuration GREEN

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/service.py src/halo_research_gateway/config.py tests/unit/test_result_retention.py; uv run --locked pytest -q tests/unit/test_result_retention.py tests/unit/test_retrieval_regressions.py tests/unit/test_v15_state.py tests/unit/test_config.py
```

Output:

```text
1 file reformatted, 2 files left unchanged
..........................................                               [100%]
42 passed in 1.94s
```

### Lossless pagination assertion RED

Command:

```powershell
uv run --locked pytest -q tests/unit/test_result_retention.py -k 'every_content or restart_resumes'
```

Output:

```text
F....                                                                    [100%]
================================== FAILURES ===================================
_________ test_all_cursor_pages_retain_every_content_character[2000] __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1980/test_all_cursor_pages_retain_e0')
budget = 2000

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    async def test_all_cursor_pages_retain_every_content_character(tmp_path, budget):
        service = service_at(tmp_path)
        expected = "Research evidence: alpha beta gamma.\n" * 250
    
        async def fetch(url):
            return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content=expected)])
    
        service.http.fetch = fetch
        try:
            result = await service.web_fetch("https://example.org/research", max_chars=budget)
            text = ""
            pages = 0
            while True:
                assert result["ok"], result
                assert len(json.dumps(result, indent=2, ensure_ascii=False)) <= budget
                text += "".join(item.get("content", "") for item in result["items"])
                pages += 1
                cursor = result["page"]["next_cursor"]
                if not cursor:
                    break
                assert pages < 300, "pagination did not make forward progress"
                result = await service.web_fetch(cursor=cursor)
>           assert len(text) == len(expected), f"pagination lost {len(expected) - len(text)} evidence characters"
E           AssertionError: pagination lost 3816 evidence characters
E           assert 5434 == 9250
E            +  where 5434 = len('Research evidence: alpha beta gamma.\nReseara gamma.\nResearch evidence: alpha beta gamma.\nResearch evidence: alpha ...a.\nResearch evidence: alpha beta gamma.\nResearch evidence: alpha beta gamma.\nResearch evidence: alpha beta gamma.\n')
E            +  and   9250 = len('Research evidence: alpha beta gamma.\nResearch evidence: alpha beta gamma.\nResearch evidence: alpha beta gamma.\nRes...a.\nResearch evidence: alpha beta gamma.\nResearch evidence: alpha beta gamma.\nResearch evidence: alpha beta gamma.\n')

tests\unit\test_result_retention.py:244: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_result_retention.py::test_all_cursor_pages_retain_every_content_character[2000]
1 failed, 4 passed, 13 deselected in 1.30s
```

### Formatter GREEN

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/envelope.py tests/unit/test_result_retention.py; uv run --locked pytest -q tests/unit/test_result_retention.py tests/unit/test_envelope.py tests/unit/test_v15_state.py tests/unit/test_retrieval_regressions.py
```

Output:

```text
2 files reformatted
...................................................                      [100%]
51 passed in 2.10s
```

### Falsification: private-cache recovery and duplicated snippets RED

Command:

```powershell
uv run --locked pytest -q tests/unit/test_result_retention.py -k 'noncacheable_cursor or preserves_snippet'
```

Output:

```text
F.FF                                                                     [100%]
================================== FAILURES ===================================
______ test_noncacheable_cursor_cannot_recover_from_an_older_disk_entry _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1982/test_noncacheable_cursor_canno0')

    async def test_noncacheable_cursor_cannot_recover_from_an_older_disk_entry(tmp_path):
        service = service_at(tmp_path)
        source = ProviderResult("private-fixture", [EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T00:00:00Z", content="private fixture evidence " * 400)])
        service.cache.put("private-fixture-key", service._encode_result(source), 3600)
    
        async def operation():
            return source
    
        value = await service._cached_run("http", "fixture", "private-fixture-key", 3600, operation, cacheable=False)
        first = service._envelope("web_crawl", value, 2000)
        await service.close()
        restarted = service_at(tmp_path)
        try:
            result = restarted._resume("web_crawl", first["page"]["next_cursor"], None)
>           assert not result["ok"], "non-cacheable cursor recovered an old disk entry"
E           AssertionError: non-cacheable cursor recovered an old disk entry
E           assert not True

tests\unit\test_result_retention.py:293: AssertionError
___ test_pagination_preserves_snippet_and_content_without_duplication[both] ___

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1982/test_pagination_preserves_snip1')
kind = 'both'

    @pytest.mark.parametrize("kind", ["snippet", "both", "unicode"])
    async def test_pagination_preserves_snippet_and_content_without_duplication(tmp_path, kind):
        service = service_at(tmp_path)
        snippet = "Brief source summary. " * 20
        content = "Complete research source text. " * 300
        if kind == "snippet":
            snippet, content = snippet * 20, ""
        elif kind == "unicode":
            snippet, content = '"\\\\\\n \xe9 \u7814\u7a76 \U0001f50e "' * 80, "Research\\t\\n\U0001f4da" * 600
    
        async def fetch(url):
            return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", snippet=snippet, content=content)])
    
        service.http.fetch = fetch
        try:
            page = await service.web_fetch("https://example.org/", max_chars=2000)
            contents, snippets = [], []
            for _ in range(300):
                assert page["ok"], page
                wire = json.dumps(page, indent=2, ensure_ascii=False)
                assert len(wire) == page["page"]["serialized_chars"] <= 2000
                contents.extend(item.get("content") or "" for item in page["items"])
                snippets.extend(item.get("snippet") or "" for item in page["items"])
                if not page["page"]["next_cursor"]:
                    break
                page = await service.web_fetch(cursor=page["page"]["next_cursor"])
            else:
                pytest.fail("pagination did not terminate")
            assert "".join(contents) == content
>           assert len("".join(snippets)) == len(snippet), "snippet was repeated on content chunks"
E           AssertionError: snippet was repeated on content chunks
E           assert 16720 == 440
E            +  where 16720 = len('Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief s...ummary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. ')
E            +    where 'Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief s...ummary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. ' = <built-in method join of str object at 0x00007FF9C1F19CA0>(['Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief ...ief source summary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. ', '', ...])
E            +      where <built-in method join of str object at 0x00007FF9C1F19CA0> = ''.join
E            +  and   440 = len('Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief s...ummary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. Brief source summary. ')

tests\unit\test_result_retention.py:328: AssertionError
_ test_pagination_preserves_snippet_and_content_without_duplication[unicode] __

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1982/test_pagination_preserves_snip2')
kind = 'unicode'

    @pytest.mark.parametrize("kind", ["snippet", "both", "unicode"])
    async def test_pagination_preserves_snippet_and_content_without_duplication(tmp_path, kind):
        service = service_at(tmp_path)
        snippet = "Brief source summary. " * 20
        content = "Complete research source text. " * 300
        if kind == "snippet":
            snippet, content = snippet * 20, ""
        elif kind == "unicode":
            snippet, content = '"\\\\\\n \xe9 \u7814\u7a76 \U0001f50e "' * 80, "Research\\t\\n\U0001f4da" * 600
    
        async def fetch(url):
            return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", snippet=snippet, content=content)])
    
        service.http.fetch = fetch
        try:
            page = await service.web_fetch("https://example.org/", max_chars=2000)
            contents, snippets = [], []
            for _ in range(300):
                assert page["ok"], page
                wire = json.dumps(page, indent=2, ensure_ascii=False)
                assert len(wire) == page["page"]["serialized_chars"] <= 2000
                contents.extend(item.get("content") or "" for item in page["items"])
                snippets.extend(item.get("snippet") or "" for item in page["items"])
                if not page["page"]["next_cursor"]:
                    break
                page = await service.web_fetch(cursor=page["page"]["next_cursor"])
            else:
                pytest.fail("pagination did not terminate")
            assert "".join(contents) == content
>           assert len("".join(snippets)) == len(snippet), "snippet was repeated on content chunks"
E           AssertionError: snippet was repeated on content chunks
E           assert 25920 == 960
E            +  where 25920 = len('"\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n...\u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e "')
E            +    where '"\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n...\u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e "' = <built-in method join of str object at 0x00007FF9C1F19CA0>(['"\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\..."\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e "', ...])
E            +      where <built-in method join of str object at 0x00007FF9C1F19CA0> = ''.join
E            +  and   960 = len('"\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n...\u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e ""\\\\\\n \xe9 \u7814\u7a76 \U0001f50e "')

tests\unit\test_result_retention.py:328: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_result_retention.py::test_noncacheable_cursor_cannot_recover_from_an_older_disk_entry
FAILED tests/unit/test_result_retention.py::test_pagination_preserves_snippet_and_content_without_duplication[both]
FAILED tests/unit/test_result_retention.py::test_pagination_preserves_snippet_and_content_without_duplication[unicode]
3 failed, 1 passed, 18 deselected in 1.15s
```

### Falsification GREEN and adjacent regressions

Command:

```powershell
uv run --locked ruff format src/halo_research_gateway/service.py tests/unit/test_result_retention.py; uv run --locked pytest -q tests/unit/test_result_retention.py tests/unit/test_envelope.py tests/unit/test_retrieval_regressions.py tests/unit/test_v15_state.py tests/unit/test_crawl_options.py tests/unit/test_document_options.py tests/unit/test_job_continuation.py
```

Output:

```text
1 file reformatted, 1 file left unchanged
.....................................................................
... [ 60%]
...............................................                          [100%]
119 passed in 17.53s
```

### Intermediate full gate

Command:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

Output:

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
89 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
.................................................
....................... [ 23%]
........................................................................ [ 46%]
........................................................................ [ 69%]
........................................................................ [ 92%]
......................                                                   [100%]
310 passed in 60.19s (0:01:00)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

### Native two-client test and existing process-crash recovery

Command:

```powershell
uv run --locked ruff format tests/acceptance/test_result_retention_native.py; uv run --locked pytest -q tests/acceptance/test_result_retention_native.py; if($LASTEXITCODE){exit $LASTEXITCODE}; uv run --locked python tests/acceptance/job_process_recovery.py
```

Output:

```text
1 file left unchanged
.                                                                        [100%]
1 passed in 4.72s
{"passed": true, "native_process_crash_recovered": true, "search_repeated": false, "completed_source_refetched": false, "attempts": 3, "sources": ["https://example.org/task-groups", "https://example.org/cancellation"], "fixture_only": true}
```

### Final focused and full gate

Command:

```powershell
uv run --locked ruff format tests/unit/test_result_retention.py; uv run --locked pytest -q tests/unit/test_result_retention.py tests/unit/test_envelope.py; if($LASTEXITCODE){exit $LASTEXITCODE}; pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

Output:

```text
1 file reformatted
......................................                                   [100%]
38 passed in 1.91s
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
90 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
.....................................
................................... [ 22%]
........................................................................ [ 45%]
........................................................................ [ 68%]
........................................................................ [ 91%]
..........................                                               [100%]
314 passed in 59.81s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

### Final native MCP/document/crawl/cookie-WebSocket regression

Command:

```powershell
uv run --locked pytest -q tests/acceptance/test_result_retention_native.py tests/acceptance/test_document_native.py tests/acceptance/test_crawl_traversal_native.py tests/acceptance/test_local_research_browser.py
```

Output:

```text
.....
........                                                            [100%]
13 passed in 22.37s
```

