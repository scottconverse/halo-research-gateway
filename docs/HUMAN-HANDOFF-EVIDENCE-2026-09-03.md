# Human research handoff evidence — 2026-09-03

## Followup before push: session identity and driver-start cancellation

The first local commit `23527af6301d92a6e7f6d29060a69993e57f4340` passed
`466 passed in 77.35s (0:01:17)` in its commit gate and was not pushed yet.
Review found a race where finishing an old session could return the new session's
state, and a displayed 120-second deadline ignored a lower configured limit.
Both were corrected with deterministic interleaving/lower-limit assertions.

The first race-test attempt accidentally invoked real Playwright startup because
the new deadline test lacked its browser stub. Cancelling during driver startup
left the isolated test hung. It printed assertion-failure markers but never a
complete pytest summary; that run is **not** a pass or a complete RED receipt.
The known test-only node driver (40780, parent 53696) and then the isolated pytest
process (53696, parent 56084) were stopped after PID, command, path, creation-time
and parent checks. Installed Gateway PIDs 47164/36236 and DSH were untouched.
The initial cleanup command refused an exact timestamp comparison; the retry
retained a process handle and allowed only 1 ms of CIM/.NET timestamp precision.

The tests were fixed to stay isolated. The two manager behaviors were replayed
against their 23527af implementation (only those methods temporarily restored),
producing complete assertion RED output, then the corrections were restored and
passed. This replay is reported as a later reproduction, not fabricated original
output from the interrupted run.

The native incident exposed a shared profile-reader/visible-handoff startup
cancellation hole. Driver entry now settles before a cancelled operation shuts
that same driver down; exit is also protected against repeated cancellation.
A genuinely hung initialization/shutdown still has no hard overall cleanup
deadline. Two deterministic cases first failed on the missing shutdown.
Two actual native driver-start cancellation cases now return and reap their
children, alongside the visible-cookie-transfer and UI tests:
`19 passed in 1.90s`, `4 passed in 6.82s`.
These are disposable fixtures, not installed or DSH acceptance.


### Interrupted race-test attempt (no complete pytest summary)

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
```

```text
...............FF

```

### Driver cleanup identity precision check refused before stopping anything

```powershell
$ErrorActionPreference='Stop'
$taskDriver=Get-CimInstance Win32_Process -Filter 'ProcessId=40780'
$taskOwner=Get-CimInstance Win32_Process -Filter 'ProcessId=53696'
if($taskDriver.ParentProcessId -ne 53696 -or $taskOwner.Name -ne 'python.exe' -or $taskOwner.CommandLine -notmatch 'pytest.*tests/unit/test_human_handoff.py' -or $taskDriver.ExecutablePath -notlike '*\.venv\Lib\site-packages\playwright\driver\node.exe'){throw 'Test-driver ownership did not match'}
$taskHandle=Get-Process -Id 40780
if($taskHandle.StartTime.ToUniversalTime().ToString('o') -ne $taskDriver.CreationDate.ToUniversalTime().ToString('o')){throw 'Process identity changed'}
$taskDriver | Select-Object ProcessId,ParentProcessId,CreationDate,ExecutablePath | ConvertTo-Json
$taskHandle.Kill()
$taskHandle.WaitForExit(10000)
'Stopped only the verified stuck test Playwright driver; no browser or installed process targeted.'
```

```text
Exception: 
Line |
   7 |  … te.ToUniversalTime().ToString('o')){throw 'Process identity changed'}
     |                                        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | Process identity changed

```

### Verified disposable driver cleanup

```powershell
$ErrorActionPreference='Stop'
$taskDriver=Get-CimInstance Win32_Process -Filter 'ProcessId=40780'
$taskOwner=Get-CimInstance Win32_Process -Filter 'ProcessId=53696'
if($taskDriver.ParentProcessId -ne 53696 -or $taskOwner.Name -ne 'python.exe' -or $taskOwner.CommandLine -notmatch 'pytest.*tests/unit/test_human_handoff.py' -or $taskDriver.ExecutablePath -notlike '*\.venv\Lib\site-packages\playwright\driver\node.exe'){throw 'Test-driver ownership did not match'}
$taskHandle=Get-Process -Id 40780
$taskProcessHandle=$taskHandle.Handle
if([Math]::Abs(($taskHandle.StartTime.ToUniversalTime()-$taskDriver.CreationDate.ToUniversalTime()).TotalMilliseconds) -gt 1){throw 'Process identity changed'}
$taskDriver | Select-Object ProcessId,ParentProcessId,CreationDate,ExecutablePath | ConvertTo-Json
$taskHandle.Kill()
$taskHandle.WaitForExit(10000)
'Stopped only the verified stuck test Playwright driver; no browser or installed process targeted.'
```

```text
{
  "ProcessId": 40780,
  "ParentProcessId": 53696,
  "CreationDate": "2026-09-03T01:51:18.750946-06:00",
  "ExecutablePath": "C:\\Users\\scott\\Desktop\\Code\\halo-research-gateway\\.venv\\Lib\\site-packages\\playwright\\driver\\node.exe"
}
True
Stopped only the verified stuck test Playwright driver; no browser or installed process targeted.

```

### Verified isolated pytest cleanup after its driver exited

```powershell
$ErrorActionPreference='Stop'
$taskRunner=Get-CimInstance Win32_Process -Filter 'ProcessId=53696'
if($taskRunner.ParentProcessId -ne 56084 -or $taskRunner.CommandLine -notmatch 'pytest.*tests/unit/test_human_handoff.py' -or $taskRunner.Name -ne 'python.exe'){throw 'Test runner identity mismatch'}
if(Get-CimInstance Win32_Process -Filter 'ParentProcessId=53696'){throw 'Unexpected surviving child; inspect first'}
$taskHandle=Get-Process -Id 53696
$taskProcessHandle=$taskHandle.Handle
if([Math]::Abs(($taskHandle.StartTime.ToUniversalTime()-$taskRunner.CreationDate.ToUniversalTime()).TotalMilliseconds) -gt 1){throw 'Process identity changed'}
$taskHandle.Kill()
$taskHandle.WaitForExit(10000)
'Stopped the isolated hung pytest runner after its driver was removed. No installed process targeted.'
```

```text
True
Stopped the isolated hung pytest runner after its driver was removed. No installed process targeted.

```

### Completed race/deadline RED replay against 23527af method behavior

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py -k 'finished_response_cannot or lower_configured_deadline'
```

```text
FF                                                                       [100%]
================================== FAILURES ===================================
_______ test_finished_response_cannot_describe_a_newly_started_session ________

handoff_app = (<starlette.applications.Starlette object at 0x00000237FE486F60>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000237FE4B17F0>

    async def test_finished_response_cannot_describe_a_newly_started_session(handoff_app, monkeypatch):
        app, _ = handoff_app
        manager = app.state.halo_service.research_session
    
        async def browser(url, profile, done, ready):
            ready()
            await done.wait()
    
        monkeypatch.setattr(manager.crawler, "human_handoff", browser)
        first = await manager.begin("https://example.org/first", "research")
        original_gather = asyncio.gather
    
        async def interleave(*tasks, **kwargs):
            result = await original_gather(*tasks, **kwargs)
            await manager.begin("https://example.org/second", "research")
            return result
    
        with monkeypatch.context() as race:
            race.setattr(asyncio, "gather", interleave)
            finished = await manager.finish(first["session_id"], cancel=True)
>       assert finished["session_id"] == first["session_id"], "completion returned another request's session"
E       AssertionError: completion returned another request's session
E       assert '8ef3694f-324...-cd6d34b2b27b' == '73b6e830-7ac...-3a027550de7e'
E         
E         - 73b6e830-7ace-4288-998b-3a027550de7e
E         + 8ef3694f-3248-4f3b-83ef-cd6d34b2b27b

tests\unit\test_human_handoff.py:337: AssertionError
__________ test_handoff_status_reports_the_lower_configured_deadline __________

handoff_app = (<starlette.applications.Starlette object at 0x00000237FE54A3C0>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000237FE54AF60>

    async def test_handoff_status_reports_the_lower_configured_deadline(handoff_app, monkeypatch):
        app, _ = handoff_app
        manager = app.state.halo_service.research_session
    
        async def browser(url, profile, done, ready):
            ready()
            await done.wait()
    
        monkeypatch.setattr(manager.crawler, "human_handoff", browser)
        manager.crawler.limits.job_timeout_seconds = 30
        status = await manager.begin("https://example.org", "research")
>       assert status["timeout_seconds"] == 30
E       assert 120 == 30

tests\unit\test_human_handoff.py:354: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_human_handoff.py::test_finished_response_cannot_describe_a_newly_started_session
FAILED tests/unit/test_human_handoff.py::test_handoff_status_reports_the_lower_configured_deadline
2 failed, 17 deselected in 1.01s

```

### Race/deadline GREEN after restoring corrections

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py -k 'finished_response_cannot or lower_configured_deadline'
```

```text
..                                                                       [100%]
2 passed, 17 deselected in 0.87s

```

### Driver-start cancellation assertion RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
```

```text
.................FF                                                      [100%]
================================== FAILURES ===================================
______ test_cancel_during_driver_start_still_closes_that_driver[profile] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2151/test_cancel_during_driver_star0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001AE63843E00>
operation = 'profile'

    @pytest.mark.parametrize("operation", ["profile", "handoff"])
    async def test_cancel_during_driver_start_still_closes_that_driver(tmp_path, monkeypatch, operation):
        from playwright import async_api
    
        provider = Crawl4AIProvider(str(tmp_path))
        (tmp_path / "profiles" / "research").mkdir(parents=True)
        entered, release, stopped = asyncio.Event(), asyncio.Event(), asyncio.Event()
    
        class Driver:
            async def __aenter__(self):
                entered.set()
                await release.wait()
                return self
    
            async def __aexit__(self, *args):
                stopped.set()
    
        async def validate(*args):
            pass
    
        async def cookies(*args):
            return []
    
        monkeypatch.setattr(async_api, "async_playwright", Driver)
        monkeypatch.setattr(provider, "_validate_browser_request", validate)
        if operation == "handoff":
            monkeypatch.setattr(provider, "_profile_cookies", cookies)
            work = provider.human_handoff("https://example.org", "research", asyncio.Event(), lambda: None)
        else:
            work = provider._profile_cookies("research")
        task = asyncio.create_task(work)
        await asyncio.wait_for(entered.wait(), 1)
        task.cancel()
        await asyncio.sleep(0)
        release.set()
        result = await asyncio.gather(task, return_exceptions=True)
        assert isinstance(result[0], asyncio.CancelledError)
>       assert stopped.is_set(), "driver startup cancellation skipped its shutdown"
E       AssertionError: driver startup cancellation skipped its shutdown
E       assert False
E        +  where False = is_set()
E        +    where is_set = <asyncio.locks.Event object at 0x000001AE6399E7B0 [unset]>.is_set

tests\unit\test_human_handoff.py:394: AssertionError
______ test_cancel_during_driver_start_still_closes_that_driver[handoff] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2151/test_cancel_during_driver_star1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001AE6395E8D0>
operation = 'handoff'

    @pytest.mark.parametrize("operation", ["profile", "handoff"])
    async def test_cancel_during_driver_start_still_closes_that_driver(tmp_path, monkeypatch, operation):
        from playwright import async_api
    
        provider = Crawl4AIProvider(str(tmp_path))
        (tmp_path / "profiles" / "research").mkdir(parents=True)
        entered, release, stopped = asyncio.Event(), asyncio.Event(), asyncio.Event()
    
        class Driver:
            async def __aenter__(self):
                entered.set()
                await release.wait()
                return self
    
            async def __aexit__(self, *args):
                stopped.set()
    
        async def validate(*args):
            pass
    
        async def cookies(*args):
            return []
    
        monkeypatch.setattr(async_api, "async_playwright", Driver)
        monkeypatch.setattr(provider, "_validate_browser_request", validate)
        if operation == "handoff":
            monkeypatch.setattr(provider, "_profile_cookies", cookies)
            work = provider.human_handoff("https://example.org", "research", asyncio.Event(), lambda: None)
        else:
            work = provider._profile_cookies("research")
        task = asyncio.create_task(work)
        await asyncio.wait_for(entered.wait(), 1)
        task.cancel()
        await asyncio.sleep(0)
        release.set()
        result = await asyncio.gather(task, return_exceptions=True)
        assert isinstance(result[0], asyncio.CancelledError)
>       assert stopped.is_set(), "driver startup cancellation skipped its shutdown"
E       AssertionError: driver startup cancellation skipped its shutdown
E       assert False
E        +  where False = is_set()
E        +    where is_set = <asyncio.locks.Event object at 0x000001AE6399DB50 [unset]>.is_set

tests\unit\test_human_handoff.py:394: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_human_handoff.py::test_cancel_during_driver_start_still_closes_that_driver[profile]
FAILED tests/unit/test_human_handoff.py::test_cancel_during_driver_start_still_closes_that_driver[handoff]
2 failed, 17 passed in 2.99s

```

### Focused/native GREEN after lifecycle correction

```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
uv run --locked python -m pytest -q tests/acceptance/test_human_handoff_native.py
```

```text
109 files left unchanged
...................                                                      [100%]
19 passed in 1.90s
..
..                                                                     [100%]
4 passed in 6.82s

```

## Scope and delivery boundary

Base checkpoint: `a9cb02f229a44fffd2db47f7b725e4150b6c7ced`, clean main at start.
This record proves a source change and disposable tests, not installation or CI.
Version remains 0.2.0; fourteen MCP tools; no dependencies, installed credentials,
DSH settings, production profile imports, paid calls or website changes.

The operator can open a public research URL from an existing owned profile,
complete a human step and retain a bounded temporary cookie copy for subsequent
managed reads. Only a local operator CSRF-authorized request starts/finishes the
flow. There are no model click/form/action APIs. Cookies are held in memory,
not written back to imported profiles or the vault, and not returned in status.

## Files read / implementation / blast radius

Read repository AGENTS, research-only contract, original spec's handoff references,
crawler/provider/config/service/app/UI, vault/store/import and related tests,
quality gate, README/changelog/manual/operations/status and bundled scope before edits.
The existing browser request/redirect/WebSocket guard was moved into one reusable
method, preserving ordinary/local traversal behavior. A new bounded session manager,
operator routes and console controls reuse it. Browser and cookie-import operations
share ownership. Cancelled native copies settle under that lock before their receipt
and cancellation response; a completed same-profile import invalidates the temporary session.

## Verification and falsification

Fifteen new unit cases: CSRF/origin, private destinations, unknown/traversal profiles,
unsupported action arguments, one active session, stale completion, sanitized error/state,
temporary-cookie retention only on Done, cancellation/timeout, oversize rejection,
browser cleanup, shutdown clearing, import invalidation and copy-cancellation ownership.
Relevant baseline `70 passed in 16.17s`; final unit gate
`466 passed in 78.72s (0:01:18)`.

Native tests use actual owned Chrome and intercepted public-shaped fixture pages.
The test—not a real human—clicks a synthetic gate button. It then closes the
handoff and performs a service-level managed read, verifying the expected source
text/citation, cookie non-disclosure and process cleanup. This is not network-MCP,
real-account or DSH proof. Fixture hostname DNS is injected; no paid endpoint or
personal profile is used. The native test checks that cookie state is absent from
the original owned profile after service shutdown. Chromium can create its normal
housekeeping files while reading that profile.

The UI ran in real Chrome at 1280 and 390 CSS pixels. Opening, waiting, ready,
cancelled, timed-out, failed and idle states and button enablement passed;
no page errors were observed. Desktop/mobile screenshots were inspected.
Existing traversal/challenge tests also ran: `11 passed in 24.51s`.
Those prior tests include a real public header echo and a local fake vendor,
not a live paid call. The UI behavior was initially implemented before its native
state check; this is runtime verification, not a claim that all UI code had RED tests.

## Security checklist

- Input validation: PASS for exact field sets, public URL policy, existing owned
  profile name/path, opaque current-session identity and supported operations.
- Changed routes/auth: PASS for existing loopback operator origin/CSRF controls;
  no MCP tool addition. This is not protection from another process running as Scott.
- Secrets: no source URLs/cookies in returned status except the public origin and
  operator-chosen profile label; browser exceptions are replaced with stable errors.
  Fixture values are synthetic. No credential import or paid dispatch in this work.
- Rendering/eval/deserialization: status uses textContent; no model/script execution
  interface. JSON input uses existing operator conventions, not pickle/eval.
- Dependencies: N/A, no dependency or lockfile change.

## Known limits / not acceptance claims

- One active handoff; at most 120 seconds (or lower crawl job timeout) including
  lock wait/startup/human step. Native cleanup/driver hangs have no hard deadline.
- One completed cookie set, at most 5000 cookies/2 MiB JSON. Cleared on shutdown,
  same-profile successful import, or replaced on another completed handoff.
- Cancel/timeout/window-close/failure discards that attempt, not an earlier
  completed temporary session. A retry must prove source readability.
- Cookies only: local storage, device-bound credentials and browser fingerprints
  are not carried over. Real login/app-bound-cookie compatibility remains unproved.
- Same-tab public redirects allowed; popup and private/local login unsupported.
  Existing Chromium DNS pinning/OOPIF/subresource resource-bound gaps remain.
- No manual challenge step through actual DSH, installed handoff, paid provider,
  full workflow, clean install, package/tag or full project completion is claimed.
- Original import-copy duration, general HTTP request-body limits and wider
  shutdown/provider stress are not solved by this bounded handoff.
- The skill required baseline, assertion REDs, raw failures, widened runs and
  documentation sync. No existing assertion was weakened, skipped or removed.

## Exact execution evidence

All commands below ran from
`C:\Users\scott\Desktop\Code\halo-research-gateway`.
Initial failed test-author/lint runs are retained rather than counted as proof.

### Relevant unchanged baseline

```powershell
uv run --locked python -m pytest -q tests/unit/test_crawl_options.py tests/unit/test_challenge_routing.py tests/unit/test_operator_ui.py tests/unit/test_research_scope.py
```

```text
...............
.......................................................   [100%]
70 passed in 16.17s

```

### Initial test-author mistake (HTTPX client re-entry)

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
```

```text
FFFFFFFFF                                                                [100%]
================================== FAILURES ===================================
__________ test_handoff_requires_operator_csrf_and_origin[headers0] ___________

handoff_app = (<starlette.applications.Starlette object at 0x0000017029142B40>, [])
headers = {'x-halo-csrf': 'wrong'}

    @pytest.mark.parametrize("headers", [{"x-halo-csrf": "wrong"}, {"origin": "https://untrusted.example"}])
    async def test_handoff_requires_operator_csrf_and_origin(handoff_app, headers):
        app, calls = handoff_app
>       async with await operator_client(app) as client:
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_human_handoff.py:42: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <httpx.AsyncClient object at 0x0000017029141DF0>

    async def __aenter__(self: U) -> U:
        if self._state != ClientState.UNOPENED:
            msg = {
                ClientState.OPENED: "Cannot open a client instance more than once.",
                ClientState.CLOSED: (
                    "Cannot reopen a client instance, once it has been closed."
                ),
            }[self._state]
>           raise RuntimeError(msg)
E           RuntimeError: Cannot open a client instance more than once.

.venv\Lib\site-packages\httpx\_client.py:1998: RuntimeError
__________ test_handoff_requires_operator_csrf_and_origin[headers1] ___________

handoff_app = (<starlette.applications.Starlette object at 0x00000170291D3BF0>, [])
headers = {'origin': 'https://untrusted.example'}

    @pytest.mark.parametrize("headers", [{"x-halo-csrf": "wrong"}, {"origin": "https://untrusted.example"}])
    async def test_handoff_requires_operator_csrf_and_origin(handoff_app, headers):
        app, calls = handoff_app
>       async with await operator_client(app) as client:
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_human_handoff.py:42: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <httpx.AsyncClient object at 0x00000170292C1C70>

    async def __aenter__(self: U) -> U:
        if self._state != ClientState.UNOPENED:
            msg = {
                ClientState.OPENED: "Cannot open a client instance more than once.",
                ClientState.CLOSED: (
                    "Cannot reopen a client instance, once it has been closed."
                ),
            }[self._state]
>           raise RuntimeError(msg)
E           RuntimeError: Cannot open a client instance more than once.

.venv\Lib\site-packages\httpx\_client.py:1998: RuntimeError
_ test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values0] _

handoff_app = (<starlette.applications.Starlette object at 0x00000170291D3C80>, [])
values = {'url': 'http://127.0.0.1/private', 'profile': 'research'}

    @pytest.mark.parametrize("values", [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ])
    async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
        app, _ = handoff_app
>       async with await operator_client(app) as client:
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_human_handoff.py:59: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <httpx.AsyncClient object at 0x00000170292C2D20>

    async def __aenter__(self: U) -> U:
        if self._state != ClientState.UNOPENED:
            msg = {
                ClientState.OPENED: "Cannot open a client instance more than once.",
                ClientState.CLOSED: (
                    "Cannot reopen a client instance, once it has been closed."
                ),
            }[self._state]
>           raise RuntimeError(msg)
E           RuntimeError: Cannot open a client instance more than once.

.venv\Lib\site-packages\httpx\_client.py:1998: RuntimeError
_ test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values1] _

handoff_app = (<starlette.applications.Starlette object at 0x00000170293837A0>, [])
values = {'url': 'https://example.org/read', 'profile': '../personal'}

    @pytest.mark.parametrize("values", [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ])
    async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
        app, _ = handoff_app
>       async with await operator_client(app) as client:
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_human_handoff.py:59: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <httpx.AsyncClient object at 0x00000170294F8BC0>

    async def __aenter__(self: U) -> U:
        if self._state != ClientState.UNOPENED:
            msg = {
                ClientState.OPENED: "Cannot open a client instance more than once.",
                ClientState.CLOSED: (
                    "Cannot reopen a client instance, once it has been closed."
                ),
            }[self._state]
>           raise RuntimeError(msg)
E           RuntimeError: Cannot open a client instance more than once.

.venv\Lib\site-packages\httpx\_client.py:1998: RuntimeError
_ test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values2] _

handoff_app = (<starlette.applications.Starlette object at 0x00000170294FB290>, [])
values = {'url': 'https://example.org/read', 'profile': 'missing'}

    @pytest.mark.parametrize("values", [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ])
    async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
        app, _ = handoff_app
>       async with await operator_client(app) as client:
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_human_handoff.py:59: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <httpx.AsyncClient object at 0x0000017029589AF0>

    async def __aenter__(self: U) -> U:
        if self._state != ClientState.UNOPENED:
            msg = {
                ClientState.OPENED: "Cannot open a client instance more than once.",
                ClientState.CLOSED: (
                    "Cannot reopen a client instance, once it has been closed."
                ),
            }[self._state]
>           raise RuntimeError(msg)
E           RuntimeError: Cannot open a client instance more than once.

.venv\Lib\site-packages\httpx\_client.py:1998: RuntimeError
_ test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values3] _

handoff_app = (<starlette.applications.Starlette object at 0x000001702958AEA0>, [])
values = {'url': 'https://example.org/read', 'profile': 'research', 'click': 'Buy'}

    @pytest.mark.parametrize("values", [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ])
    async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
        app, _ = handoff_app
>       async with await operator_client(app) as client:
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_human_handoff.py:59: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <httpx.AsyncClient object at 0x0000017029444530>

    async def __aenter__(self: U) -> U:
        if self._state != ClientState.UNOPENED:
            msg = {
                ClientState.OPENED: "Cannot open a client instance more than once.",
                ClientState.CLOSED: (
                    "Cannot reopen a client instance, once it has been closed."
                ),
            }[self._state]
>           raise RuntimeError(msg)
E           RuntimeError: Cannot open a client instance more than once.

.venv\Lib\site-packages\httpx\_client.py:1998: RuntimeError
________ test_handoff_is_one_operator_session_with_no_secrets_in_state ________

handoff_app = (<starlette.applications.Starlette object at 0x0000017029445910>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000017029533710>

    async def test_handoff_is_one_operator_session_with_no_secrets_in_state(handoff_app, monkeypatch):
        app, calls = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x00000170294471A0>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x00000170294471A0> = <halo_research_gateway.service.HaloService object at 0x0000017029447050>.crawler

tests\unit\test_human_handoff.py:67: AssertionError
_____________ test_stale_done_cannot_complete_a_different_session _____________

handoff_app = (<starlette.applications.Starlette object at 0x0000017029401160>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000170294459D0>

    async def test_stale_done_cannot_complete_a_different_session(handoff_app, monkeypatch):
        app, _ = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x00000170294007D0>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x00000170294007D0> = <halo_research_gateway.service.HaloService object at 0x0000017029403B00>.crawler

tests\unit\test_human_handoff.py:102: AssertionError
____________ test_failed_browser_does_not_return_exception_secrets ____________

handoff_app = (<starlette.applications.Starlette object at 0x0000017029604E60>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000170295A7F20>

    async def test_failed_browser_does_not_return_exception_secrets(handoff_app, monkeypatch):
        app, _ = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x00000170296044D0>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x00000170296044D0> = <halo_research_gateway.service.HaloService object at 0x0000017029604290>.crawler

tests\unit\test_human_handoff.py:121: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_human_handoff.py::test_handoff_requires_operator_csrf_and_origin[headers0]
FAILED tests/unit/test_human_handoff.py::test_handoff_requires_operator_csrf_and_origin[headers1]
FAILED tests/unit/test_human_handoff.py::test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values0]
FAILED tests/unit/test_human_handoff.py::test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values1]
FAILED tests/unit/test_human_handoff.py::test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values2]
FAILED tests/unit/test_human_handoff.py::test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values3]
FAILED tests/unit/test_human_handoff.py::test_handoff_is_one_operator_session_with_no_secrets_in_state
FAILED tests/unit/test_human_handoff.py::test_stale_done_cannot_complete_a_different_session
FAILED tests/unit/test_human_handoff.py::test_failed_browser_does_not_return_exception_secrets
9 failed in 2.22s

```

### Corrected interface assertion RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
```

```text
FFFFFFFFF                                                                [100%]
================================== FAILURES ===================================
__________ test_handoff_requires_operator_csrf_and_origin[headers0] ___________

handoff_app = (<starlette.applications.Starlette object at 0x0000023777836ED0>, [])
headers = {'x-halo-csrf': 'wrong'}

    @pytest.mark.parametrize("headers", [{"x-halo-csrf": "wrong"}, {"origin": "https://untrusted.example"}])
    async def test_handoff_requires_operator_csrf_and_origin(handoff_app, headers):
        app, calls = handoff_app
        async with operator_client(app) as client:
            response = await client.post(
                "/operator/api/research-session", headers=headers,
                json={"url": "https://example.org/read", "profile": "research"},
            )
>           assert response.status_code == 403
E           assert 404 == 403
E            +  where 404 = <Response [404 Not Found]>.status_code

tests\unit\test_human_handoff.py:49: AssertionError
__________ test_handoff_requires_operator_csrf_and_origin[headers1] ___________

handoff_app = (<starlette.applications.Starlette object at 0x00000237778C7C50>, [])
headers = {'origin': 'https://untrusted.example'}

    @pytest.mark.parametrize("headers", [{"x-halo-csrf": "wrong"}, {"origin": "https://untrusted.example"}])
    async def test_handoff_requires_operator_csrf_and_origin(handoff_app, headers):
        app, calls = handoff_app
        async with operator_client(app) as client:
            response = await client.post(
                "/operator/api/research-session", headers=headers,
                json={"url": "https://example.org/read", "profile": "research"},
            )
>           assert response.status_code == 403
E           assert 404 == 403
E            +  where 404 = <Response [404 Not Found]>.status_code

tests\unit\test_human_handoff.py:49: AssertionError
_ test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values0] _

handoff_app = (<starlette.applications.Starlette object at 0x000002377799B260>, [])
values = {'url': 'http://127.0.0.1/private', 'profile': 'research'}

    @pytest.mark.parametrize("values", [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ])
    async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
        app, _ = handoff_app
        async with operator_client(app) as client:
            response = await client.post("/operator/api/research-session", json=values)
>           assert response.status_code == 400
E           assert 404 == 400
E            +  where 404 = <Response [404 Not Found]>.status_code

tests\unit\test_human_handoff.py:63: AssertionError
_ test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values1] _

handoff_app = (<starlette.applications.Starlette object at 0x0000023777A644A0>, [])
values = {'url': 'https://example.org/read', 'profile': '../personal'}

    @pytest.mark.parametrize("values", [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ])
    async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
        app, _ = handoff_app
        async with operator_client(app) as client:
            response = await client.post("/operator/api/research-session", json=values)
>           assert response.status_code == 400
E           assert 404 == 400
E            +  where 404 = <Response [404 Not Found]>.status_code

tests\unit\test_human_handoff.py:63: AssertionError
_ test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values2] _

handoff_app = (<starlette.applications.Starlette object at 0x0000023777ADBE30>, [])
values = {'url': 'https://example.org/read', 'profile': 'missing'}

    @pytest.mark.parametrize("values", [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ])
    async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
        app, _ = handoff_app
        async with operator_client(app) as client:
            response = await client.post("/operator/api/research-session", json=values)
>           assert response.status_code == 400
E           assert 404 == 400
E            +  where 404 = <Response [404 Not Found]>.status_code

tests\unit\test_human_handoff.py:63: AssertionError
_ test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values3] _

handoff_app = (<starlette.applications.Starlette object at 0x0000023777B66DE0>, [])
values = {'url': 'https://example.org/read', 'profile': 'research', 'click': 'Buy'}

    @pytest.mark.parametrize("values", [
        {"url": "http://127.0.0.1/private", "profile": "research"},
        {"url": "https://example.org/read", "profile": "../personal"},
        {"url": "https://example.org/read", "profile": "missing"},
        {"url": "https://example.org/read", "profile": "research", "click": "Buy"},
    ])
    async def test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments(handoff_app, values):
        app, _ = handoff_app
        async with operator_client(app) as client:
            response = await client.post("/operator/api/research-session", json=values)
>           assert response.status_code == 400
E           assert 404 == 400
E            +  where 404 = <Response [404 Not Found]>.status_code

tests\unit\test_human_handoff.py:63: AssertionError
________ test_handoff_is_one_operator_session_with_no_secrets_in_state ________

handoff_app = (<starlette.applications.Starlette object at 0x0000023777BDF5F0>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000023777BDE9F0>

    async def test_handoff_is_one_operator_session_with_no_secrets_in_state(handoff_app, monkeypatch):
        app, calls = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x0000023777BDEB10>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x0000023777BDEB10> = <halo_research_gateway.service.HaloService object at 0x0000023777BDEA20>.crawler

tests\unit\test_human_handoff.py:69: AssertionError
_____________ test_stale_done_cannot_complete_a_different_session _____________

handoff_app = (<starlette.applications.Starlette object at 0x0000023777C5D5B0>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000023777BDFEC0>

    async def test_stale_done_cannot_complete_a_different_session(handoff_app, monkeypatch):
        app, _ = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x0000023777BDDB50>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x0000023777BDDB50> = <halo_research_gateway.service.HaloService object at 0x0000023777BDD970>.crawler

tests\unit\test_human_handoff.py:104: AssertionError
____________ test_failed_browser_does_not_return_exception_secrets ____________

handoff_app = (<starlette.applications.Starlette object at 0x0000023777CECE30>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000023777C8E330>

    async def test_failed_browser_does_not_return_exception_secrets(handoff_app, monkeypatch):
        app, _ = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x0000023777CEC2C0>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x0000023777CEC2C0> = <halo_research_gateway.service.HaloService object at 0x0000023777CEFB30>.crawler

tests\unit\test_human_handoff.py:123: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_human_handoff.py::test_handoff_requires_operator_csrf_and_origin[headers0]
FAILED tests/unit/test_human_handoff.py::test_handoff_requires_operator_csrf_and_origin[headers1]
FAILED tests/unit/test_human_handoff.py::test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values0]
FAILED tests/unit/test_human_handoff.py::test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values1]
FAILED tests/unit/test_human_handoff.py::test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values2]
FAILED tests/unit/test_human_handoff.py::test_handoff_rejects_private_targets_unknown_profiles_and_action_arguments[values3]
FAILED tests/unit/test_human_handoff.py::test_handoff_is_one_operator_session_with_no_secrets_in_state
FAILED tests/unit/test_human_handoff.py::test_stale_done_cannot_complete_a_different_session
FAILED tests/unit/test_human_handoff.py::test_failed_browser_does_not_return_exception_secrets
9 failed in 2.37s

```

### Test-author placement error, not a valid RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
```

```text

=================================== ERRORS ====================================
______________ ERROR collecting tests/unit/test_human_handoff.py ______________
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
E     File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\unit\test_human_handoff.py", line 202
E       assert "private-path" not in json.dumps(state)
E   IndentationError: unexpected indent
=========================== short test summary info ===========================
ERROR tests/unit/test_human_handoff.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.32s

```

### Corrected browser assertion RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
```

```text
......FFFFFFF                                                            [100%]
================================== FAILURES ===================================
________ test_handoff_is_one_operator_session_with_no_secrets_in_state ________

handoff_app = (<starlette.applications.Starlette object at 0x000001E49DB7A9F0>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001E49D721A90>

    async def test_handoff_is_one_operator_session_with_no_secrets_in_state(handoff_app, monkeypatch):
        app, calls = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49DE6AC60>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49DE6AC60> = <halo_research_gateway.service.HaloService object at 0x000001E49DE69910>.crawler

tests\unit\test_human_handoff.py:70: AssertionError
_____________ test_stale_done_cannot_complete_a_different_session _____________

handoff_app = (<starlette.applications.Starlette object at 0x000001E49DE2E240>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001E49DE2F110>

    async def test_stale_done_cannot_complete_a_different_session(handoff_app, monkeypatch):
        app, _ = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49DE2D760>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49DE2D760> = <halo_research_gateway.service.HaloService object at 0x000001E49DE2D4F0>.crawler

tests\unit\test_human_handoff.py:107: AssertionError
____________ test_failed_browser_does_not_return_exception_secrets ____________

handoff_app = (<starlette.applications.Starlette object at 0x000001E49DF48FE0>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001E49DEF7DA0>

    async def test_failed_browser_does_not_return_exception_secrets(handoff_app, monkeypatch):
        app, _ = handoff_app
        service = app.state.halo_service
>       assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
E       AssertionError: no human research handoff exists
E       assert False
E        +  where False = hasattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49DF485F0>, 'human_handoff')
E        +    where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49DF485F0> = <halo_research_gateway.service.HaloService object at 0x000001E49DF48320>.crawler

tests\unit\test_human_handoff.py:126: AssertionError
_ test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser[done] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2135/test_temporary_cookie_handoff_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001E49DF72150>
completion = 'done'

    @pytest.mark.parametrize("completion", ["done", "cancel", "timeout", "oversized"])
    async def test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser(tmp_path, monkeypatch, completion):
        from playwright import async_api
    
        provider = Crawl4AIProvider(str(tmp_path))
>       assert callable(getattr(provider, "human_handoff", None)), "missing browser handoff implementation"
E       AssertionError: missing browser handoff implementation
E       assert False
E        +  where False = callable(None)
E        +    where None = getattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49DBFF110>, 'human_handoff', None)

tests\unit\test_human_handoff.py:146: AssertionError
_ test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser[cancel] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2135/test_temporary_cookie_handoff_1')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001E49E0A26C0>
completion = 'cancel'

    @pytest.mark.parametrize("completion", ["done", "cancel", "timeout", "oversized"])
    async def test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser(tmp_path, monkeypatch, completion):
        from playwright import async_api
    
        provider = Crawl4AIProvider(str(tmp_path))
>       assert callable(getattr(provider, "human_handoff", None)), "missing browser handoff implementation"
E       AssertionError: missing browser handoff implementation
E       assert False
E        +  where False = callable(None)
E        +    where None = getattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49E0A0BC0>, 'human_handoff', None)

tests\unit\test_human_handoff.py:146: AssertionError
_ test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser[timeout] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2135/test_temporary_cookie_handoff_2')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001E49E0A3170>
completion = 'timeout'

    @pytest.mark.parametrize("completion", ["done", "cancel", "timeout", "oversized"])
    async def test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser(tmp_path, monkeypatch, completion):
        from playwright import async_api
    
        provider = Crawl4AIProvider(str(tmp_path))
>       assert callable(getattr(provider, "human_handoff", None)), "missing browser handoff implementation"
E       AssertionError: missing browser handoff implementation
E       assert False
E        +  where False = callable(None)
E        +    where None = getattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49E0A1580>, 'human_handoff', None)

tests\unit\test_human_handoff.py:146: AssertionError
_ test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser[oversized] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2135/test_temporary_cookie_handoff_3')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000001E49E0A1E80>
completion = 'oversized'

    @pytest.mark.parametrize("completion", ["done", "cancel", "timeout", "oversized"])
    async def test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser(tmp_path, monkeypatch, completion):
        from playwright import async_api
    
        provider = Crawl4AIProvider(str(tmp_path))
>       assert callable(getattr(provider, "human_handoff", None)), "missing browser handoff implementation"
E       AssertionError: missing browser handoff implementation
E       assert False
E        +  where False = callable(None)
E        +    where None = getattr(<halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x000001E49E0A22D0>, 'human_handoff', None)

tests\unit\test_human_handoff.py:146: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_human_handoff.py::test_handoff_is_one_operator_session_with_no_secrets_in_state
FAILED tests/unit/test_human_handoff.py::test_stale_done_cannot_complete_a_different_session
FAILED tests/unit/test_human_handoff.py::test_failed_browser_does_not_return_exception_secrets
FAILED tests/unit/test_human_handoff.py::test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser[done]
FAILED tests/unit/test_human_handoff.py::test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser[cancel]
FAILED tests/unit/test_human_handoff.py::test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser[timeout]
FAILED tests/unit/test_human_handoff.py::test_temporary_cookie_handoff_retains_only_on_done_and_closes_browser[oversized]
7 failed, 6 passed in 2.15s

```

### First focused GREEN

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py tests/unit/test_crawl_options.py tests/unit/test_challenge_routing.py tests/unit/test_operator_ui.py tests/unit/test_research_scope.py
```

```text
...........................
............................................. [ 86%]
...........                                                              [100%]
83 passed in 15.89s

```

### Initial native fixture import error

```powershell
uv run --locked python -m pytest -q tests/acceptance/test_human_handoff_native.py
```

```text

=================================== ERRORS ====================================
_______ ERROR collecting tests/acceptance/test_human_handoff_native.py ________
ImportError while importing test module 'C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\test_human_handoff_native.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
..\..\..\AppData\Local\Programs\Python\Python312\Lib\importlib\__init__.py:90: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\acceptance\test_human_handoff_native.py:14: in <module>
    from test_crawl_options import application_at
E   ModuleNotFoundError: No module named 'test_crawl_options'
=========================== short test summary info ===========================
ERROR tests/acceptance/test_human_handoff_native.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 error in 0.20s

```

### Corrected native fixture

```powershell
uv run --locked python -m pytest -q tests/acceptance/test_human_handoff_native.py
```

```text
.                                                                        [100%]
1 passed in 5.22s

```

### Health/import-ownership assertion RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
```

```text
......F......F                                                           [100%]
================================== FAILURES ===================================
________ test_handoff_is_one_operator_session_with_no_secrets_in_state ________

handoff_app = (<starlette.applications.Starlette object at 0x0000026EFCF74560>, [('browser', 'https://example.org/private-path?token=fixture-secret', 'research')])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000026EFCF32AB0>

    async def test_handoff_is_one_operator_session_with_no_secrets_in_state(handoff_app, monkeypatch):
        app, calls = handoff_app
        service = app.state.halo_service
        assert hasattr(service.crawler, "human_handoff"), "no human research handoff exists"
        opened = asyncio.Event()
    
        async def browser(url, profile, done, ready):
            calls.append(("browser", url, profile))
            ready()
            opened.set()
            await done.wait()
    
        monkeypatch.setattr(service.crawler, "human_handoff", browser)
        async with operator_client(app) as client:
            response = await client.post(
                "/operator/api/research-session",
                json={
                    "url": "https://example.org/private-path?token=fixture-secret",
                    "profile": "research",
                },
            )
            assert response.status_code == 202
            await asyncio.wait_for(opened.wait(), 1)
            state = (await client.get("/operator/api/state")).json()["research_session"]
            assert state["state"] == "waiting_for_operator"
>           assert service.health().get("research_session") == "waiting_for_operator"
E           AssertionError: assert None == 'waiting_for_operator'
E            +  where None = <built-in method get of dict object at 0x0000026EFD0F8500>('research_session')
E            +    where <built-in method get of dict object at 0x0000026EFD0F8500> = {'status': 'ok', 'version': '0.2.0', 'result_schema_version': '1.5', 'database_schema_version': 3, ...}.get
E            +      where {'status': 'ok', 'version': '0.2.0', 'result_schema_version': '1.5', 'database_schema_version': 3, ...} = health()
E            +        where health = <halo_research_gateway.service.HaloService object at 0x0000026EFD06DFA0>.health

tests\unit\test_human_handoff.py:96: AssertionError
____ test_cookie_import_clears_temporary_session_only_for_replaced_profile ____

handoff_app = (<starlette.applications.Starlette object at 0x0000026EFD33B860>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000026EFD6708C0>

    async def test_cookie_import_clears_temporary_session_only_for_replaced_profile(handoff_app, monkeypatch):
        app, _ = handoff_app
        service = app.state.halo_service
        provider = service.crawler
        provider._human_cookies = ("research", [{"name": "old", "value": "fixture-only"}])
    
        async def execute(plan_id, token, key, executor):
            return await executor({"action": "chrome_import", "import": {"destination_name": plan_id}})
    
        def import_profile(plan):
            assert provider._lock.locked(), "profile import raced a live research browser"
            return {"status": "imported"}
    
        monkeypatch.setattr(service.import_reviews, "execute", execute)
        monkeypatch.setattr(service.chrome_importer, "execute", import_profile)
>       await service.chrome_import_execute("other", "fixture", "fixture")

tests\unit\test_human_handoff.py:281: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _
src\halo_research_gateway\service.py:162: in chrome_import_execute
    return await self.import_reviews.execute(plan_id, approval_token, idempotency_key, executor)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
tests\unit\test_human_handoff.py:273: in execute
    return await executor({"action": "chrome_import", "import": {"destination_name": plan_id}})
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src\halo_research_gateway\service.py:160: in executor
    return await asyncio.to_thread(self.chrome_importer.execute, plan["import"])
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\AppData\Local\Programs\Python\Python312\Lib\asyncio\threads.py:25: in to_thread
    return await loop.run_in_executor(None, func_call)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\AppData\Local\Programs\Python\Python312\Lib\concurrent\futures\thread.py:59: in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

plan = {'destination_name': 'other'}

    def import_profile(plan):
>       assert provider._lock.locked(), "profile import raced a live research browser"
E       AssertionError: profile import raced a live research browser
E       assert False
E        +  where False = locked()
E        +    where locked = <asyncio.locks.Lock object at 0x0000026EFD3947D0 [unlocked]>.locked
E        +      where <asyncio.locks.Lock object at 0x0000026EFD3947D0 [unlocked]> = <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x0000026EFD3E9610>._lock

tests\unit\test_human_handoff.py:276: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_human_handoff.py::test_handoff_is_one_operator_session_with_no_secrets_in_state
FAILED tests/unit/test_human_handoff.py::test_cookie_import_clears_temporary_session_only_for_replaced_profile
2 failed, 12 passed in 2.58s

```

### Native/UI state check

```powershell
$env:HALO_UI_EVIDENCE_DIR='C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\human-handoff'
uv run --locked python -m pytest -q tests/acceptance/test_human_handoff_native.py
```

```text
..                                                                       [100%]
2 passed in 6.36s

```

### Widened focused GREEN

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py tests/unit/test_crawl_options.py tests/unit/test_challenge_routing.py tests/unit/test_operator_ui.py tests/unit/test_research_scope.py
```

```text
............................
............................................ [ 85%]
............                                                             [100%]
84 passed in 16.58s

```

### Native-copy cancellation assertion RED

```powershell
uv run --locked python -m pytest -q tests/unit/test_human_handoff.py
```

```text
..............F                                                          [100%]
================================== FAILURES ===================================
_________ test_cancelled_import_keeps_profile_lock_until_copy_settles _________

handoff_app = (<starlette.applications.Starlette object at 0x00000255A5AF7D70>, [])
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000255A58B46B0>

    async def test_cancelled_import_keeps_profile_lock_until_copy_settles(handoff_app, monkeypatch):
        app, _ = handoff_app
        service = app.state.halo_service
        entered = asyncio.Event()
        release = threading.Event()
        loop = asyncio.get_running_loop()
    
        def import_profile(plan):
            loop.call_soon_threadsafe(entered.set)
            assert release.wait(5)
            return {"status": "imported"}
    
        async def execute(plan_id, token, key, executor):
            return await executor({"action": "chrome_import", "import": {"destination_name": "research"}})
    
        monkeypatch.setattr(service.import_reviews, "execute", execute)
        monkeypatch.setattr(service.chrome_importer, "execute", import_profile)
        task = asyncio.create_task(service.chrome_import_execute("research", "fixture", "fixture"))
        try:
            await asyncio.wait_for(entered.wait(), 2)
            task.cancel()
            await asyncio.sleep(0.02)
>           assert service.crawler._lock.locked(), "cancel released ownership while the profile copy was still running"
E           AssertionError: cancel released ownership while the profile copy was still running
E           assert False
E            +  where False = locked()
E            +    where locked = <asyncio.locks.Lock object at 0x00000255A5AF5C10 [unlocked]>.locked
E            +      where <asyncio.locks.Lock object at 0x00000255A5AF5C10 [unlocked]> = <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x00000255A5AF5BE0>._lock
E            +        where <halo_research_gateway.providers.crawl4ai_provider.Crawl4AIProvider object at 0x00000255A5AF5BE0> = <halo_research_gateway.service.HaloService object at 0x00000255A5AF41D0>.crawler

tests\unit\test_human_handoff.py:310: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_human_handoff.py::test_cancelled_import_keeps_profile_lock_until_copy_settles
1 failed, 14 passed in 1.87s

```

### Initial full gate lint failures

```powershell
uv run --locked ruff check --fix tests/unit/test_human_handoff.py tests/acceptance/test_human_handoff_native.py
uv run --locked ruff format src tests
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

```text
ASYNC110 Use `asyncio.Event` instead of awaiting `asyncio.sleep` in a `while` loop
   --> tests\acceptance\test_human_handoff_native.py:114:9
    |
112 |           await service.close()
113 |       async with asyncio.timeout(15):
114 | /         while {p.pid for p in psutil.Process().children(recursive=True)} - before:
115 | |             await asyncio.sleep(0.1)
    | |____________________________________^

ASYNC240 Async functions should not use pathlib.Path methods, use trio.Path or anyio.path
   --> tests\acceptance\test_human_handoff_native.py:129:5
    |
127 |     errors = []
128 |     evidence = Path(os.environ.get("HALO_UI_EVIDENCE_DIR", str(tmp_path)))
129 |     evidence.mkdir(parents=True, exist_ok=True)
    |     ^^^^^^^^^^^^^^
130 |     try:
131 |         async with async_playwright() as driver:
    |

Found 3 errors (1 fixed, 2 remaining).
1 file reformatted, 108 files left unchanged
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
109 files already formatted
[GATE] lint
ASYNC110 Use `asyncio.Event` instead of awaiting `asyncio.sleep` in a `while` loop
   --> tests\acceptance\test_human_handoff_native.py:118:9
    |
116 |           await service.close()
117 |       async with asyncio.timeout(15):
118 | /         while {p.pid for p in psutil.Process().children(recursive=True)} - before:
119 | |             await asyncio.sleep(0.1)
    | |____________________________________^

ASYNC240 Async functions should not use pathlib.Path methods, use trio.Path or anyio.path
   --> tests\acceptance\test_human_handoff_native.py:138:5
    |
136 |     errors = []
137 |     evidence = Path(os.environ.get("HALO_UI_EVIDENCE_DIR", str(tmp_path)))
138 |     evidence.mkdir(parents=True, exist_ok=True)
    |     ^^^^^^^^^^^^^^
139 |     try:
140 |         async with async_playwright() as driver:
    |

Found 2 errors.
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | lint failed with exit code 1

```

### Full gate after lint corrections

```powershell
uv run --locked ruff format src tests
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

```text
109 files left unchanged
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
109 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 15%]
............
............................................................ [ 30%]
........................................................................ [ 46%]
.............................................................
........... [ 61%]
........................................................................ [ 77%]
........................................................................ [ 92%]
..................................                                       [100%]
466 passed in 78.72s (0:01:18)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```

### Broader native/browser/UI check

```powershell
$env:HALO_UI_EVIDENCE_DIR='C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\human-handoff'
uv run --locked python -m pytest -q tests/acceptance/test_human_handoff_native.py tests/acceptance/test_crawl_traversal_native.py tests/acceptance/test_challenge_native.py
```

```text
..
.........                                                              [100%]
11 passed in 24.51s

```
