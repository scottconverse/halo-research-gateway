# Durable research-job evidence — 2026-09-02

## Outcome and boundary

Continues the research-only goal from clean checkpoint 2aa748e. No DSH settings/packages, credentials, paid calls or live jobs were changed during implementation. The service now checkpoints completed evidence, discovery frontier, position and cumulative attempts; retries consume attempts. Active time persists across resume, leases renew and crash recovery conservatively charges the unobserved lease remainder. Queued-before-start records are recoverable on startup. Status summarizes progress and exposes bounded citable evidence with cache-backed cursors instead of dumping the entire durable packet.

Known-sensitive source/link query URLs are excluded from durable jobs. Checkpoint size is capped by storage.entry_max_bytes; overflow retains the previous checkpoint and fails explicitly. This is not a guarantee that arbitrary public page prose contains no sensitive information.

Read before editing: service deep research/job control/snapshot code, job manager, models, config limits, cache and URL helpers, existing deep/job/state tests, and affected manual/scope/status/changelog/skill documents. No dependency or database schema change. Existing fourteen-tool MCP surface and DSH native capabilities remain unchanged.

## Test evidence

### Baseline

Exact command(s):

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_lifecycle.py tests/unit/test_deep_research.py tests/unit/test_v15_state.py
```

```text
...........................                                              [100%]
27 passed in 1.99s
```

### Missing frontier RED

Exact command(s):

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py
```

```text
FF                                                                       [100%]
================================== FAILURES ===================================
___ test_restart_keeps_completed_sources_frontier_and_total_page_budget[2] ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1877/test_restart_keeps_completed_s0')
page_budget = 2

    @pytest.mark.asyncio
    @pytest.mark.parametrize("page_budget", [2, 3])
    async def test_restart_keeps_completed_sources_frontier_and_total_page_budget(tmp_path, page_budget):
        first = service_at(tmp_path)
        entered = asyncio.Event()
        first_url, second_url = "https://example.org/first", "https://example.org/second"
        searches = 0

        async def search(*args, **kwargs):
            nonlocal searches
            searches += 1
            return ProviderResult("fixture", [evidence(first_url, ""), evidence(second_url, "")])

        async def initial_fetch(url):
            if url == first_url:
                return ProviderResult("fixture", [evidence(url, "First source says cancelled tasks must clean up.")])
            entered.set()
            await asyncio.Event().wait()

        first.ddgs.search, first.http.fetch = search, initial_fetch
        resumed = None
        try:
            job = await first.research_job("create", "planner", question="task cancellation", limits={"max_sources": 2, "max_pages": page_budget})
            await asyncio.wait_for(entered.wait(), 3)
            await first.research_job("pause", "planner", job_id=job["job_id"])
            paused = first.jobs.status(job["job_id"], "planner")
            saved = paused["progress"].get("checkpoint", {})
>           assert [item["url"] for item in saved.get("items", [])] == [first_url]
E           AssertionError: assert [] == ['https://example.org/first']
E
E             Right contains one more item: 'https://example.org/first'
E             Use -v to get more diff

tests\unit\test_job_continuation.py:43: AssertionError
___ test_restart_keeps_completed_sources_frontier_and_total_page_budget[3] ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1877/test_restart_keeps_completed_s1')
page_budget = 3

    @pytest.mark.asyncio
    @pytest.mark.parametrize("page_budget", [2, 3])
    async def test_restart_keeps_completed_sources_frontier_and_total_page_budget(tmp_path, page_budget):
        first = service_at(tmp_path)
        entered = asyncio.Event()
        first_url, second_url = "https://example.org/first", "https://example.org/second"
        searches = 0

        async def search(*args, **kwargs):
            nonlocal searches
            searches += 1
            return ProviderResult("fixture", [evidence(first_url, ""), evidence(second_url, "")])

        async def initial_fetch(url):
            if url == first_url:
                return ProviderResult("fixture", [evidence(url, "First source says cancelled tasks must clean up.")])
            entered.set()
            await asyncio.Event().wait()

        first.ddgs.search, first.http.fetch = search, initial_fetch
        resumed = None
        try:
            job = await first.research_job("create", "planner", question="task cancellation", limits={"max_sources": 2, "max_pages": page_budget})
            await asyncio.wait_for(entered.wait(), 3)
            await first.research_job("pause", "planner", job_id=job["job_id"])
            paused = first.jobs.status(job["job_id"], "planner")
            saved = paused["progress"].get("checkpoint", {})
>           assert [item["url"] for item in saved.get("items", [])] == [first_url]
E           AssertionError: assert [] == ['https://example.org/first']
E
E             Right contains one more item: 'https://example.org/first'
E             Use -v to get more diff

tests\unit\test_job_continuation.py:43: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_continuation.py::test_restart_keeps_completed_sources_frontier_and_total_page_budget[2]
FAILED tests/unit/test_job_continuation.py::test_restart_keeps_completed_sources_frontier_and_total_page_budget[3]
2 failed in 1.04s
```

### Frontier GREEN

Exact command(s):

```powershell
uv run --locked ruff format src/halo_research_gateway/service.py src/halo_research_gateway/jobs/manager.py tests/unit/test_job_continuation.py
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py tests/unit/test_job_lifecycle.py tests/unit/test_deep_research.py tests/unit/test_v15_state.py
```

```text
2 files reformatted, 1 file left unchanged
.............................                                            [100%]
29 passed in 2.58s
```

### Time, lease and shared-limit RED

Exact command(s):

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py
```

```text
..FFF                                                                    [100%]
================================== FAILURES ===================================
___________ test_resume_cannot_reset_an_exhausted_total_time_budget ___________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1880/test_resume_cannot_reset_an_ex0')

    @pytest.mark.asyncio
    async def test_resume_cannot_reset_an_exhausted_total_time_budget(tmp_path):
        service = service_at(tmp_path)
        calls = []

        async def research(*args, **kwargs):
            calls.append("started")
            return {"ok": True, "items": [{"url": "https://example.org/source"}]}

        service.deep_research = research
        try:
            job = service.jobs.create("planner", "sources", {"max_sources": 2, "max_pages": 3, "timeout_seconds": 1})
            service.jobs.transition(job["job_id"], "planner", "pause")
            with sqlite3.connect(service.config.storage.database) as db:
                db.execute("UPDATE jobs SET progress_json=? WHERE job_id=?", (json.dumps({"checkpoint": {"elapsed_seconds": 1.0}}), job["job_id"]))
            await service.research_job("resume", "planner", job_id=job["job_id"])
            await service._job_tasks[job["job_id"]]
            status = service.jobs.status(job["job_id"], "planner")
>           assert calls == [], "resuming reset the consumed time budget"
E           AssertionError: resuming reset the consumed time budget
E           assert ['started'] == []
E
E             Left contains one more item: 'started'
E             Use -v to get more diff

tests\unit\test_job_continuation.py:100: AssertionError
____________ test_live_worker_renews_lease_and_pause_stops_renewal ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1880/test_live_worker_renews_lease_0')

    @pytest.mark.asyncio
    async def test_live_worker_renews_lease_and_pause_stops_renewal(tmp_path):
        service = service_at(tmp_path)
        service.config.jobs.lease_seconds = 1
        entered = asyncio.Event()

        async def research(*args, **kwargs):
            entered.set()
            await asyncio.Event().wait()

        service.deep_research = research
        try:
            job = await service.research_job("create", "planner", question="sources")
            await entered.wait()
            original_lease = service.jobs.status(job["job_id"], "planner")["lease_until"]
            for _ in range(20):
                await asyncio.sleep(0.1)
                current = service.jobs.status(job["job_id"], "planner")
                if current["lease_until"] != original_lease:
                    break
>           assert current["lease_until"] > original_lease
E           AssertionError: assert '2026-09-02T23:24:18.395641Z' > '2026-09-02T23:24:18.395641Z'

tests\unit\test_job_continuation.py:127: AssertionError
___________ test_distinct_jobs_still_share_the_deep_provider_limit ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1880/test_distinct_jobs_still_share0')

    @pytest.mark.asyncio
    async def test_distinct_jobs_still_share_the_deep_provider_limit(tmp_path):
        service = service_at(tmp_path)
        entered = asyncio.Event()
        calls = 0

        async def search(*args, **kwargs):
            nonlocal calls
            calls += 1
            entered.set()
            await asyncio.Event().wait()

        service.ddgs.search = search
        try:
            await service.research_job("create", "planner", question="first")
            await service.research_job("create", "worker", question="second")
            await entered.wait()
            for _ in range(10):
                await asyncio.sleep(0)
>           assert calls == 1, "durable jobs bypassed the existing shared deep-research limit"
E           AssertionError: durable jobs bypassed the existing shared deep-research limit
E           assert 2 == 1

tests\unit\test_job_continuation.py:157: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_continuation.py::test_resume_cannot_reset_an_exhausted_total_time_budget
FAILED tests/unit/test_job_continuation.py::test_live_worker_renews_lease_and_pause_stops_renewal
FAILED tests/unit/test_job_continuation.py::test_distinct_jobs_still_share_the_deep_provider_limit
3 failed, 2 passed in 3.58s
```

### Time, lease and shared-limit GREEN

Exact command(s):

```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py tests/unit/test_job_lifecycle.py tests/unit/test_deep_research.py tests/unit/test_v15_state.py
```

```text
2 files reformatted, 75 files left unchanged
................................                                         [100%]
32 passed in 3.68s
```

### Crash recovery RED

Exact command(s):

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py
```

```text
.....F.                                                                  [100%]
================================== FAILURES ===================================
_ test_expired_crash_lease_is_recoverable_on_status_and_charges_uncertain_time _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1882/test_expired_crash_lease_is_re0')

    @pytest.mark.asyncio
    async def test_expired_crash_lease_is_recoverable_on_status_and_charges_uncertain_time(tmp_path):
        service = service_at(tmp_path)
        clock = FakeClock()
        service.jobs.clock = clock
        try:
            job = service.jobs.create("planner", "sources", {"timeout_seconds": 10})
            service.jobs.start(job["job_id"], "planner", 3)
            service.jobs.heartbeat(job["job_id"], "planner", 2, 3)
            clock.now += timedelta(seconds=4)
            status = await service.research_job("status", "planner", job_id=job["job_id"])
>           assert status["state"] == "paused_recoverable"
E           AssertionError: assert 'running' == 'paused_recoverable'
E
E             - paused_recoverable
E             + running

tests\unit\test_job_continuation.py:178: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_continuation.py::test_expired_crash_lease_is_recoverable_on_status_and_charges_uncertain_time
1 failed, 6 passed in 2.42s
```

### Recovery GREEN and lint failure

Exact command(s):

```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py tests/unit/test_job_lifecycle.py tests/unit/test_deep_research.py tests/unit/test_v15_state.py
uv run --locked ruff check src tests
```

```text
1 file reformatted, 76 files left unchanged
..................................                                       [100%]
34 passed in 4.43s
I001 [*] Import block is un-sorted or un-formatted
  --> tests\unit\test_job_continuation.py:3:1
   |
 1 |   """Paused jobs must resume persisted evidence, not repeat a fresh research run."""
 2 |
 3 | / import asyncio
 4 | | import json
 5 | | import sqlite3
 6 | | from datetime import timedelta
 7 | |
 8 | | import pytest
 9 | |
10 | | from halo_research_gateway.models import EvidenceItem, ProviderResult
11 | | from test_job_lifecycle import service_at
12 | | from test_v15_state import FakeClock
   | |____________________________________^
help: Organize imports
   |
8  | import pytest
9  + from test_job_lifecycle import service_at
10 + from test_v15_state import FakeClock
11 |
12 | from halo_research_gateway.models import EvidenceItem, ProviderResult
   - from test_job_lifecycle import service_at
   - from test_v15_state import FakeClock
13 |
   |

Found 1 error.
[*] 1 fixable with the `--fix` option.
```

### Native process canary first attempt: cleanup FAILED

Exact command(s):

```powershell
uv run --locked ruff format tests/acceptance/job_process_recovery.py tests/unit/test_job_continuation.py
uv run --locked python tests/acceptance/job_process_recovery.py
uv run --locked ruff check src tests
```

```text
1 file reformatted, 1 file left unchanged
{"passed": true, "native_process_crash_recovered": true, "search_repeated": false, "completed_source_refetched": false, "attempts": 3, "sources": ["https://example.org/task-groups", "https://example.org/cancellation"], "fixture_only": true}
Traceback (most recent call last):
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\shutil.py", line 633, in _rmtree_unsafe
    os.unlink(fullname)
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\\Users\\scott\\AppData\\Local\\Temp\\halo-job-recovery-ryk3msmy\\state\\gateway.db'

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\job_process_recovery.py", line 149, in <module>
    main()
  File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\job_process_recovery.py", line 90, in main
    with tempfile.TemporaryDirectory(prefix="halo-job-recovery-") as directory:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\tempfile.py", line 950, in __exit__
    self.cleanup()
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\tempfile.py", line 954, in cleanup
    self._rmtree(self.name, ignore_errors=self._ignore_cleanup_errors)
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\tempfile.py", line 934, in _rmtree
    _shutil.rmtree(name, onexc=onexc)
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\shutil.py", line 781, in rmtree
    return _rmtree_unsafe(path, onexc)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\shutil.py", line 635, in _rmtree_unsafe
    onexc(os.unlink, fullname, err)
  File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\tempfile.py", line 909, in onexc
    _os.unlink(path)
PermissionError: [WinError 32] The process cannot access the file because it is being used by another process: 'C:\\Users\\scott\\AppData\\Local\\Temp\\halo-job-recovery-ryk3msmy\\state\\gateway.db'
All checks passed!
```

### Sensitive URL RED

Exact command(s):

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py -k sensitive
```

```text
F                                                                        [100%]
================================== FAILURES ===================================
_____ test_known_sensitive_source_and_link_urls_are_not_persisted_in_jobs _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1887/test_known_sensitive_source_an0')

    @pytest.mark.asyncio
    async def test_known_sensitive_source_and_link_urls_are_not_persisted_in_jobs(tmp_path):
        service = service_at(tmp_path)
        safe = "https://example.org/source"
        sensitive = "https://example.org/export?token=fixture-secret-value"
        fetched = []

        async def search(*args, **kwargs):
            return ProviderResult("fixture", [evidence(sensitive, ""), evidence(safe, "")])

        async def fetch(url):
            fetched.append(url)
            page = evidence(url, "Public source evidence")
            page.metadata = {"links": [("private export", sensitive)]}
            return ProviderResult("fixture", [page])

        service.ddgs.search, service.http.fetch = search, fetch
        try:
            job = await service.research_job("create", "planner", question="public evidence")
            await service._job_tasks[job["job_id"]]
            status = service.jobs.status(job["job_id"], "planner")
>           assert sensitive not in fetched
E           AssertionError: assert 'https://example.org/export?token=fixture-secret-value' not in ['https://example.org/export?token=fixture-secret-value', 'https://example.org/source']

tests\unit\test_job_continuation.py:229: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_continuation.py::test_known_sensitive_source_and_link_urls_are_not_persisted_in_jobs
1 failed, 7 deselected in 1.34s
```

### Sensitive URL GREEN

Exact command(s):

```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py tests/unit/test_job_lifecycle.py tests/unit/test_deep_research.py tests/unit/test_v15_state.py
```

```text
78 files left unchanged
...................................                                      [100%]
35 passed in 4.38s
```

### Native process canary: PASS after cleanup

Exact command(s):

```powershell
uv run --locked python tests/acceptance/job_process_recovery.py
```

```text
{"passed": true, "native_process_crash_recovered": true, "search_repeated": false, "completed_source_refetched": false, "attempts": 3, "sources": ["https://example.org/task-groups", "https://example.org/cancellation"], "fixture_only": true}
```

### Queued startup RED

Exact command(s):

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py -k startup_recovers
```

```text
F                                                                        [100%]
================================== FAILURES ===================================
__________ test_startup_recovers_a_job_persisted_before_worker_start __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1890/test_startup_recovers_a_job_pe0')

    @pytest.mark.asyncio
    async def test_startup_recovers_a_job_persisted_before_worker_start(tmp_path):
        first = service_at(tmp_path)
        job = first.jobs.create("planner", "queued before interruption", {"timeout_seconds": 10})
        await first.close()
        restarted = service_at(tmp_path)
        try:
            status = restarted.jobs.status(job["job_id"], "planner")
>           assert status["state"] == "paused_recoverable"
E           AssertionError: assert 'queued' == 'paused_recoverable'
E
E             - paused_recoverable
E             + queued

tests\unit\test_job_continuation.py:244: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_continuation.py::test_startup_recovers_a_job_persisted_before_worker_start
1 failed, 8 deselected in 0.91s
```

### Bounded status RED

Exact command(s):

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py -k public_job_status
```

```text
F                                                                        [100%]
================================== FAILURES ===================================
_____ test_public_job_status_is_bounded_and_retained_evidence_is_pageable _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1894/test_public_job_status_is_boun0')

    @pytest.mark.asyncio
    async def test_public_job_status_is_bounded_and_retained_evidence_is_pageable(tmp_path):
        service = service_at(tmp_path)
        source = "https://example.org/retained"
        try:
            job = service.jobs.create("planner", "bounded status", {"timeout_seconds": 30})
            service.jobs.start(job["job_id"], "planner", 30)
            service.jobs.checkpoint(job["job_id"], "planner", {
                "items": [evidence(source, "Evidence with citation. " * 4000).as_dict()],
                "frontier": [[source, 0, "example.org"]], "position": 1, "attempted": 1,
                "elapsed_seconds": 0.5, "search_complete": True, "warnings": [],
            }, service.config.storage.entry_max_bytes)
            status = await service.research_job("status", "planner", job_id=job["job_id"])
>           assert len(json.dumps(status, indent=2)) <= 6000
E           assert 96939 <= 6000
E            +  where 96939 = len('{\n  "job_id": "7df1d523-a6a8-4d58-9bb5-2143ab726f75",\n  "owner": "planner",\n  "request": {\n    "question": "bound..."updated_at": "2026-09-02T23:34:05.997363Z",\n  "lease_until": "2026-09-02T23:34:35.992699Z",\n  "error_code": null\n}')
E            +    where '{\n  "job_id": "7df1d523-a6a8-4d58-9bb5-2143ab726f75",\n  "owner": "planner",\n  "request": {\n    "question": "bound..."updated_at": "2026-09-02T23:34:05.997363Z",\n  "lease_until": "2026-09-02T23:34:35.992699Z",\n  "error_code": null\n}' = <function dumps at 0x00000227FDD99A80>({'job_id': '7df1d523-a6a8-4d58-9bb5-2143ab726f75', 'owner': 'planner', 'request': {'question': 'bounded status'}, 'limits': {'timeout_seconds': 30}, ...}, indent=2)
E            +      where <function dumps at 0x00000227FDD99A80> = json.dumps

tests\unit\test_job_continuation.py:264: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_continuation.py::test_public_job_status_is_bounded_and_retained_evidence_is_pageable
1 failed, 9 deselected in 1.03s
```

### Bounded status GREEN

Exact command(s):

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_continuation.py tests/unit/test_job_lifecycle.py
```

```text
......................                                                   [100%]
22 passed in 3.34s
```

## Interpretation of failures

The first frontier implementation accidentally bypassed the shared deep queue. Its new regression failed (2 concurrent calls instead of 1), and the queue was restored with job-specific operation identities before commit. The import-order lint error was fixed without changing production behavior.

The first native canary recovered evidence but failed temporary-directory cleanup: the parent harness kept a SQLite connection alive. Its early passed field was not an acceptance pass; the shell's later lint command also obscured the Python exit code. The harness now explicitly closes that connection and prints success only after cleanup. The corrected canary ran by itself with exit code 0. Only the disposable failed-test directory halo-job-recovery-ryk3msmy was removed afterward; no runtime/user data was removed.

The native canary starts two owned Windows Python processes against a temporary database. It terminates only the first owned Process object while its second source is in flight, verifies the persisted first source and attempt count, clears only fixture cache, waits for that recorded lease to expire, and starts the second worker. Recovery retained both citable fixture sources, repeated neither discovery nor the completed source, and charged three total attempts. Both processes and temporary storage were cleaned up. Sources are deterministic example.org fixtures, not claims about real upstream content.

## Falsification and wider verification

Additional checks covered exhausted page/time budgets, checkpoint overflow, live lease renewal stopping after pause, queued-before-start recovery, shared deep admission, token-bearing URLs, and 96,939-character raw status becoming a bounded evidence page. Cursor continuation after service restart is covered as an additional falsification test.

Exact widened commands:

```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/unit
uv run --locked ruff check src tests
```

```text
1 file reformatted, 77 files left unchanged
........................................................................ [ 40%]
........................................................................ [ 81%]
................................                                         [100%]
176 passed in 15.17s
All checks passed!
```

## Security, performance and remaining acceptance

- Inputs: previously validated positive limits retained; cumulative budget enforcement and recognized sensitive-URL checks added. Large questions/custom metadata still require wider response-size testing; the checkpoint/evidence payload, not every arbitrary caller field, is what this checkpoint bounds.
- Auth: existing ownership checks and localhost architecture unchanged; no new route. Client labels remain scheduling metadata, not authentication. Jobs here are for public research.
- Secrets: only synthetic tokens/URLs in tests; no personal or connected-account data used. Pattern checks are not a comprehensive data-loss-prevention system.
- Rendering/evaluation: none introduced. Checkpoints are local JSON; no executable deserialization.
- Dependencies: none added. No new dependency audit required by this diff.
- Performance: checkpoints serialize bounded evidence; heartbeat interval is one-third of the configured lease. Page snapshots use content hashes and existing bounded disk cache. General in-memory snapshot retention and provider stress remain broader reliability work.
- Ownership: recovery assumes one Gateway process owns its database. Duplicate-service startup fencing and larger host installation/recovery acceptance remain separate work.
- Cancellation: DDGS uses synchronous work in a thread. Cancelling the async worker does not forcibly terminate that in-flight synchronous request. Long-running provider stress remains unproved.
- Scope: complete DSH workflow, real login/app-bound cookies, human challenge/provider routing, source coverage, website publication and full host/release acceptance remain open. This checkpoint does not complete the overall goal.

## Commit gate and final native canary

Commands: `pwsh -NoProfile -File scripts/Update-BuildManifest.ps1`, then `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`.

```text
Wrote BUILD-MANIFEST.json with 205 files.
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
78 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 40%]
........................................................................ [ 81%]
................................                                         [100%]
176 passed in 15.26s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

The final `uv run --locked python tests/acceptance/job_process_recovery.py` was also repeated after bounded-status and queued-startup changes. Exit code 0:

```json
{"passed": true, "native_process_crash_recovered": true, "search_repeated": false, "completed_source_refetched": false, "attempts": 3, "sources": ["https://example.org/task-groups", "https://example.org/cancellation"], "fixture_only": true}
```
