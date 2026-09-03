# Coordinator cancellation evidence — 2026-09-02

Scope: Gateway queue reliability only. No DSH setting/service, private account,
paid provider, optional feature, or public API was changed. This is one part
of the active research-only completion goal, not full acceptance.

## Change and boundaries

Three independent bugs were reproduced before changing production code:
new callers joined an already-cancelled shared read; cancellation after a
provider returned could interrupt settlement and leak its queue slot; and a
second caller cancellation could abandon waiter detachment and leave upstream
work running. Done-callback settlement now owns provider cleanup, waiter
cleanup is shielded and retained, and a stopping flight is removed by identity
from the join map while keeping its admission/active slot until actual exit.
An old flight cannot remove its replacement. Existing shared results, FIFO/
round-robin scheduling, saturation and pacing semantics remain tested.

Read before edits: coordinator, cancellation tests, clock, scheduler/state
fixtures, relevant job tests and affected README/manual/scope/changelog.
No dependency or network policy changed. Lifecycle inputs are internal task
state; public input/authentication routes unchanged. No secrets, unsafe
rendering/eval/deserialization or new provider access introduced.

## Baselines

Command: `uv run --locked python -m pytest -q tests/unit/test_active_cancellation.py tests/unit/test_job_lifecycle.py tests/unit/test_job_continuation.py`

```text
24 passed in 3.82s
```

Command: `uv run --locked python -m pytest -q tests/unit/test_v15_state.py tests/unit/test_active_cancellation.py`

```text
14 passed in 1.13s
```

These passed against unchanged production code. No pre-existing failure or
warning was reported. The prior full checkpoint had 176 tests; seven cases
were added to the deterministic suite in this change.

## Three race regressions — RED

Command: `uv run --locked python -m pytest -q tests/unit/test_active_cancellation.py`

```text
..FFF                                                                    [100%]
================================== FAILURES ===================================
________ test_new_call_during_cancel_cleanup_starts_fresh_shared_read _________

    @pytest.mark.asyncio
    async def test_new_call_during_cancel_cleanup_starts_fresh_shared_read():
        coordinator = Coordinator({"http": QueuePolicy(4, 4, 1)})
        entered, cleaning, release_cleanup = asyncio.Event(), asyncio.Event(), asyncio.Event()
        replacement_entered, release_replacement = asyncio.Event(), asyncio.Event()
        calls = []
    
        async def abandoned():
            calls.append("abandoned")
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                cleaning.set()
                await release_cleanup.wait()
    
        async def replacement():
            calls.append("replacement")
            replacement_entered.set()
            await release_replacement.wait()
            return "fresh evidence"
    
        first = asyncio.create_task(coordinator.run("http", "a", "same", abandoned))
        tasks = [first]
        try:
            await entered.wait()
            first.cancel()
            await asyncio.gather(first, return_exceptions=True)
            await cleaning.wait()
            second = asyncio.create_task(coordinator.run("http", "b", "same", replacement))
            tasks.append(second)
            await asyncio.sleep(0)
            assert not replacement_entered.is_set(), "cancel cleanup must retain its active slot"
            release_cleanup.set()
            for _ in range(12):
                await asyncio.sleep(0)
            third = asyncio.create_task(coordinator.run("http", "c", "same", replacement))
            tasks.append(third)
            await asyncio.sleep(0)
            release_replacement.set()
            results = await asyncio.wait_for(asyncio.gather(second, third, return_exceptions=True), 1)
>           assert results == ["fresh evidence", "fresh evidence"]
E           AssertionError: assert [CancelledErr...esh evidence'] == ['fresh evide...esh evidence']
E             
E             At index 0 diff: CancelledError('') != 'fresh evidence'
E             Use -v to get more diff

tests\unit\test_active_cancellation.py:107: AssertionError
________ test_cancel_after_operation_returns_still_releases_queue_slot ________

    @pytest.mark.asyncio
    async def test_cancel_after_operation_returns_still_releases_queue_slot():
        coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
        entered, return_result = asyncio.Event(), asyncio.Event()
    
        async def operation():
            entered.set()
            await return_result.wait()
            return "evidence"
    
        request = asyncio.create_task(coordinator.run("http", "a", "first", operation))
        await entered.wait()
        # Force waiter detachment ahead of result settlement at the state-lock boundary.
        async with coordinator._state_lock:
            request.cancel()
            await asyncio.sleep(0)
            return_result.set()
            await asyncio.sleep(0)
        await asyncio.gather(request, return_exceptions=True)
        for _ in range(12):
            await asyncio.sleep(0)
>       assert coordinator.stats()["http"]["pending"] == 0
E       assert 1 == 0

tests\unit\test_active_cancellation.py:139: AssertionError
_____ test_repeated_caller_cancellation_cannot_abandon_waiter_detachment ______

    @pytest.mark.asyncio
    async def test_repeated_caller_cancellation_cannot_abandon_waiter_detachment():
        coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
        entered, stopped, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    
        async def operation():
            entered.set()
            try:
                await release.wait()
            finally:
                stopped.set()
    
        request = asyncio.create_task(coordinator.run("http", "a", "first", operation))
        try:
            await entered.wait()
            async with coordinator._state_lock:
                request.cancel()
                await asyncio.sleep(0)
                request.cancel()
                await asyncio.gather(request, return_exceptions=True)
            for _ in range(12):
                await asyncio.sleep(0)
>           assert stopped.is_set(), "repeat cancellation must not strand active upstream work"
E           AssertionError: repeat cancellation must not strand active upstream work
E           assert False
E            +  where False = is_set()
E            +    where is_set = <asyncio.locks.Event object at 0x000001A93A585D60 [unset]>.is_set

tests\unit\test_active_cancellation.py:165: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_active_cancellation.py::test_new_call_during_cancel_cleanup_starts_fresh_shared_read
FAILED tests/unit/test_active_cancellation.py::test_cancel_after_operation_returns_still_releases_queue_slot
FAILED tests/unit/test_active_cancellation.py::test_repeated_caller_cancellation_cannot_abandon_waiter_detachment
3 failed, 2 passed in 0.17s
```

These were assertion failures, not setup errors. Tests control event ordering
at the state-lock seam and assert actual caller results, upstream termination,
replacement deduplication and released capacity. They do not substitute a mock
implementation of the coordinator.

## GREEN and adjacent scheduler/jobs

Commands:

```powershell
uv run --locked ruff format src/halo_research_gateway/coordinator.py tests/unit/test_active_cancellation.py
uv run --locked python -m pytest -q tests/unit/test_active_cancellation.py tests/unit/test_v15_state.py tests/unit/test_job_lifecycle.py tests/unit/test_job_continuation.py
```

```text
2 files left unchanged
.......................................                                  [100%]
39 passed in 4.07s
```

## Falsification

Added cancellation before the provider's first instruction, cancellation while
waiting for pacing, and multi-client success/error/cancellation batches (one
round and 25 rounds). A round creates 12 callers for four shared keys, cancels
six callers including every waiter of one queued read, and checks all remaining
results. Only three provider calls start per round; active concurrency stays
at or below two, all counters return to zero, no flights or cleanup tasks remain.
These are fast deterministic batches, not a multi-hour host soak.

While adding these tests, an insertion initially split a try/finally block.
Formatting/lint/pytest rejected the test file; this was an editing error, not
another production RED. After fixing block placement, lint found the following
late-bound test closure, also corrected before running the tests:

```text
1 file reformatted, 1 file left unchanged
B023 Function definition does not bind loop variable `release`
   --> tests\unit\test_active_cancellation.py:252:103
    |
250 |                 requests.append(
251 |                     asyncio.create_task(
252 |                         coordinator.run("http", client, f"{number}:{key}", lambda k=key: operation(k, release))
    |                                                                                                       ^^^^^^^
253 |                     )
254 |                 )
    |

Found 1 error.
```

Commands after correcting the test edits:

```powershell
uv run --locked ruff format src/halo_research_gateway/coordinator.py tests/unit/test_active_cancellation.py
uv run --locked ruff check src/halo_research_gateway/coordinator.py tests/unit/test_active_cancellation.py
uv run --locked python -m pytest -q tests/unit/test_active_cancellation.py
```

```text
1 file reformatted, 1 file left unchanged
All checks passed!
.........                                                                [100%]
9 passed in 0.06s
```

## Full deterministic gate

Command: `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
79 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 39%]
................................................
........................ [ 78%]
.......................................                                  [100%]
183 passed in 14.71s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

Exit 0. No skipped test or test warning reported.

## Real HTTP transport fixture

Commands:

```powershell
uv run --locked ruff format tests/acceptance/test_cancellation_http.py
uv run --locked ruff check tests/acceptance/test_cancellation_http.py
uv run --locked python -m pytest -q tests/acceptance/test_cancellation_http.py
```

```text
1 file left unchanged
All checks passed!
.                                                                        [100%]
1 passed in 0.18s
```

Three clients share one actual HTTPX request to a disposable loopback TCP
server. Cancelling two retains the read; cancelling the final caller closes
the connection (server observes EOF). A new same-key read returns fresh
response evidence. Only two connections were made, and no pending queue or
cleanup task remains. The fixture closes its own listener/clients/handlers.
It does not change public URL policy, contact external sites, use the full
HTTP-fetch policy adapter, or run through deployed MCP/DSH. This distinction
is intentional evidence scope, not a substitute for those remaining tests.

## Remaining

DDGS's synchronous thread cannot be forcibly stopped by async cancellation.
Broad browser/provider shutdown, startup ownership, memory/response bounds,
ignored research options, installation, real login/challenges, connected
GitHub and the blocked DSH workflow remain in the main finish list. See
RESEARCH-ONLY-SCOPE.md. No claim of complete project or all cancellation
behavior is made. Commit/deployment/CI identity is recorded separately once
verified; this source evidence alone does not prove the running process.

## Native job regression after coordinator changes

Command: `uv run --locked python tests/acceptance/job_process_recovery.py`.

```text
{"passed": true, "native_process_crash_recovered": true, "search_repeated": false, "completed_source_refetched": false, "attempts": 3, "sources": ["https://example.org/task-groups", "https://example.org/cancellation"], "fixture_only": true}
```

Exit 0; this is the disposable process fixture, not a production crash.
Subsequent `uv run --locked ruff check src tests` printed
`All checks passed!`. Git diff checks returned 0, with the standard Windows
LF-to-CRLF warnings on edited source/Markdown files. No content error reported.

## Initial test-edit error (not product RED)

Commands: `uv run --locked ruff format src/halo_research_gateway/coordinator.py tests/unit/test_active_cancellation.py`, then
`uv run --locked ruff check src/halo_research_gateway/coordinator.py tests/unit/test_active_cancellation.py`, then
`uv run --locked python -m pytest -q tests/unit/test_active_cancellation.py`.

The commands did not stop after the initial formatter failure; every step
rejected the same misplaced test block. No passing test claim comes from this run.

```text
error: Failed to parse tests\unit\test_active_cancellation.py:167:1: Expected `except` or `finally` after `try` block1 file left unchanged

invalid-syntax: Expected `except` or `finally` after `try` block
   --> tests\unit\test_active_cancellation.py:167:1
    |
167 | @pytest.mark.asyncio
    | ^
168 | async def test_provider_cancelled_before_first_instruction_releases_capacity():
169 |     coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
    |

invalid-syntax: Unexpected indentation
   --> tests\unit\test_active_cancellation.py:268:1
    |
266 |     assert maximum <= 2 and running == 0
267 |     assert calls == rounds * 3
268 |         assert stopped.is_set(), "repeat cancellation must not strand active upstream work"
    | ^^^^^^^^
269 |         assert coordinator.stats()["http"]["pending"] == 0
270 |     finally:
    |

invalid-syntax: Expected a statement
   --> tests\unit\test_active_cancellation.py:270:5
    |
268 |         assert stopped.is_set(), "repeat cancellation must not strand active upstream work"
269 |         assert coordinator.stats()["http"]["pending"] == 0
270 |     finally:
    |     ^^^^^^^
271 |         release.set()
272 |         request.cancel()
    |

invalid-syntax: Expected a statement
   --> tests\unit\test_active_cancellation.py:270:12
    |
268 |         assert stopped.is_set(), "repeat cancellation must not strand active upstream work"
269 |         assert coordinator.stats()["http"]["pending"] == 0
270 |     finally:
    |            ^
271 |         release.set()
272 |         request.cancel()
    |

invalid-syntax: Expected a statement
   --> tests\unit\test_active_cancellation.py:270:13
    |
268 |         assert stopped.is_set(), "repeat cancellation must not strand active upstream work"
269 |         assert coordinator.stats()["http"]["pending"] == 0
270 |     finally:
    |             ^
271 |         release.set()
272 |         request.cancel()
    |

invalid-syntax: Unexpected indentation
   --> tests\unit\test_active_cancellation.py:271:1
    |
269 |         assert coordinator.stats()["http"]["pending"] == 0
270 |     finally:
271 |         release.set()
    | ^^^^^^^^
272 |         request.cancel()
273 |         await asyncio.gather(request, return_exceptions=True)
    |

Found 6 errors.

=================================== ERRORS ====================================
___________ ERROR collecting tests/unit/test_active_cancellation.py ___________
.venv\Lib\site-packages\_pytest\python.py:508: in importtestmodule
    mod = import_path(
.venv\Lib\site-packages\_pytest\pathlib.py:596: in import_path
    importlib.import_module(module_name)
..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
.venv\Lib\site-packages\_pytest\assertion\rewrite.py:179: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.venv\Lib\site-packages\_pytest\assertion\rewrite.py:348: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\AppData\Local\Programs\Python\Python312\Lib\ast.py:52: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\unit\test_active_cancellation.py", line 167
E       @pytest.mark.asyncio
E   SyntaxError: expected 'except' or 'finally' block
=========================== short test summary info ===========================
ERROR tests/unit/test_active_cancellation.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.31s
```

