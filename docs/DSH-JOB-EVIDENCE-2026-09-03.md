# DSH research jobs and safe errors — 2026-09-03

## Result and scope

The two live DSH jobs found public evidence and followed exact retained cursors,
but both completed before their pause requests arrived. Neither is a DSH
pause/frozen-checkpoint/resume pass. A completed model turn is not acceptance.

Those runs exposed generic MCP job errors. The source repair translates only
six established control failures into the existing error envelope:
JOB_NOT_FOUND, JOB_NOT_OWNED, JOB_STATE_CONFLICT, INVALID_JOB_LIMITS,
JOB_CAPACITY_REACHED and INVALID_ARGUMENT. Replies contain ok=false, empty
items and a safe code; unknown exceptions still use SDK sanitization.
No job state machine, ownership mapping, model, preset, permission, connection,
browser profile, dependency, schema or tool-count change was made.

Base/source and installed revision during DSH observations:
`3a01a996c786800bf879d2f26c56ba3140502421`, product 0.2.0.
The new error behavior is source/native proof here; installation needs a
separate reload receipt. Final 0.3.0 is not released or tagged by this record.

## Real DSH observations

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

## Verification

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

## Security and unfinished work

Final documentation gate initially failed because the repository-bundled scope
copy had not been synchronized with the amended finish list. Both repository
copies now match. This did not touch the three denied installed host references.

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

The subsequent commit/reload receipt records the corrected final gate and exact
commit; this source report does not claim a pending run passed.

- Trust-boundary input: existing MCP schema and service validation retained;
  only exact known string codes leave the exception boundary.
- Endpoint/auth: no endpoint or authorization change. Client labels remain
  configured scheduling/ownership buckets, not a new authentication claim.
- Secrets: returned errors omit raw exception/request detail. No credential or
  personal source was used. This is not universal source/log secret detection.
- Rendering/eval/deserialization: no new rendering, eval or unsafe decoding.
- Dependencies: none added or changed; new-dependency vulnerability review N/A.
- Scope: safe expected job errors are implemented; complete project acceptance
  is not. DSH pause/resume, long-running/provider cancellation and strict final
  answer compliance remain open. Arbitrary job field/status-output bounds are
  not repaired by this change. See RESEARCH-ONLY-SCOPE.md for the full finish list.
