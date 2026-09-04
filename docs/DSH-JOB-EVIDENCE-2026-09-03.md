# DSH research jobs and safe errors — 2026-09-03

## Result and scope

Installed DSH durable-job acceptance now passes the requested lifecycle:
active pause and frozen progress, same-job resume to completion, active cancel
with stable cleanup, interruption/restart recovery, retained evidence, and
honest reporting of a non-empty terminal partial failure. The optional DSH
state adapter now generates a canonical `halo-job-receipt/v1` receipt directly
from durable tool results and rejects missing or contradictory lifecycle counts.

The earlier jobs that completed before pause, invalid model summaries, flaky
zero-evidence discovery attempts, and a recovery job that completed before a
manual restart remain recorded below. They are not retroactively counted as
passes. The final accepted runs used the unchanged local
`lmstudio / halo/qwen3.6-35b-a3b` route, the installed 0.3.0 Gateway, public
sources, no account or paid provider, and no model/permission change.

Known control failures still use the bounded safe envelope:
`JOB_NOT_FOUND`, `JOB_NOT_OWNED`, `JOB_STATE_CONFLICT`,
`INVALID_JOB_LIMITS`, `JOB_CAPACITY_REACHED` and `INVALID_ARGUMENT`.
Unknown exceptions remain SDK-sanitized. This work changes only the optional
DSH evidence ledger/final-report guard; it does not change the Gateway job state
machine, MCP schema, ownership, model, preset permissions, connections, browser
profiles, dependencies or fourteen-tool surface. Version remains 0.3.0 and the
Git tag still requires owner approval.

## Accepted installed DSH lifecycle evidence

| Scenario | DSH session | Job | Authoritative result |
| --- | --- | --- | --- |
| Pause, freeze, resume | `session-2d216831-1669-4333-8cdb-5d3a986aaeca` | `8ac4f188-b1fd-477c-b97b-530da436c750` | Pause captured active progress at attempted 17 / completed 16 / remaining 34. Two paused statuses kept the same counters. Resume preserved 17/16 and the same job completed at 25/24/26 with `partial=true`; one retained continuation was read. |
| Active cancel and cleanup | `session-689612fd-fabc-4df0-aee4-bb6c3013996f` | `854770bb-0e3c-43c2-be93-381d16071c44` | Cancel returned `cancelled` at 17/16/34. Two later DSH statuses stayed cancelled with identical counters. Gateway health then reported zero queued, running and paused jobs; 139 pre-existing DSH sessions were retained. |
| Installed restart recovery | `session-44c32c40-3984-4d4f-b63f-4b1bb9bbd52f` | `df2831ac-aab1-4c0e-afa6-e4728302e9db` | DSH created the job; sub-second observation caught it running at 16/15/65 and immediately ran the official Gateway stop/start scripts. `started_at` changed from `2026-09-04T01:15:29.131368Z` to `2026-09-04T01:18:52.094275Z`. The original DSH session recovered it as `paused_recoverable` at 17/16/64 with `JOB_RECOVERED_AFTER_INTERRUPTION`, resumed the same ID, observed 33/31/49 running, then completed at 41/40/40 with `partial=true` and one continuation. |
| Honest non-empty failure | `session-468caff9-7a3c-4e66-8375-3bd2fb2037b2` | `5ab54fdf-9a79-45a3-8569-b146f2443d76` | The job advanced through 17/16/64 and failed at 23/22/58 with `JOB_CHECKPOINT_TOO_LARGE`, `partial=true`, retained warnings/evidence and one continuation. Its final prose and canonical receipt agree under the current verifier replay. It is explicitly reported as partial failure, not success. |

The restart harness cancelled only the DSH model turn after the owned create,
polled that exact DSH-created job to close the model-latency race, and restarted
only the recorded Gateway through `Stop-HaloResearch.ps1` and
`Start-HaloResearch.ps1`. The pre-restart direct checkpoint is identified as
direct orchestration evidence; recovery status/resume/terminal reporting all
ran through the original DSH session. No job or session owned by another run
was cancelled or removed.

The failure report was replayed through the final receipt verifier after the
redundant per-job continuation count was removed; the single authoritative
root `continuation_calls_total` was present and `finalAnswerViolations` returned
an empty list. This replay is deterministic validation of the recorded live DSH
history, not a new model call.

Raw local evidence:

- `C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\dsh-job-receipt-v3`
- `C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\dsh-job-cancel`
- `C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\dsh-job-recovery-3`
- `C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\dsh-job-failure-v6`

The first two historical observations below are preserved because their races
and inaccurate prose motivated the deterministic job receipt. They are not the
accepted runs above.

## Historical pre-acceptance DSH observations

Both used halo-orchestrator and the unchanged
`lmstudio / halo/qwen3.6-35b-a3b`, actual installed MCP, public Python sources,
no account/paid calls. The observation scripts do not emit a semantic PASS.

| Observation | Session | Job | Actual outcome |
| --- | --- | --- | --- |
| Small | session-eaec2a84-e883-4640-93f0-5f4ee4bbc596 | baaaa7f8-5940-4499-8736-30339f056ea2 | complete; 3 attempts, 3 completed sources; 3.7180000000080327 active seconds |
| Standard | session-4135b51d-90a1-4591-9fad-ecadc3d6c3f7 | ad3ee3f9-3ea7-4cf8-b4c8-d99a765c1462 | complete; 13 attempts, 12 completed sources; 12.89100000000326 active seconds |

Small run: 7 calls; create, pause error, two complete statuses, resume error,
complete status and exact deep_research continuation. The two matching
checkpoints were terminal, not frozen paused checkpoints. Final answer disclosed
the race and partial warnings but incorrectly treated fragment counts as unique
source counts.

Standard run: 6 calls; create, status without job ID (error), pause error,
complete status, resume error, exact continuation. One status before pause
was emitted alongside create without the returned ID. The final answer disclosed
the race and same-document pagination, but misstated 12 completed sources as
12 attempted (actual attempts 13). Its TaskGroup example finding is supported
by returned page 2; this does not repair the lifecycle or count errors.

Both had progress.partial=true. Warnings included CROSS_SITE_LINK_SKIPPED,
DUPLICATE_URL_SKIPPED, PAGE_LIMIT_REACHED, PROVIDER_FALLBACK_USED,
RESULT_TRUNCATED and SOURCE_LIMIT_REACHED. The standard run also had
DUPLICATE_CONTENT_SKIPPED. Both read page 2 of the same cited document:
https://docs.python.org/3/library/asyncio-task.html
The warning set and continuation mean source coverage is not complete.

Both commands completed exit 0, which means capture/owned cleanup finished,
not that lifecycle assertions passed. No previous sessions were removed.
Both owned jobs were already terminal, so cleanup did not cancel them.

Exact commands, run from the Gateway repository:
```powershell
uv run --locked python 'C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\dsh-job-observation.py'
uv run --locked python 'C:\Users\scott\Documents\Codex\2026-09-01\is-this-tool-plugin-real-https\outputs\dsh-job-full-observation.py'
```

Raw local evidence is in those scripts' sibling folders `dsh-job` and
`dsh-job-full`, each with state.json, history.json and tool-results.json.
Preserve them, including the failures. No production timing change or increasingly
inflated workload is justified to manufacture a pause pass.

## Historical safe-error verification

Files read: Gateway AGENTS/scope, app tool wrapper and neighbors, service
error/job/status paths, job manager, existing job lifecycle/continuation tests,
native retention fixture, quality gate, README/changelog/manual/status.
Blast radius is the research_job MCP wrapper. Existing internal service errors
and state transitions are unchanged.

### Baseline

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_lifecycle.py tests/unit/test_job_continuation.py
```
```text
22 passed in 3.78s
```

### RED — actionable job codes missing

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_errors.py
```
```text
FFFFFF.                                                                  [100%]
================================== FAILURES ===================================
_ test_expected_job_failure_has_explicit_safe_mcp_code[missing-JOB_NOT_FOUND] _

app = <starlette.applications.Starlette object at 0x000001EEE204F770>
case = 'missing', code = 'JOB_NOT_FOUND'

    @pytest.mark.parametrize("case,code", [
        ("missing", "JOB_NOT_FOUND"),
        ("other_owner", "JOB_NOT_OWNED"),
        ("terminal", "JOB_STATE_CONFLICT"),
        ("limits", "INVALID_JOB_LIMITS"),
        ("capacity", "JOB_CAPACITY_REACHED"),
        ("empty", "INVALID_ARGUMENT"),
    ])
    async def test_expected_job_failure_has_explicit_safe_mcp_code(app, case, code):
        service = app.state.halo_service
        arguments = {"operation": "status", "job_id": "missing-fixture-job"}
        if case in {"other_owner", "terminal"}:
            job = service.jobs.create("other" if case == "other_owner" else "unidentified", "fixture", {})
            arguments["job_id"] = job["job_id"]
            if case == "terminal":
                service.jobs.transition(job["job_id"], "unidentified", "cancel")
                arguments["operation"] = "resume"
        elif case in {"limits", "capacity", "empty"}:
            arguments = {"operation": "create", "question": "fixture"}
            if case == "limits":
                arguments["limits"] = {"max_pages": 0}
            elif case == "capacity":
                service.config.jobs.max_active = 1
                service.jobs.create("unidentified", "occupied fixture", {})
            else:
                arguments["question"] = ""
        count_before = len(service.jobs.list())
        try:
            result = await call(app, arguments)
        except Exception:
            result = {"error": {"code": "GENERIC_MCP_EXCEPTION"}}
>       assert result.get("error", {}).get("code") == code, "Caller lost the actionable job failure code"
E       AssertionError: Caller lost the actionable job failure code
E       assert 'GENERIC_MCP_EXCEPTION' == 'JOB_NOT_FOUND'
E         
E         - JOB_NOT_FOUND
E         + GENERIC_MCP_EXCEPTION

tests\unit\test_job_errors.py:64: AssertionError
_ test_expected_job_failure_has_explicit_safe_mcp_code[other_owner-JOB_NOT_OWNED] _

app = <starlette.applications.Starlette object at 0x000001EEE18EDEE0>
case = 'other_owner', code = 'JOB_NOT_OWNED'

    @pytest.mark.parametrize("case,code", [
        ("missing", "JOB_NOT_FOUND"),
        ("other_owner", "JOB_NOT_OWNED"),
        ("terminal", "JOB_STATE_CONFLICT"),
        ("limits", "INVALID_JOB_LIMITS"),
        ("capacity", "JOB_CAPACITY_REACHED"),
        ("empty", "INVALID_ARGUMENT"),
    ])
    async def test_expected_job_failure_has_explicit_safe_mcp_code(app, case, code):
        service = app.state.halo_service
        arguments = {"operation": "status", "job_id": "missing-fixture-job"}
        if case in {"other_owner", "terminal"}:
            job = service.jobs.create("other" if case == "other_owner" else "unidentified", "fixture", {})
            arguments["job_id"] = job["job_id"]
            if case == "terminal":
                service.jobs.transition(job["job_id"], "unidentified", "cancel")
                arguments["operation"] = "resume"
        elif case in {"limits", "capacity", "empty"}:
            arguments = {"operation": "create", "question": "fixture"}
            if case == "limits":
                arguments["limits"] = {"max_pages": 0}
            elif case == "capacity":
                service.config.jobs.max_active = 1
                service.jobs.create("unidentified", "occupied fixture", {})
            else:
                arguments["question"] = ""
        count_before = len(service.jobs.list())
        try:
            result = await call(app, arguments)
        except Exception:
            result = {"error": {"code": "GENERIC_MCP_EXCEPTION"}}
>       assert result.get("error", {}).get("code") == code, "Caller lost the actionable job failure code"
E       AssertionError: Caller lost the actionable job failure code
E       assert 'GENERIC_MCP_EXCEPTION' == 'JOB_NOT_OWNED'
E         
E         - JOB_NOT_OWNED
E         + GENERIC_MCP_EXCEPTION

tests\unit\test_job_errors.py:64: AssertionError
_ test_expected_job_failure_has_explicit_safe_mcp_code[terminal-JOB_STATE_CONFLICT] _

app = <starlette.applications.Starlette object at 0x000001EEE216CFE0>
case = 'terminal', code = 'JOB_STATE_CONFLICT'

    @pytest.mark.parametrize("case,code", [
        ("missing", "JOB_NOT_FOUND"),
        ("other_owner", "JOB_NOT_OWNED"),
        ("terminal", "JOB_STATE_CONFLICT"),
        ("limits", "INVALID_JOB_LIMITS"),
        ("capacity", "JOB_CAPACITY_REACHED"),
        ("empty", "INVALID_ARGUMENT"),
    ])
    async def test_expected_job_failure_has_explicit_safe_mcp_code(app, case, code):
        service = app.state.halo_service
        arguments = {"operation": "status", "job_id": "missing-fixture-job"}
        if case in {"other_owner", "terminal"}:
            job = service.jobs.create("other" if case == "other_owner" else "unidentified", "fixture", {})
            arguments["job_id"] = job["job_id"]
            if case == "terminal":
                service.jobs.transition(job["job_id"], "unidentified", "cancel")
                arguments["operation"] = "resume"
        elif case in {"limits", "capacity", "empty"}:
            arguments = {"operation": "create", "question": "fixture"}
            if case == "limits":
                arguments["limits"] = {"max_pages": 0}
            elif case == "capacity":
                service.config.jobs.max_active = 1
                service.jobs.create("unidentified", "occupied fixture", {})
            else:
                arguments["question"] = ""
        count_before = len(service.jobs.list())
        try:
            result = await call(app, arguments)
        except Exception:
            result = {"error": {"code": "GENERIC_MCP_EXCEPTION"}}
>       assert result.get("error", {}).get("code") == code, "Caller lost the actionable job failure code"
E       AssertionError: Caller lost the actionable job failure code
E       assert 'GENERIC_MCP_EXCEPTION' == 'JOB_STATE_CONFLICT'
E         
E         - JOB_STATE_CONFLICT
E         + GENERIC_MCP_EXCEPTION

tests\unit\test_job_errors.py:64: AssertionError
_ test_expected_job_failure_has_explicit_safe_mcp_code[limits-INVALID_JOB_LIMITS] _

app = <starlette.applications.Starlette object at 0x000001EEE216C8F0>
case = 'limits', code = 'INVALID_JOB_LIMITS'

    @pytest.mark.parametrize("case,code", [
        ("missing", "JOB_NOT_FOUND"),
        ("other_owner", "JOB_NOT_OWNED"),
        ("terminal", "JOB_STATE_CONFLICT"),
        ("limits", "INVALID_JOB_LIMITS"),
        ("capacity", "JOB_CAPACITY_REACHED"),
        ("empty", "INVALID_ARGUMENT"),
    ])
    async def test_expected_job_failure_has_explicit_safe_mcp_code(app, case, code):
        service = app.state.halo_service
        arguments = {"operation": "status", "job_id": "missing-fixture-job"}
        if case in {"other_owner", "terminal"}:
            job = service.jobs.create("other" if case == "other_owner" else "unidentified", "fixture", {})
            arguments["job_id"] = job["job_id"]
            if case == "terminal":
                service.jobs.transition(job["job_id"], "unidentified", "cancel")
                arguments["operation"] = "resume"
        elif case in {"limits", "capacity", "empty"}:
            arguments = {"operation": "create", "question": "fixture"}
            if case == "limits":
                arguments["limits"] = {"max_pages": 0}
            elif case == "capacity":
                service.config.jobs.max_active = 1
                service.jobs.create("unidentified", "occupied fixture", {})
            else:
                arguments["question"] = ""
        count_before = len(service.jobs.list())
        try:
            result = await call(app, arguments)
        except Exception:
            result = {"error": {"code": "GENERIC_MCP_EXCEPTION"}}
>       assert result.get("error", {}).get("code") == code, "Caller lost the actionable job failure code"
E       AssertionError: Caller lost the actionable job failure code
E       assert 'GENERIC_MCP_EXCEPTION' == 'INVALID_JOB_LIMITS'
E         
E         - INVALID_JOB_LIMITS
E         + GENERIC_MCP_EXCEPTION

tests\unit\test_job_errors.py:64: AssertionError
_ test_expected_job_failure_has_explicit_safe_mcp_code[capacity-JOB_CAPACITY_REACHED] _

app = <starlette.applications.Starlette object at 0x000001EEE2290500>
case = 'capacity', code = 'JOB_CAPACITY_REACHED'

    @pytest.mark.parametrize("case,code", [
        ("missing", "JOB_NOT_FOUND"),
        ("other_owner", "JOB_NOT_OWNED"),
        ("terminal", "JOB_STATE_CONFLICT"),
        ("limits", "INVALID_JOB_LIMITS"),
        ("capacity", "JOB_CAPACITY_REACHED"),
        ("empty", "INVALID_ARGUMENT"),
    ])
    async def test_expected_job_failure_has_explicit_safe_mcp_code(app, case, code):
        service = app.state.halo_service
        arguments = {"operation": "status", "job_id": "missing-fixture-job"}
        if case in {"other_owner", "terminal"}:
            job = service.jobs.create("other" if case == "other_owner" else "unidentified", "fixture", {})
            arguments["job_id"] = job["job_id"]
            if case == "terminal":
                service.jobs.transition(job["job_id"], "unidentified", "cancel")
                arguments["operation"] = "resume"
        elif case in {"limits", "capacity", "empty"}:
            arguments = {"operation": "create", "question": "fixture"}
            if case == "limits":
                arguments["limits"] = {"max_pages": 0}
            elif case == "capacity":
                service.config.jobs.max_active = 1
                service.jobs.create("unidentified", "occupied fixture", {})
            else:
                arguments["question"] = ""
        count_before = len(service.jobs.list())
        try:
            result = await call(app, arguments)
        except Exception:
            result = {"error": {"code": "GENERIC_MCP_EXCEPTION"}}
>       assert result.get("error", {}).get("code") == code, "Caller lost the actionable job failure code"
E       AssertionError: Caller lost the actionable job failure code
E       assert 'GENERIC_MCP_EXCEPTION' == 'JOB_CAPACITY_REACHED'
E         
E         - JOB_CAPACITY_REACHED
E         + GENERIC_MCP_EXCEPTION

tests\unit\test_job_errors.py:64: AssertionError
_ test_expected_job_failure_has_explicit_safe_mcp_code[empty-INVALID_ARGUMENT] _

app = <starlette.applications.Starlette object at 0x000001EEE2313C50>
case = 'empty', code = 'INVALID_ARGUMENT'

    @pytest.mark.parametrize("case,code", [
        ("missing", "JOB_NOT_FOUND"),
        ("other_owner", "JOB_NOT_OWNED"),
        ("terminal", "JOB_STATE_CONFLICT"),
        ("limits", "INVALID_JOB_LIMITS"),
        ("capacity", "JOB_CAPACITY_REACHED"),
        ("empty", "INVALID_ARGUMENT"),
    ])
    async def test_expected_job_failure_has_explicit_safe_mcp_code(app, case, code):
        service = app.state.halo_service
        arguments = {"operation": "status", "job_id": "missing-fixture-job"}
        if case in {"other_owner", "terminal"}:
            job = service.jobs.create("other" if case == "other_owner" else "unidentified", "fixture", {})
            arguments["job_id"] = job["job_id"]
            if case == "terminal":
                service.jobs.transition(job["job_id"], "unidentified", "cancel")
                arguments["operation"] = "resume"
        elif case in {"limits", "capacity", "empty"}:
            arguments = {"operation": "create", "question": "fixture"}
            if case == "limits":
                arguments["limits"] = {"max_pages": 0}
            elif case == "capacity":
                service.config.jobs.max_active = 1
                service.jobs.create("unidentified", "occupied fixture", {})
            else:
                arguments["question"] = ""
        count_before = len(service.jobs.list())
        try:
            result = await call(app, arguments)
        except Exception:
            result = {"error": {"code": "GENERIC_MCP_EXCEPTION"}}
>       assert result.get("error", {}).get("code") == code, "Caller lost the actionable job failure code"
E       AssertionError: Caller lost the actionable job failure code
E       assert 'GENERIC_MCP_EXCEPTION' == 'INVALID_ARGUMENT'
E         
E         - INVALID_ARGUMENT
E         + GENERIC_MCP_EXCEPTION

tests\unit\test_job_errors.py:64: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_job_errors.py::test_expected_job_failure_has_explicit_safe_mcp_code[missing-JOB_NOT_FOUND]
FAILED tests/unit/test_job_errors.py::test_expected_job_failure_has_explicit_safe_mcp_code[other_owner-JOB_NOT_OWNED]
FAILED tests/unit/test_job_errors.py::test_expected_job_failure_has_explicit_safe_mcp_code[terminal-JOB_STATE_CONFLICT]
FAILED tests/unit/test_job_errors.py::test_expected_job_failure_has_explicit_safe_mcp_code[limits-INVALID_JOB_LIMITS]
FAILED tests/unit/test_job_errors.py::test_expected_job_failure_has_explicit_safe_mcp_code[capacity-JOB_CAPACITY_REACHED]
FAILED tests/unit/test_job_errors.py::test_expected_job_failure_has_explicit_safe_mcp_code[empty-INVALID_ARGUMENT]
6 failed, 1 passed in 1.47s
```

### GREEN — focused module and existing lifecycle tests

```powershell
uv run --locked ruff format tests/unit/test_job_errors.py src/halo_research_gateway/app.py
uv run --locked python -m pytest -q tests/unit/test_job_errors.py tests/unit/test_job_lifecycle.py tests/unit/test_job_continuation.py
```
```text
1 file reformatted, 1 file left unchanged
29 passed in 4.37s
```

### First widened gate — test lint failure, not a product regression

The assertion initially expected any Exception. It now requires the SDK's
UnexpectedToolError and verifies synthetic sensitive text is absent.
No existing test was weakened.

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```
```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
111 files already formatted
[GATE] lint
B017 Do not assert blind exception: `Exception`
  --> tests\unit\test_job_errors.py:79:10
   |
78 |     app.state.halo_service.research_job = unexpected
79 |     with pytest.raises(Exception):
   |          ^^^^^^^^^^^^^^^^^^^^^^^^
80 |         await call(app, {"operation": "status", "job_id": "fixture"})
   |

Found 1 error.
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | lint failed with exit code 1
```

### Stricter assertion and complete gate

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_errors.py
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```
```text
7 passed in 1.21s
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
111 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
497 passed in 77.56s (0:01:17)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)
```

### Native MCP — first fixture schema mistake and correction

The first run successfully checked four actual MCP error responses but its
final no-job assertion assumed a nonexistent jobs.total statistic.
Corrected to sum the existing per-state counts; product code unchanged.
This first native failure is not a valid RED reproduction of the product bug.

```powershell
uv run --locked ruff format tests/acceptance/test_job_errors_native.py
uv run --locked python -m pytest -q tests/acceptance/test_job_errors_native.py
```
```text
1 file left unchanged
F                                                                        [100%]
================================== FAILURES ===================================
____ test_native_job_control_errors_are_actionable_and_do_not_create_jobs _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-2192/test_native_job_control_errors0')

    async def test_native_job_control_errors_are_actionable_and_do_not_create_jobs(tmp_path):
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        assert port != 8765
        root = tmp_path.as_posix()
        config = tmp_path / "config.toml"
        config.write_text(
            f"[server]\nport={port}\nlog_level='ERROR'\n"
            f"[storage]\ndatabase='{root}/state/gateway.db'\n"
            f"backup_directory='{root}/backups'\ncontent_directory='{root}/content'\n"
            f"[crawl]\nbase_directory='{root}/browser'\n",
            encoding="utf-8",
        )
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-m",
            "halo_research_gateway",
            env=dict(os.environ, HALO_RESEARCH_CONFIG=str(config), LOCALAPPDATA=str(tmp_path)),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
        )
        output = asyncio.create_task(process.communicate())
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=1) as http:
                async with asyncio.timeout(20):
                    while True:
                        if process.returncode is not None:
                            raise AssertionError((await output)[0].decode(errors="replace"))
                        try:
                            health = await http.get(f"http://127.0.0.1:{port}/health")
                            if health.status_code == 200 and health.json()["status"] == "ok":
                                break
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.05)
            async with httpx.AsyncClient(trust_env=False, timeout=15) as http:
                async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
                    async with ClientSession(streams[0], streams[1]) as client:
                        await client.initialize()
                        assert len((await client.list_tools()).tools) == 14
                        for arguments, code in [
                            ({"operation": "status", "job_id": "missing-fixture"}, "JOB_NOT_FOUND"),
                            ({"operation": "status"}, "JOB_NOT_FOUND"),
                            ({"operation": "create", "question": ""}, "INVALID_ARGUMENT"),
                            (
                                {"operation": "create", "question": "fixture", "limits": {"max_pages": 0}},
                                "INVALID_JOB_LIMITS",
                            ),
                        ]:
                            reply = await client.call_tool("research_job", arguments)
                            wire = "\n".join(block.text for block in reply.content if hasattr(block, "text"))
                            payload = json.loads(wire)
                            assert not reply.is_error, wire
                            assert payload["ok"] is False and payload["items"] == [], wire
                            assert payload["error"]["code"] == code, wire
                            assert "fixture" not in wire and len(wire) < 2000
                stats = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
>               assert stats["jobs"]["total"] == 0
                       ^^^^^^^^^^^^^^^^^^^^^^
E               KeyError: 'total'

tests\acceptance\test_job_errors_native.py:74: KeyError
=========================== short test summary info ===========================
FAILED tests/acceptance/test_job_errors_native.py::test_native_job_control_errors_are_actionable_and_do_not_create_jobs
1 failed in 2.92s
```

```powershell
uv run --locked python -m pytest -q tests/acceptance/test_job_errors_native.py
```
```text
.                                                                        [100%]
1 passed in 2.04s
```

Native fixture: disposable state and loopback port, no installed restart,
no upstream/provider call, fourteen tools, four explicit bounded error replies,
zero jobs created, synthetic job ID absent from replies/captured process output,
exact owned process terminated. Unit falsification additionally covers another
owner, terminal resume, capacity and unknown-error sanitization.

## Current receipt and lifecycle verification

Focused job suite:

```powershell
uv run --locked python -m pytest -q tests/unit/test_job_lifecycle.py tests/unit/test_job_continuation.py tests/unit/test_job_errors.py tests/unit/test_job_bounds.py
```

```text
43 passed in 7.37s
```

Full repository gate after synchronizing the bundled scope copy:

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

```text
597 passed in 121.04s
12 DSH adapter tests passed
halo-research skill package valid
[GATE] PASS (Full)
```

Landing-page source:

```powershell
cd website
npm run lint
npm run build
```

Both commands passed; vinext built all five environments and the `/` route.

The final v6 failure history was replayed through the v7 code by mapping its
durable event wrappers to DSH events, building the current job receipt and
running `finalAnswerViolations`. Result:

```json
{
  "canonical_present": true,
  "continuation_calls_total": 1,
  "violations": []
}
```

The first full-gate attempt had 597 Python and 12 DSH tests green but failed the
skill-package check because the governing scope had changed without its bundled
copy. The copy was synchronized byte-for-byte and the complete gate above was
rerun; the initial failure is not reported as a pass.

## Security and unfinished work

Historical safe-error documentation gate: its first run failed because the
repository-bundled scope copy had not been synchronized with the then-amended
finish list. Both repository copies were corrected. This did not touch the
three denied installed host references. The current 597-test gate is recorded
above and supersedes this older count.

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```
```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
112 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
497 passed in 80.20s (0:01:20)
[GATE] skill package
skill-bundled research-only scope differs from current contract
Exception: C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Invoke-QualityGate.ps1:9
Line |
   9 |  … EXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
     |                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
     | skill package failed with exit code 1
```

The subsequent historical commit/reload receipt recorded that corrected older
gate and exact commit. It is not evidence for the current pending source commit.

- Trust-boundary input: existing MCP schema and service validation retained;
  only exact known string codes leave the exception boundary.
- Endpoint/auth: no endpoint or authorization change. Client labels remain
  configured scheduling/ownership buckets, not a new authentication claim.
- Secrets: returned errors omit raw exception/request detail. No credential or
  personal source was used. This is not universal source/log secret detection.
- Rendering/eval/deserialization: no new rendering, eval or unsafe decoding.
- Dependencies: none added or changed; new-dependency vulnerability review N/A.
- Scope: safe expected job errors and the installed DSH lifecycle scenarios
  above are implemented and verified; complete project acceptance is not.
  Broader long-running/provider stress, forced cancellation of an already-
  running synchronous DDGS request, and unrelated clean-OS/logon acceptance
  remain open. Arbitrary job field/status-output bounds are not expanded by
  this change. See RESEARCH-ONLY-SCOPE.md for the full finish list.
