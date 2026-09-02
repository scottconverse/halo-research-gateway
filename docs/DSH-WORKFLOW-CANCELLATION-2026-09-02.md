# DSH workflow failure and active-cancellation checkpoint — 2026-09-02

## Actual DSH result: FAILED

Ran `uv run --locked python tests/acceptance/dsh_research_workflow.py` against existing production DSH, with no model or settings changes. Created only `session-f011b834-ec16-4270-ac7e-753e7a2f231c`; all 118 prior sessions remained. The session used `lmstudio / halo/qwen3.6-35b-a3b`, with danger-full-access and approval policy never unchanged. It selected `mcp__halo_research__web_search`, but there were zero tool-result events, no cursor use, no fetched pages and no supported answer.

```text
Cannot read properties of undefined (reading 'prepare')
```

The initial runner exited 0 when it saw turn/end; that was runner completion, not workflow success, and was explicitly reported as failure during execution. The runner now produces a failed verdict and exits nonzero for this state. An initial placeholder evaluator test was discarded; the real runner assertion RED below exercises its main function with deterministic RPC error responses.

Read-only DSH diagnostics found that the host resolves dsh-tools from `C:\Users\scott\.dsh\profiles\web\node_modules\@deepseek-ai\dsh-tools\lib\index.js`, while agent-loop resolves a separate pnpm store instance. Both are version 0.1.1-rc.2 but their exported TOOL_RUNTIME_SCHEDULER symbols are unequal. Source tool-calls.ts:169 accesses that symbol's prepare method. This is the identified package-instance mismatch consistent with the exact failure; repair/retest has not been performed. No DSH source, package, preset, permission, model setting or service was changed. Scott was asked for permission to repair package resolution and restart the idle cockpit.

## Delivery/runtime status

Six checkpoints were fast-forward pushed to existing private origin/main at `135cdd8c231bfe986343cd6fb538dc000f76fb89`. CI [33691709059](https://github.com/scottconverse/halo-research-gateway/actions/runs/33691709059) returned status completed, conclusion success for that exact SHA. There was no PR merge or release tag. Version remains 0.2.0. A credential-pattern scan found zero matches across 192 tracked text files, plus the ignored local AGENTS file; this is a limited pattern scan, not an exhaustive security audit. No public package release is implied; LICENSE/CONTRIBUTING are absent.

Gateway was reloaded through its existing scheduled task at 2026-09-02T22:45:42.598427Z. A subsequent paced live MCP reddit_thread call returned the source post and four comment entries, with canonical per-comment URLs and RESULT_TRUNCATED, no error. This fixes the earlier matrix's last failing source case but is not a substitute for a full repeated matrix or DSH proof.

## Active cancellation

Baseline: preceding full commit gate `151 passed in 12.49s`. Found that cancelled active calls continued after their last waiter detached. The coordinator now retains the running task and cancels it when no caller needs it. A second regression confirms cancelling one caller does not interrupt another client's shared read. Durable-job pause/resume still needs separate implementation and tests.

### Cancellation RED

`uv run --locked python -m pytest -q tests/unit/test_active_cancellation.py`

```text
F.                                                                       [100%]
================================== FAILURES ===================================
___ test_last_cancelled_waiter_stops_active_upstream_and_releases_capacity ____

    @pytest.mark.asyncio
    async def test_last_cancelled_waiter_stops_active_upstream_and_releases_capacity():
        coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
        entered, stopped, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    
        async def operation():
            entered.set()
            try:
                await release.wait()
            finally:
                stopped.set()
    
        request = asyncio.create_task(coordinator.run("http", "a", "key", operation))
        try:
            await entered.wait()
            request.cancel()
            with pytest.raises(asyncio.CancelledError):
                await request
            for _ in range(5):
                await asyncio.sleep(0)
>           assert stopped.is_set()
E           assert False
E            +  where False = is_set()
E            +    where is_set = <asyncio.locks.Event object at 0x000001D9D2F2F500 [unset]>.is_set

tests\unit\test_active_cancellation.py:28: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_active_cancellation.py::test_last_cancelled_waiter_stops_active_upstream_and_releases_capacity
1 failed, 1 passed in 0.15s

```

### Actual DSH runner RED

`uv run --locked python -m pytest -q tests/unit/test_dsh_acceptance_verdict.py`

```text
F                                                                        [100%]
================================== FAILURES ===================================
______ test_dsh_finished_turn_with_runtime_error_is_not_workflow_success ______

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000020BFABB1EB0>

    @pytest.mark.asyncio
    async def test_dsh_finished_turn_with_runtime_error_is_not_workflow_success(monkeypatch):
        acceptance = runpy.run_path(str(Path(__file__).parents[1] / "acceptance" / "dsh_research_workflow.py"))
        history = {"events": [{"event": {"type": "turn/end", "data": {"reason": {"kind": "error", "error": {"message": "Cannot read properties of undefined (reading 'prepare')"}}}}}]}
    
        def respond(request):
            method = json.loads(request.content)["method"]
            values = {"session.list": {"items": [{"sessionId": "test-owned", "running": False}]}, "session.create": {"sessionId": "test-owned"}, "session.models": {"current": {"provider": "fixture", "model": "fixture"}}, "session.prompt": {}, "session.history": history}
            return httpx.Response(200, json={"result": {"ok": True, "value": values[method]}})
    
        original_client = httpx.AsyncClient
        monkeypatch.setattr(httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs))
        original_sleep = asyncio.sleep
    
        async def tick(_):
            await original_sleep(0)
    
        monkeypatch.setattr(asyncio, "sleep", tick)
>       assert await acceptance["main"]() == 1
E       assert 0 == 1

tests\unit\test_dsh_acceptance_verdict.py:28: AssertionError
---------------------------- Captured stdout call -----------------------------
{"created_session": "test-owned", "baseline_sessions": 1}
{"model": {"provider": "fixture", "model": "fixture"}}
{"session": "test-owned", "running": false, "events": 1, "last_types": ["turn/end"]}
{"owned_history": {"events": [{"event": {"type": "turn/end", "data": {"reason": {"kind": "error", "error": {"message": "Cannot read properties of undefined (reading 'prepare')"}}}}}]}}
{"finished": true, "missing_existing_sessions": 0}
=========================== short test summary info ===========================
FAILED tests/unit/test_dsh_acceptance_verdict.py::test_dsh_finished_turn_with_runtime_error_is_not_workflow_success
1 failed in 0.14s

```

### GREEN

`uv run --locked python -m pytest -q tests/unit/test_active_cancellation.py tests/unit/test_v15_state.py`:

```text
14 passed in 1.26s
```

`uv run --locked python -m pytest -q tests/unit/test_dsh_acceptance_verdict.py tests/unit/test_active_cancellation.py`:

```text
3 passed in 0.03s
```

First full-gate attempt found ASYNC240 at dsh_research_workflow.py:85 (Path.resolve inside async main) and I001 at test_dsh_acceptance_verdict.py:1 (import ordering). The acceptance path is now resolved at module load, mkdir runs in a worker thread, and imports are sorted. No production behavior was changed for those lint fixes.

Final commands:

```powershell
uv run --locked ruff format src tests
pwsh -NoProfile -File scripts/Update-BuildManifest.ps1
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
75 files left unchanged
Wrote BUILD-MANIFEST.json with 199 files.
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
75 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 46%]
........................................................................ [ 93%]
..........                                                               [100%]
154 passed in 12.68s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)

```

Read before editing: coordinator, existing cancellation tests, actual DSH API schemas/runner, affected docs. No dependency added. Falsification covered a sole active waiter, two clients sharing one call, and a completed DSH turn with a runtime error. Full job, login/challenge, process/install, final delivery and DSH proof remain unfinished; see RESEARCH-ONLY-SCOPE.md for the revised finish list.

