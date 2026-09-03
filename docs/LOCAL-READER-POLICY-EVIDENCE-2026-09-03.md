# Local research reader policy — September 3, 2026

## Outcome

Based on clean source `a6405493a89e6bfe03e6f19efa65261b5f7193dc`.
The two policy gaps explicitly left open in the response-bound checkpoint are
now fixed: local_fetch cannot perform GET unless the named target allows it,
and recognized sensitive query values are redacted from returned citation and
snapshot URLs. The raw authorized URL still reaches the exact source. Source
text and ordinary non-sensitive citations remain unchanged and fully pageable.
IPv6 brackets are retained by the shared redaction helper.

No tool, permission, account action, dependency, config field or provider was
added. Product stays 0.2.0 with fourteen tools. The changes use the existing
operator target policy and existing sensitive-name detector; this is not a
restriction on DSH's native capabilities.

## Exact verification scope

Relevant unchanged baseline: `54 passed in 2.56s`.
Ten new unit cases: nine assertions failed before the fix; the unchanged
ordinary-query case passed. No existing tests were changed or weakened.
Focused GREEN: `64 passed in 3.46s`.
Complete source gate: `451 passed in 78.61s (0:01:18)`, including skill validation.

Native Windows Gateway in disposable process/state/ports; two actual MCP clients,
actual loopback source. At each ERROR/INFO/DEBUG level, the denied target made no
source request, the allowed request carried the synthetic query value, and all
3400 content characters survived 13 cursor pages with one source request and
no disk cache. Neither returned evidence nor captured Gateway stdout/stderr
contained the synthetic query secret. This is observed fixture behavior, not
universal logging or secret-detection proof.

The native run also reran the previous response bounds, real unauthenticated
GitHub response, native retention/restart and cancellation tests unchanged:
`7 passed in 16.76s`. No real account, paid endpoint, personal profile or DSH
was used. The installed Gateway was not touched during these tests.

## Behavior and limitations

- A HEAD-only or empty method list returns LOCAL_METHOD_NOT_ALLOWED before
  HTTP queue admission/network I/O. local_fetch remains a GET reader, not a
  method-switching or general-purpose HTTP client.
- Recognized session/auth/key/signature parameter names reuse the public
  detector. Once sensitive, all citation query values are redacted and the
  fragment is removed; SENSITIVE_URL_NOT_CACHED is explicit.
- Snapshots contain only the redacted citation; local results remain off disk
  cache. Cursor continuation preserves collected text, not a new source request.
- The redacted citation may not reopen an authenticated source independently.
  Original URLs are not recovered from snapshots. Existing older snapshots in
  a running process are not rewritten; restarting drops those in-memory records.
- This does not scrub arbitrary fetched prose/embedded links/path secrets,
  unrecognized parameter names, existing logs, databases or historical receipts.
  A changed operator method policy does not erase already-collected evidence.
- The shared IPv6 formatting repair also applies to sensitive public/document/
  crawler citations. It does not change destination validation or DNS policy.
- a640549's decoded-response/network deadline limits remain separate from
  compressed-wire, decompressor/JSON, whole-GitHub-operation and native RAM limits.

## Delivery boundary and full objective

A subsequent successful commit hook, exact-SHA CI and ownership-checked idle
Gateway-only reload must be recorded in the operator delivery receipt before
claiming installed acceptance. This document records source/native tests, not
a prospective deployment as completed. Previous evidence is retained unchanged.

Full DSH dispatch/workflow/jobs acceptance still requires the scoped DSH repair/
restart decision; no DSH model, preset, permission or conversation is changed.
Real chosen research login, app-bound cookies, visible human challenge handling,
solver application, broad browser/provider/process/install/stress work, package
metadata/licensing and final source/site/runtime alignment remain unfinished.
Previously denied installed skill copies remain outside this change. Site v4
is still a dated snapshot of runtime 7cdfe72, not live monitoring.

## Review and security checklist

Read before modifying: current local reader/construction/error/snapshot paths,
security helpers and LocalTarget/config contracts, response-bound tests, existing
native process/MCP fixtures, logging setup/entrypoint, lifecycle scripts and
current scope/README/manual/operations/status. No lifecycle/logging code changed.

TDD and falsification: HEAD-only/empty policies, five sensitive-name forms,
ordinary query preservation, full cursor reassembly, snapshot/cache checks and
IPv6 parsing. Native ERROR/INFO/DEBUG checks, two clients and actual source hits
supplement the unit checks. Self-review only, not independent review.

- Trust boundaries: operator method list checked before network; known sensitive
  values excluded from returned citation/snapshot URLs.
- New routes/authn/authz: none. Existing local-target and fourteen-tool contracts.
- Secrets: all session values in tests/evidence are synthetic; no real credential
  was read or used. Repository scan/ignore review belongs to the delivery gate.
- Unsafe rendering/eval/deserialization: none introduced.
- Dependencies: none added/changed; existing metadata gaps remain.
- Blast radius: local_fetch and shared IPv6 redaction; all source tests pass.
- Performance: one method membership check and existing linear URL parsing;
  request queue/body limits from a640549 remain unchanged.
- Docs: README, CHANGELOG, manual, operations, status/progress, current scope and
  its repository-bundled copy updated together. Installed copies not overwritten.

## Exact commands and complete test output

### Relevant unchanged baseline

```powershell
uv run --locked python -m pytest -q tests/unit/test_research_response_bounds.py tests/unit/test_retrieval_regressions.py tests/unit/test_security.py tests/unit/test_research_scope.py
```

```text
......................................................                   [100%]
54 passed in 2.56s
```

### Assertion-based RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_local_reader_policy.py
```

```text
FFFFFFFF.F                                                               [100%]
================================== FAILURES ===================================
_ test_get_is_denied_before_network_when_operator_did_not_allow_it[methods0] __

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001EF8FD70B60>
service = <halo_research_gateway.service.HaloService object at 0x000001EF8FC34620>
methods = ['HEAD']

    @pytest.mark.parametrize("methods", [["HEAD"], []])
    async def test_get_is_denied_before_network_when_operator_did_not_allow_it(monkeypatch, service, methods):
        stream = Payload([b"must not be fetched"])
        calls = install(monkeypatch, stream)
        service.config.local_targets["fixture"].methods = methods
        result = await service.local_fetch("fixture", "/research/source")
>       assert not result["ok"] and result["error"]["code"] == "LOCAL_METHOD_NOT_ALLOWED"
E       assert (not True)

tests\unit\test_local_reader_policy.py:19: AssertionError
_ test_get_is_denied_before_network_when_operator_did_not_allow_it[methods1] __

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001EF8FD72E70>
service = <halo_research_gateway.service.HaloService object at 0x000001EF8FD72540>
methods = []

    @pytest.mark.parametrize("methods", [["HEAD"], []])
    async def test_get_is_denied_before_network_when_operator_did_not_allow_it(monkeypatch, service, methods):
        stream = Payload([b"must not be fetched"])
        calls = install(monkeypatch, stream)
        service.config.local_targets["fixture"].methods = methods
        result = await service.local_fetch("fixture", "/research/source")
>       assert not result["ok"] and result["error"]["code"] == "LOCAL_METHOD_NOT_ALLOWED"
E       assert (not True)

tests\unit\test_local_reader_policy.py:19: AssertionError
__________ test_session_query_reaches_source_but_not_evidence[token] __________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001EF8FD70890>
service = <halo_research_gateway.service.HaloService object at 0x000001EF8FD73EC0>
name = 'token'

    @pytest.mark.parametrize("name", ["token", "api_key", "X-Amz-Signature", "session", "auth_code"])
    async def test_session_query_reaches_source_but_not_evidence(monkeypatch, service, name):
        stream = Payload([b"Allowed research evidence"])
        calls = install(monkeypatch, stream)
        secret = "fixture-private-query-value"
        result = await service.local_fetch("fixture", f"/research/source?{name}={secret}&q=research")
        assert result["ok"], result
        assert calls[0].url.params[name] == secret
        assert result["items"][0]["content"] == "Allowed research evidence"
>       assert secret not in json.dumps(result)
E       assert 'fixture-pri...-query-value' not in '{"schema_ve...rnings": []}'
E
E         'fixture-private-query-value' is contained here:
E           rce?token=fixture-private-query-value&q=research", "published_at": null, "retrieved_at": "2026-09-03T07:00:21.665810Z", "source": "fixture", "snippet": null, "content": "Allowed research evidence", "metadata": {}}], "warnings": []}
E         ?           +++++++++++++++++++++++++++

tests\unit\test_local_reader_policy.py:33: AssertionError
_________ test_session_query_reaches_source_but_not_evidence[api_key] _________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001EF8FD73BF0>
service = <halo_research_gateway.service.HaloService object at 0x000001EF8FDF5BE0>
name = 'api_key'

    @pytest.mark.parametrize("name", ["token", "api_key", "X-Amz-Signature", "session", "auth_code"])
    async def test_session_query_reaches_source_but_not_evidence(monkeypatch, service, name):
        stream = Payload([b"Allowed research evidence"])
        calls = install(monkeypatch, stream)
        secret = "fixture-private-query-value"
        result = await service.local_fetch("fixture", f"/research/source?{name}={secret}&q=research")
        assert result["ok"], result
        assert calls[0].url.params[name] == secret
        assert result["items"][0]["content"] == "Allowed research evidence"
>       assert secret not in json.dumps(result)
E       assert 'fixture-pri...-query-value' not in '{"schema_ve...rnings": []}'
E
E         'fixture-private-query-value' is contained here:
E           e?api_key=fixture-private-query-value&q=research", "published_at": null, "retrieved_at": "2026-09-03T07:00:21.719477Z", "source": "fixture", "snippet": null, "content": "Allowed research evidence", "metadata": {}}], "warnings": []}
E         ?           +++++++++++++++++++++++++++

tests\unit\test_local_reader_policy.py:33: AssertionError
_____ test_session_query_reaches_source_but_not_evidence[X-Amz-Signature] _____

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001EF8FDF58B0>
service = <halo_research_gateway.service.HaloService object at 0x000001EF8FDF6AB0>
name = 'X-Amz-Signature'

    @pytest.mark.parametrize("name", ["token", "api_key", "X-Amz-Signature", "session", "auth_code"])
    async def test_session_query_reaches_source_but_not_evidence(monkeypatch, service, name):
        stream = Payload([b"Allowed research evidence"])
        calls = install(monkeypatch, stream)
        secret = "fixture-private-query-value"
        result = await service.local_fetch("fixture", f"/research/source?{name}={secret}&q=research")
        assert result["ok"], result
        assert calls[0].url.params[name] == secret
        assert result["items"][0]["content"] == "Allowed research evidence"
>       assert secret not in json.dumps(result)
E       assert 'fixture-pri...-query-value' not in '{"schema_ve...rnings": []}'
E
E         'fixture-private-query-value' is contained here:
E           Signature=fixture-private-query-value&q=research", "published_at": null, "retrieved_at": "2026-09-03T07:00:21.769990Z", "source": "fixture", "snippet": null, "content": "Allowed research evidence", "metadata": {}}], "warnings": []}
E         ?           +++++++++++++++++++++++++++

tests\unit\test_local_reader_policy.py:33: AssertionError
_________ test_session_query_reaches_source_but_not_evidence[session] _________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001EF8FDF7140>
service = <halo_research_gateway.service.HaloService object at 0x000001EF8FDF4080>
name = 'session'

    @pytest.mark.parametrize("name", ["token", "api_key", "X-Amz-Signature", "session", "auth_code"])
    async def test_session_query_reaches_source_but_not_evidence(monkeypatch, service, name):
        stream = Payload([b"Allowed research evidence"])
        calls = install(monkeypatch, stream)
        secret = "fixture-private-query-value"
        result = await service.local_fetch("fixture", f"/research/source?{name}={secret}&q=research")
        assert result["ok"], result
        assert calls[0].url.params[name] == secret
        assert result["items"][0]["content"] == "Allowed research evidence"
>       assert secret not in json.dumps(result)
E       assert 'fixture-pri...-query-value' not in '{"schema_ve...rnings": []}'
E
E         'fixture-private-query-value' is contained here:
E           e?session=fixture-private-query-value&q=research", "published_at": null, "retrieved_at": "2026-09-03T07:00:21.824501Z", "source": "fixture", "snippet": null, "content": "Allowed research evidence", "metadata": {}}], "warnings": []}
E         ?           +++++++++++++++++++++++++++

tests\unit\test_local_reader_policy.py:33: AssertionError
________ test_session_query_reaches_source_but_not_evidence[auth_code] ________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001EF8FDF6ED0>
service = <halo_research_gateway.service.HaloService object at 0x000001EF8FDF62A0>
name = 'auth_code'

    @pytest.mark.parametrize("name", ["token", "api_key", "X-Amz-Signature", "session", "auth_code"])
    async def test_session_query_reaches_source_but_not_evidence(monkeypatch, service, name):
        stream = Payload([b"Allowed research evidence"])
        calls = install(monkeypatch, stream)
        secret = "fixture-private-query-value"
        result = await service.local_fetch("fixture", f"/research/source?{name}={secret}&q=research")
        assert result["ok"], result
        assert calls[0].url.params[name] == secret
        assert result["items"][0]["content"] == "Allowed research evidence"
>       assert secret not in json.dumps(result)
E       assert 'fixture-pri...-query-value' not in '{"schema_ve...rnings": []}'
E
E         'fixture-private-query-value' is contained here:
E           auth_code=fixture-private-query-value&q=research", "published_at": null, "retrieved_at": "2026-09-03T07:00:21.882048Z", "source": "fixture", "snippet": null, "content": "Allowed research evidence", "metadata": {}}], "warnings": []}
E         ?           +++++++++++++++++++++++++++

tests\unit\test_local_reader_policy.py:33: AssertionError
_____ test_sensitive_local_cursor_preserves_text_without_restoring_query ______

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001EF8FDF53A0>
service = <halo_research_gateway.service.HaloService object at 0x000001EF8FD71FA0>

    async def test_sensitive_local_cursor_preserves_text_without_restoring_query(monkeypatch, service):
        body = "Pageable local evidence. " * 200
        service.config.http.max_decompressed_bytes = 10000
        stream = Payload([body.encode()])
        calls = install(monkeypatch, stream)
        secret = "fixture-paged-query-value"
        result = await service.local_fetch("fixture", f"/research/source?token={secret}", max_chars=2000)
        content, pages = "", 0
        while True:
            assert result["ok"], result
>           assert secret not in json.dumps(result)
E           assert 'fixture-paged-query-value' not in '{"schema_ve...TRUNCATED"]}'
E
E             'fixture-paged-query-value' is contained here:
E             ?           ^^
E               rce?token=fixture-paged-query-value", "published_at": null, "retrieved_at": "2026-09-03T07:00:21.939569Z", "source": "fixture", "snippet": null, "content": "Pageable local evidence. Pageable local evidence. Pageable local evidence. Pageable local evidence. Pageable local evidence. Pageable local evidence. Pageable local evidence. Pageable local evidence. Pageable local evidence. Pageable local evidence. ", "metadata": {"content_part": 1, "content_parts": 20}}], "warnings": ["RESULT_TRUNCATED"]}
E             ?           ^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_local_reader_policy.py:51: AssertionError
________ test_redacted_ipv6_citation_remains_a_parseable_exact_origin _________

    def test_redacted_ipv6_citation_remains_a_parseable_exact_origin():
        result = redact_url("http://[::1]:3090/research/source?token=fixture-value")
>       assert result == "http://[::1]:3090/research/source?token=%5BREDACTED%5D"
E       AssertionError: assert 'http://::1:3...5BREDACTED%5D' == 'http://[::1]...5BREDACTED%5D'
E
E         - http://[::1]:3090/research/source?token=%5BREDACTED%5D
E         ?        -   -
E         + http://::1:3090/research/source?token=%5BREDACTED%5D

tests\unit\test_local_reader_policy.py:75: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_local_reader_policy.py::test_get_is_denied_before_network_when_operator_did_not_allow_it[methods0]
FAILED tests/unit/test_local_reader_policy.py::test_get_is_denied_before_network_when_operator_did_not_allow_it[methods1]
FAILED tests/unit/test_local_reader_policy.py::test_session_query_reaches_source_but_not_evidence[token]
FAILED tests/unit/test_local_reader_policy.py::test_session_query_reaches_source_but_not_evidence[api_key]
FAILED tests/unit/test_local_reader_policy.py::test_session_query_reaches_source_but_not_evidence[X-Amz-Signature]
FAILED tests/unit/test_local_reader_policy.py::test_session_query_reaches_source_but_not_evidence[session]
FAILED tests/unit/test_local_reader_policy.py::test_session_query_reaches_source_but_not_evidence[auth_code]
FAILED tests/unit/test_local_reader_policy.py::test_sensitive_local_cursor_preserves_text_without_restoring_query
FAILED tests/unit/test_local_reader_policy.py::test_redacted_ipv6_citation_remains_a_parseable_exact_origin
9 failed, 1 passed in 2.32s
```

### Focused GREEN and unchanged regressions

```powershell
uv run --locked ruff check --select I --fix tests/unit/test_local_reader_policy.py
uv run --locked ruff format src/halo_research_gateway/service.py src/halo_research_gateway/security.py tests/unit/test_local_reader_policy.py
uv run --locked python -m pytest -q tests/unit/test_local_reader_policy.py tests/unit/test_research_response_bounds.py tests/unit/test_retrieval_regressions.py tests/unit/test_security.py tests/unit/test_research_scope.py
```

```text
Found 1 error (1 fixed, 0 remaining).
3 files left unchanged
................................................................         [100%]
64 passed in 3.46s
```

### Initial native check

```powershell
uv run --locked ruff format tests/acceptance/test_local_policy_native.py
uv run --locked python -m pytest -q -s tests/acceptance/test_local_policy_native.py
```

```text
1 file reformatted
Native local policy: denied target made zero requests; 3400 characters/13 pages; one source read; no disk cache.
.
1 passed in 3.39s
```

### All logging levels and prior native acceptance

```powershell
uv run --locked python -m pytest -q -s tests/acceptance/test_local_policy_native.py tests/acceptance/test_response_bounds_native.py tests/acceptance/test_result_retention_native.py tests/acceptance/test_cancellation_http.py
```

```text
Native local policy: denied target made zero requests; 3400 characters/13 pages; one source read; no disk cache.
.Native local policy: denied target made zero requests; 3400 characters/13 pages; one source read; no disk cache.
.Native local policy: denied target made zero requests; 3400 characters/13 pages; one source read; no disk cache.
.NATIVE local bounds: two MCP clients; 3200 characters/12 pages; initial source peak=1; overflow/compression/redirect/timeout rejected; subsequent read passed; cache entries=0; HTTP pending=0.
.NATIVE public GitHub: one-byte cap rejected real API response; normal-cap followup decoded resources.
...
7 passed in 16.76s
```

### Complete deterministic gate

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
106 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 15%]
........................................................................ [ 31%]
........................................................................ [ 47%]
........................................................................ [ 63%]
........................................................................ [ 79%]
........................................................................ [ 95%]
...................                                                      [100%]
451 passed in 78.61s (0:01:18)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```
