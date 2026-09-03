# GitHub whole-operation bounds — source/native evidence, September 3

## Result and identity

Whole GitHub research/discussion operations now share a deadline and aggregate
decoded-response byte ceiling across token setup and every API follow-up.
The source change is based on clean `4df0ccc4f686a872a040e3464a4783c87ca45a08`.
Version remains 0.2.0, result schema 1.5, database schema 3 and fourteen tools.
The installed service was not restarted for this checkpoint. Do not infer
installed, DSH or real-account acceptance from these tests.

Exact commands and full failure/error/warning output:
[raw verification record](evidence/github-operation-bounds-20260903.json).
That record retains failed attempts, not only the final passes.

## What changed and why

Before: each HTTP request was bounded, but a sequence of individually valid
responses could accumulate arbitrary elapsed time relative to the configured
request deadline, or many times its byte ceiling. Token-lock waiting was not
within that deadline.

Now: public provider research and discussion-thread entry points scope the
whole operation. Task-local byte accounting resets on every exit and remains
independent across concurrent callers. All real API responses, including token
minting, consume the shared decoded-byte ceiling. Existing per-response checks
remain. The existing HTTP settings supply both limits; no new setting, tool,
permission gate, endpoint or dependency was introduced.

Exhaustion is GITHUB_OPERATION_TIMEOUT or GITHUB_OPERATION_TOO_LARGE. A failed
operation returns no items or cursor; previously read sources in that failed
attempt are not retained. This matches fatal-provider failure behavior and avoids
success-shaped incomplete evidence or authenticated-to-public fallback. Normal
completed partial results and retained pagination are unchanged.

External cancellation stays cancellation. A request-specific timeout remains
GITHUB_REQUEST_TIMEOUT unless the whole deadline expired. The operation waits
for asynchronous cleanup. Synchronous/native work cannot be preempted; a
late result is rejected after control returns. Queue wait is outside this active
provider deadline. Mixed-community work has other providers outside this scope.

## Test-first evidence

Relevant baseline:
```powershell
uv run --locked python -m pytest -q tests/unit/test_github_provider.py tests/unit/test_research_response_bounds.py
```
```text
30 passed in 2.38s
```

New regressions before implementation:
```powershell
uv run --locked python -m pytest -q tests/unit/test_github_operation_bounds.py
```
```text
9 failed, 1 passed in 1.85s
```

Four sequence cases cover kinds, ref traversal, nested discussions and token minting.
Other cases cover token-lock waiting, streamed aggregate bytes, token-body accounting,
concurrent callers/reset, external cancellation and service-visible safe errors.

The first implementation produced `4 failed, 36 passed in 3.20s`: all four
failures were the fixture's exact second-request assertion, because a 60 ms
Windows budget could expire during the first 40 ms sleep. The timing was changed
to 100/200 ms requests inside 250 ms, retaining the same two-request/closure
assertions. The rerun was `40 passed in 3.42s`.

Falsification adds forced concurrent overlap, request-error code preservation and
deliberately synchronous over-deadline work:
```text
51 passed in 3.47s
```
That combined command also reported four lint findings. Imports were mechanically
sorted, disconnect polling became an Event, and only the deliberate synchronous
test stall has an explained ASYNC251 annotation. No production lint suppression
or weakened existing assertion was added. Full findings are in the JSON.

## Native process and MCP evidence

A disposable Gateway process exposes the real fourteen tools to two native MCP
clients. A test-process-only exact synthetic-host DNS mapping connects production
HTTPX/PinnedTransport streaming to an owned loopback fake GitHub API. Synthetic
credentials only; no personal vault, real GitHub account, public DNS, paid call,
installed-service restart or DSH configuration change.

The initial fixture used a private literal and correctly failed UNSAFE_URL.
Production URL checks were not changed. Two later fixture failures used the
wrong PR route assumption; GitHub issue/PR searches both use /search/issues with
different query qualifiers. Fixing that fake-API routing made the test exercise
the required second-request disconnect. Timing was also given native transport
setup margin; each individual simulated response remains below the operation's
3-second budget, while the sequence exceeds it.

Final command:
```powershell
uv run --locked ruff check --select I --fix tests/unit/test_github_operation_bounds.py tests/acceptance/test_github_operation_native.py
uv run --locked ruff format tests/unit/test_github_operation_bounds.py tests/acceptance/test_github_operation_native.py
uv run --locked ruff check src/halo_research_gateway/providers/github.py tests/unit/test_github_operation_bounds.py tests/acceptance/test_github_operation_native.py
uv run --locked python -m pytest -q -s tests/acceptance/test_github_operation_native.py
```
```text
Found 2 errors (2 fixed, 0 remaining).
2 files left unchanged
All checks passed!
{"tools": 14, "mcp_clients": 2, "aggregate_error": "GITHUB_OPERATION_TOO_LARGE", "deadline_error": "GITHUB_OPERATION_TIMEOUT", "second_request_disconnected": true, "followup_source_counts": [2, 2], "http_pending": 0, "cache_entries": 0, "real_github_authentication": false}
.
1 passed in 6.65s
```

The test requires aggregate/deadline error codes, empty failed evidence, absence
of synthetic secrets from MCP/log output, observed second-request disconnection,
two successful sources for each subsequent concurrent client, zero pending HTTP
work and zero disk-cache entries. Cleanup uses only the exact owned process handle
and always closes the fixture listener. This proves fake-API transport integration,
not GitHub availability/authentication or complete installation acceptance.

## Full gate

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```
```text
523 passed in 79.61s (0:01:19)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)
```

## Scope review and limitations

Read before changes: governing scope/AGENTS, GitHub provider/token/search/ref/
discussion paths, service error/coordinator integration, community use, HTTP
transport, relevant unit/native tests, quality gate and affected README/manual/
changelog/status/configuration sections.

Security review:
- Trust-boundary streamed bytes counted before appending; existing URL/DNS,
  repository/ref and API response-shape checks retained.
- No new routes/auth model; existing encrypted connections and authorization unchanged.
- No credentials added; fixtures use synthetic strings/generated transient keys.
  Gitignore still excludes local config/env/vault/runtime/key files.
- No eval, unsafe rendering or new deserialization introduced.
- Dependency vulnerability review: not applicable to this change; no dependency changed.

Adjacent GitHub/token/community and HTTP request-limit tests pass. The cumulative
cap may reject a broad query previously allowed to exceed the intended workload;
the manual explains narrowing it or deliberately adjusting existing settings.

Not proved/fixed: real installed authenticated GitHub/DSH, all upstream pagination,
wider origin scheduling, hard JSON/decompression/native RAM bounds, synchronous
preemption, general provider cancellation, complete DSH synthesis/pause/resume,
real login/challenges, paid use, broad install/stress or final release delivery.
No push, merge or 0.3.0 tag is claimed. The full finish list remains
[research-only scope](RESEARCH-ONLY-SCOPE.md).
