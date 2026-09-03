# Live Gateway and DSH checkpoint — 2026-09-02

Partial acceptance, not a completed project. Product version 0.2.0, research
surface fourteen tools. No non-research capability was added. No DSH setting,
package, model, permission, preset or service was changed/restarted here.

## Delivery and runtime identity

- Gateway source: `b178cbe622abd9372153e96f7c1cb534cee229b7`, pushed directly
  to private `origin/main`; exact remote SHA verified with `git ls-remote`.
- CI run [33697543325](https://github.com/scottconverse/halo-research-gateway/actions/runs/33697543325)
  completed successfully for that SHA. No PR merge or release tag was created.
- Gateway-only reload: health `ok`, version `0.2.0`, started_at
  `2026-09-02T23:59:44.28445Z`. Recorded parent PID 31368, creation record
  `2026-09-02T23:59:43.5082820Z`, executable repository `.venv\Scripts\python.exe`.
  These are dated identities, not permission to stop a reused PID.
- Reload preflight checked zero queued/running jobs, exact executable,
  Gateway command line, process creation time within two seconds of the
  record, and the existing scheduled-task action. Only Gateway was stopped
  and started through `Halo Research Gateway`; DSH/LM Studio were untouched.
- Corrected landing page was already published as owner-only Sites version
  3; exact source/version/deployment evidence is in
  [SITE-CORRECTION-2026-09-02.md](SITE-CORRECTION-2026-09-02.md).

This document and the reusable job canary are later evidence-only changes.
Their eventual commit/CI receipt must not be confused with b178cbe's receipt.

## Full deterministic gate

Command: `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`.

First restricted-process attempt failed before tests because it could not
read the existing native uv cache. This is not a test failure or a green run:

```text
[GATE] lock check
error: Failed to initialize cache at `C:\Users\scott\AppData\Local\uv\cache`
  Caused by: failed to open file `C:\Users\scott\AppData\Local\uv\cache\sdists-v9\.git`: Access is denied. (os error 5)
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | lock check failed with exit code 2
```

The same command under authorized native execution:

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
78 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
176 passed in 16.53s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

Only per-test dot output omitted. Exit 0; no test warning or skip reported.
Credential-pattern scan: 207 tracked text/instruction files, zero high-confidence
matches. This is a limited scan, not an exhaustive security audit. Ignore rules
cover local configuration, credentials, runtime data and build output. LICENSE
and CONTRIBUTING remain absent; no public package/license release is claimed.

## Live MCP fetch

Command: `uv run --locked python tests/acceptance/mcp_smoke.py`.

```text
{'tools': 14, 'web_fetch': 'ok', 'chars': 1381}
```

Exit 0 after the reload, using the actual Streamable HTTP endpoint.

## Fresh DSH workflow: FAILED

Command: `uv run --locked python tests/acceptance/dsh_research_workflow.py`.

```text
{"created_session": "session-411a80a4-05e6-409f-8fcd-cb445769e180", "baseline_sessions": 119}
{"model": {"provider": "lmstudio", "model": "halo/qwen3.6-35b-a3b"}}
{"session": "session-411a80a4-05e6-409f-8fcd-cb445769e180", "running": false, "events": 52, "last_types": ["tool/call", "step/end", "turn/end", "session/title"]}
{"workflow_verdict": {"passed": false, "turn_end": {"kind": "error", "error": {"message": "Cannot read properties of undefined (reading 'prepare')", "code": "UNKNOWN"}}, "calls": ["mcp__halo_research__web_search"], "result_events": 0, "cursor_used": false, "fetched_urls": [], "final": "I'll use the Halo Research Gateway tools to answer this question about Python asyncio TaskGroup behavior.\n\n", "semantic_evidence_review_required": true}}
{"finished": true, "missing_existing_sessions": 0}
```

Exit 1. The model chose the expected tool but received no results and produced
no supported research answer. This revalidates the failure despite newer
separate DSH work. The earlier package-instance/scheduler-symbol diagnosis is
in [DSH-WORKFLOW-CANCELLATION-2026-09-02.md](DSH-WORKFLOW-CANCELLATION-2026-09-02.md).
Scoped DSH repair/restart approval is still requested, not assumed.

## Live Gateway job controls: PASS, with partial evidence

Commands:

```powershell
uv run --locked ruff format tests/acceptance/mcp_job_lifecycle.py
uv run --locked ruff check tests/acceptance/mcp_job_lifecycle.py
uv run --locked python tests/acceptance/mcp_job_lifecycle.py
```

```text
1 file left unchanged
All checks passed!
{"created_job": "2fbc8124-1312-4317-bf86-447fad038b48", "limits": {"profile": "standard", "max_sources": 2, "max_pages": 3, "timeout_seconds": 45}}
{"pause": "passed", "checkpoint_frozen": true}
{"job_id": "2fbc8124-1312-4317-bf86-447fad038b48", "state": "complete", "error_code": null, "checkpoint": {"attempted": 2, "completed_sources": 2, "remaining_sources": 1, "elapsed_seconds": 0.9530000000086147, "search_complete": true}, "partial": true, "warnings": ["CROSS_SITE_LINK_SKIPPED", "DUPLICATE_URL_SKIPPED", "PAGE_LIMIT_REACHED", "PROVIDER_FALLBACK_USED", "RESULT_TRUNCATED", "SOURCE_LIMIT_REACHED"], "source_urls": ["https://docs.python.org/3/library/asyncio-task.html"], "status_chars": 4492}
{"evidence_cursor": "passed", "page_source_urls": ["https://docs.python.org/3/library/asyncio-task.html"]}
{"live_gateway_job_canary": "PASS", "dsh_proof": false, "crash_proof": false}
```

Exit 0. This used real accountless DDGS discovery through the live job path
and ordinary public-page retrieval. It did not force `web_search`'s Exa-to-DDGS
fallback branch, prove two-source synthesis, stress the service, or crash the
production process. Pause was near job start, not mid-page completion. Saved
source continuation after a crash is separately proven by the disposable native
process fixture in [DURABLE-JOB-EVIDENCE-2026-09-02.md](DURABLE-JOB-EVIDENCE-2026-09-02.md).

The 4000-character budget is the embedded evidence envelope, not the entire
4492-character status object. Source/page-limit warnings are expected bounded
coverage, not hidden completeness. The evidence cursor was followed once,
not to exhaustion. No private account/profile or paid provider was used.

An earlier inline client probe used `response.isError`, but this installed MCP
SDK exposes `is_error`. The probe errored after its create call; it is not
counted as a successful control test. The corrected reusable canary above
uses the installed field and cancels only its own job if interrupted. A
separate corrected create/cancel diagnostic created and cancelled only
`ef6177a3-8087-4139-8347-9f4baf83618a`. Final health reported zero queued,
running and paused jobs, one cancelled and two completed test jobs; records
are retained, not deleted. Read-only queries from Codex initially returned no
rows even after loading the same configuration. The diagnostic cause and
native verification follow; those empty queries are not evidence of lost jobs.

## Windows AppData diagnostic trap: resolved

Codex's MSIX context redirected database reads under the normal AppData path
to `C:\Users\scott\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HaloResearchGateway`.
The permissions tool explicitly returned that resolved path. Normal and volume
paths from the packaged process still saw the old copy (zero jobs, 99 cache
entries); the live service reported three jobs and seven cache entries. The
Gateway listener PID 51240, child of recorded parent 31368, held the normal
host database/WAL/SHM paths. Do not diagnose host data loss from the packaged
process's redirected view.

A disposable, limited-privilege, on-demand scheduled task ran a read-only
Python probe outside that redirected environment. It loaded the Gateway's
normal config and queried only the public canary question created in this
checkpoint. No database rows/configuration were changed. Both the initial
inline client's completed job and the final canary were present:

```text
{"configured_database": "C:\\Users\\scott\\AppData\\Local\\HaloResearchGateway\\state\\gateway.db", "canary_jobs": [{"id": "eb7ed4e1-7936-4608-ae23-22272e97b30f", "state": "complete", "created_at": "2026-09-03T00:01:54.537025Z", "error_code": null}, {"id": "ef6177a3-8087-4139-8347-9f4baf83618a", "state": "cancelled", "created_at": "2026-09-03T00:02:57.100065Z", "error_code": null}, {"id": "2fbc8124-1312-4317-bf86-447fad038b48", "state": "complete", "created_at": "2026-09-03T00:03:50.262434Z", "error_code": null}], "read_only": true, "passed": true}
```

Task last run `2026-09-02T18:14:59-06:00`, LastTaskResult `0`; only
`Halo Research Gateway DB Read Canary b178cbe` was unregistered afterward.
The first probe was stopped too early when its output file appeared; its
LastTaskResult was `267009` (still running), so it was not counted as a pass.
The corrected run waited for actual task completion. The helper and output
remain under the Codex task's `outputs/gateway-native-db-probe*` paths, not
installed into the product. No recurring task remains.

## Evidence-only change verification

After adding the reusable live canary and updating scope/status docs:
`pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`.

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
79 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
176 passed in 15.26s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

Only per-test dots omitted. Exit 0, no skips or test warnings reported.
Git also reported normal Windows line-ending warnings for edited Markdown:
`LF will be replaced by CRLF the next time Git touches it`; no diff-check
error was reported. Source behavior is unchanged from the deployed b178cbe.

## Remaining acceptance

The [research-only finish list](RESEARCH-ONLY-SCOPE.md#needs-to-be-done-to-finish)
remains open: DSH dispatch/full workflow; chosen real login/app-bound cookies;
human challenge/provider routing; wider cancellation/concurrency/response and
startup/install reliability; configured GitHub and forced search-fallback
coverage; final documentation/metadata delivery. No email, posting, shopping,
account actions or broad personal-profile migration belongs in this work.

The reusable canary and documentation add no production behavior; no new TDD
claim is made for them. Durable-job production changes have separate RED/GREEN
evidence. Inputs and routes/authentication are unchanged; no dependency,
credential, unsafe rendering/eval/deserialization or account capability was
added by this checkpoint.
