# Research-job control checkpoint — 2026-09-02

## Scope and result

Research-only job lifecycle repair, not a new automation capability. Baseline: `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit` passed `154 passed in 12.24s` at commit 6477bc7. Read before editing: jobs/manager.py, the service's create/control/worker/close paths, config job limits, existing state tests, and affected scope/manual/status/changelog/skill documents.

Eight assertion failures reproduced pause continuing work, failed envelopes being marked complete, missing shared admission, invalid numeric bounds, late failure overwriting pause, and shutdown leaving work falsely running. The implementation now serializes controls, cancels and joins paused/cancelled workers, checks positive integer inputs/admission, guards database state transitions, preserves failures/partial evidence, and leaves shutdown work recoverable.

No live jobs, DSH settings, models, presets, conversations, credentials or paid providers were changed for these tests. Tests use isolated temporary databases and deterministic providers. This is source/test evidence, not host/restart/DSH acceptance.

## TDD evidence

Command: `uv run --locked python -m pytest -q tests/unit/test_job_lifecycle.py`

```text
FFFFFFFF                                                                 [100%]
================================== FAILURES ===================================
______ test_pause_stops_worker_before_return_and_resume_starts_only_one _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1869/test_pause_stops_worker_before0')

    @pytest.mark.asyncio
    async def test_pause_stops_worker_before_return_and_resume_starts_only_one(tmp_path):
        service = service_at(tmp_path)
        entered, stopped, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        calls = 0

        async def research(*args, **kwargs):
            nonlocal calls
            calls += 1
            entered.set()
            try:
                await release.wait()
                return {"ok": True, "items": [{"url": "https://example.org/source"}]}
            finally:
                stopped.set()

        service.deep_research = research
        try:
            job = await service.research_job("create", "planner", question="find sources")
            await entered.wait()
            paused = await service.research_job("pause", "planner", job_id=job["job_id"])
            assert paused["state"] == "paused"
>           assert stopped.is_set(), "pause returned while the worker was still running"
E           AssertionError: pause returned while the worker was still running
E           assert False
E            +  where False = is_set()
E            +    where is_set = <asyncio.locks.Event object at 0x000001F79B43D220 [unset]>.is_set

tests\unit\test_job_lifecycle.py:41: AssertionError
_________ test_failed_research_envelope_marks_job_failed_not_complete _________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1869/test_failed_research_envelope_0')

    @pytest.mark.asyncio
    async def test_failed_research_envelope_marks_job_failed_not_complete(tmp_path):
        service = service_at(tmp_path)

        async def research(*args, **kwargs):
            return {"ok": False, "error": {"code": "UPSTREAM_UNAVAILABLE"}, "items": []}

        service.deep_research = research
        try:
            job = await service.research_job("create", "planner", question="find sources")
            await service._job_tasks[job["job_id"]]
            status = service.jobs.status(job["job_id"], "planner")
>           assert status["state"] == "failed"
E           AssertionError: assert 'complete' == 'failed'
E
E             - failed
E             + complete

tests\unit\test_job_lifecycle.py:70: AssertionError
________ test_job_active_limit_rejects_without_creating_another_record ________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1869/test_job_active_limit_rejects_0')

    @pytest.mark.asyncio
    async def test_job_active_limit_rejects_without_creating_another_record(tmp_path):
        service = service_at(tmp_path)
        service.config.jobs.max_active = 1
        entered, release = asyncio.Event(), asyncio.Event()

        async def research(*args, **kwargs):
            entered.set()
            await release.wait()
            return {"ok": True}

        service.deep_research = research
        try:
            await service.research_job("create", "planner", question="first")
            await entered.wait()
>           with pytest.raises(ValueError, match="JOB_CAPACITY_REACHED"):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           Failed: DID NOT RAISE ValueError

tests\unit\test_job_lifecycle.py:92: Failed
____ test_invalid_job_limits_are_rejected_before_record_creation[limits0] _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1869/test_invalid_job_limits_are_re0')
limits = {'max_sources': 0}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limits", [{"max_sources": 0}, {"max_pages": -1}, {"timeout_seconds": 0}])
    async def test_invalid_job_limits_are_rejected_before_record_creation(tmp_path, limits):
        service = service_at(tmp_path)
        try:
>           with pytest.raises(ValueError, match="INVALID_JOB_LIMITS"):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           Failed: DID NOT RAISE ValueError

tests\unit\test_job_lifecycle.py:105: Failed
____ test_invalid_job_limits_are_rejected_before_record_creation[limits1] _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1869/test_invalid_job_limits_are_re1')
limits = {'max_pages': -1}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limits", [{"max_sources": 0}, {"max_pages": -1}, {"timeout_seconds": 0}])
    async def test_invalid_job_limits_are_rejected_before_record_creation(tmp_path, limits):
        service = service_at(tmp_path)
        try:
>           with pytest.raises(ValueError, match="INVALID_JOB_LIMITS"):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           Failed: DID NOT RAISE ValueError

tests\unit\test_job_lifecycle.py:105: Failed
____ test_invalid_job_limits_are_rejected_before_record_creation[limits2] _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1869/test_invalid_job_limits_are_re2')
limits = {'timeout_seconds': 0}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("limits", [{"max_sources": 0}, {"max_pages": -1}, {"timeout_seconds": 0}])
    async def test_invalid_job_limits_are_rejected_before_record_creation(tmp_path, limits):
        service = service_at(tmp_path)
        try:
>           with pytest.raises(ValueError, match="INVALID_JOB_LIMITS"):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           Failed: DID NOT RAISE ValueError

tests\unit\test_job_lifecycle.py:105: Failed
___ test_terminal_job_cannot_resume_and_late_finish_cannot_overwrite_pause ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1869/test_terminal_job_cannot_resum0')

    @pytest.mark.asyncio
    async def test_terminal_job_cannot_resume_and_late_finish_cannot_overwrite_pause(tmp_path):
        service = service_at(tmp_path)
        try:
            job = service.jobs.create("planner", "sources", {})
            service.jobs.start(job["job_id"], "planner", 30)
            service.jobs.transition(job["job_id"], "planner", "pause")
            late = service.jobs.finish(job["job_id"], "planner", {}, "JOB_TIMEOUT")
>           assert late["state"] == "paused"
E           AssertionError: assert 'failed' == 'paused'
E
E             - paused
E             + failed

tests\unit\test_job_lifecycle.py:120: AssertionError
________ test_shutdown_leaves_interrupted_job_recoverable_immediately _________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1869/test_shutdown_leaves_interrupt0')

    @pytest.mark.asyncio
    async def test_shutdown_leaves_interrupted_job_recoverable_immediately(tmp_path):
        service = service_at(tmp_path)
        entered = asyncio.Event()

        async def research(*args, **kwargs):
            entered.set()
            await asyncio.Event().wait()

        service.deep_research = research
        job = await service.research_job("create", "planner", question="find sources")
        await entered.wait()
        await service.close()
        status = service.jobs.status(job["job_id"], "planner")
>       assert status["state"] == "paused_recoverable"
E       AssertionError: assert 'running' == 'paused_recoverable'
E
E         - paused_recoverable
E         + running

tests\unit\test_job_lifecycle.py:142: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_lifecycle.py::test_pause_stops_worker_before_return_and_resume_starts_only_one
FAILED tests/unit/test_job_lifecycle.py::test_failed_research_envelope_marks_job_failed_not_complete
FAILED tests/unit/test_job_lifecycle.py::test_job_active_limit_rejects_without_creating_another_record
FAILED tests/unit/test_job_lifecycle.py::test_invalid_job_limits_are_rejected_before_record_creation[limits0]
FAILED tests/unit/test_job_lifecycle.py::test_invalid_job_limits_are_rejected_before_record_creation[limits1]
FAILED tests/unit/test_job_lifecycle.py::test_invalid_job_limits_are_rejected_before_record_creation[limits2]
FAILED tests/unit/test_job_lifecycle.py::test_terminal_job_cannot_resume_and_late_finish_cannot_overwrite_pause
FAILED tests/unit/test_job_lifecycle.py::test_shutdown_leaves_interrupted_job_recoverable_immediately
8 failed in 1.32s
```

Command: `uv run --locked ruff format src/halo_research_gateway/service.py src/halo_research_gateway/jobs/manager.py tests/unit/test_job_lifecycle.py`
then `uv run --locked python -m pytest -q tests/unit/test_job_lifecycle.py tests/unit/test_active_cancellation.py tests/unit/test_v15_state.py`

```text
1 file reformatted, 2 files left unchanged
......................                                                   [100%]
22 passed in 1.59s
```

Widened commands: `uv run --locked python -m pytest -q tests/unit`, then `uv run --locked ruff check src tests`.

```text
162 passed in 12.76s
All checks passed!
```

## Falsification and honest empty/partial results

Additional cases exercised actual deep-research/coordinator/HTTP cancellation, simultaneous create calls under a one-job ceiling, pause before worker start, and terminal resume rejection. These passed. Empty-success evidence exposed another assertion failure:

Command: `uv run --locked python -m pytest -q tests/unit/test_job_lifecycle.py`

```text
...........F                                                             [100%]
================================== FAILURES ===================================
______ test_empty_research_is_failed_and_partial_evidence_remains_marked ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1872/test_empty_research_is_failed_0')

    @pytest.mark.asyncio
    async def test_empty_research_is_failed_and_partial_evidence_remains_marked(tmp_path):
        service = service_at(tmp_path)
        outcome = {"ok": True, "items": [], "warnings": ["SEARCH_UNAVAILABLE"]}

        async def research(*args, **kwargs):
            return outcome

        service.deep_research = research
        try:
            empty = await service.research_job("create", "planner", question="no sources")
            await service._job_tasks[empty["job_id"]]
            status = service.jobs.status(empty["job_id"], "planner")
>           assert status["state"] == "failed"
E           AssertionError: assert 'complete' == 'failed'
E
E             - failed
E             + complete

tests\unit\test_job_lifecycle.py:227: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_lifecycle.py::test_empty_research_is_failed_and_partial_evidence_remains_marked
1 failed, 11 passed in 1.58s
```

Empty results now fail with NO_RESEARCH_EVIDENCE. A completed worker with warnings or remaining cursor pages records progress.partial=true and preserves its result/warnings.

Commands: `uv run --locked ruff format src tests`, then `uv run --locked python -m pytest -q tests/unit/test_job_lifecycle.py`

```text
1 file reformatted, 75 files left unchanged
............                                                             [100%]
12 passed in 1.48s
```

## Security and limits

- Positive integer bounds validated before record creation; shared configured capacity checked before create/resume.
- Existing owner checks and localhost architecture retained; no endpoint or auth mechanism added. Client ownership labels are scheduling metadata, not authentication.
- No secrets, private content or connection values in evidence. Fixture URLs are public placeholders; fixtures never make upstream requests.
- No eval, unsafe rendering or deserialization introduced. JSON state stays local.
- No new dependencies; dependency vulnerability review is not expanded by this checkpoint.
- Database lifecycle updates are conditional; paused/cancelled state cannot be overwritten by a late finish.
- One-process admission is protected by a shared async lock. This does not claim multi-process execution support.

## Still incomplete

Exact source-frontier checkpoints, cumulative time/page budgets across resume, lease renewal, crash/restart continuation, and complete long-running-job host acceptance remain open. Resume currently restarts the run and may reuse cached pages. It is not exact-source continuation. General retrieval cancellation still needs wider stress/race testing. See RESEARCH-ONLY-SCOPE.md; the overall goal is not complete.

## Full checkpoint gate

Commands: `pwsh -NoProfile -File scripts/Update-BuildManifest.ps1`, then `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`.

```text
Wrote BUILD-MANIFEST.json with 202 files.
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
76 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
166 passed in 13.27s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

A limited credential-pattern scan covered 203 text files including local AGENTS.md and found zero matching files. This is not an exhaustive secrets/security audit. LICENSE and CONTRIBUTING.md remain absent; no public-package release or licensing choice is implied by a private source checkpoint push. Documentation was then updated with this gate evidence; the commit hook rechecks the resulting tree.
