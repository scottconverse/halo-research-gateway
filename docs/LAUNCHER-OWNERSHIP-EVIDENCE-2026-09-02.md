# Background launcher ownership evidence — 2026-09-02

## Outcome and scope

The background Windows launcher now serializes start/stop, validates repository,
executable, exact module command and process creation time, and holds the validated
process handle through stop. Readiness checks the configured port/health path and
listener ancestry. Failed newly-created instances are cleaned up; existing
mismatched/unhealthy instances remain untouched. PID records are atomically written.
No dependency, account action, MCP tool or DSH capability was added or removed.

Read before editing: repository AGENTS/scope, QA skill, Start/Stop scripts,
configuration/entry point, Windows Job Object helper, quality gate and affected
README/manual/status records. The clean source checkpoint was e722d3d; the sole
initial untracked file was the incomplete launcher regression fixture.

The first four stop tests falsely passed because PowerShell script-scoped fixture
variables resolved in the invoked script, not the wrapper. Changed only fixture
variables to uniquely named globals; all twenty original cases then failed on
assertions. That initial false pass is not evidence. A null listener returned as
an array element caused the first implementation to fail two concurrency cases;
filtering null results restored the intended empty-listener semantics. Cleanup
RED was recaptured only after that interference was removed.

Forty-four fixture cases cover both Windows PowerShell and PowerShell 7, exact
identity, PID reuse, look-alike commands, foreign repository/executable/listeners,
configured port/health, concurrent launches, failed new starts, stale records,
CIM/stop access errors, unknown schema and 100ns timestamp precision. Legacy
records permit only a one-sided two-second post-creation timestamp window; schema
2 records require exact time. This is accidental/reused-PID protection, not a
security boundary against another process running as Scott.

Two separate native acceptance cases use the real scripts and Gateway on an
unused loopback port, temporary configuration/storage and no accounts/providers.
They prove one instance after concurrent starts, healthy reuse, stop/listener
closure, restart, and preservation of a separately owned dummy process.
No Chrome was launched by this fixture. Temporary state is left to pytest's normal
retention. Only test-created processes and their own PID records were stopped.

Production health was rechecked: status ok, version 0.2.0, unchanged started_at
2026-09-03T00:36:16.942206Z. Production Gateway, DSH, LM Studio and Mission Control
were not restarted or reconfigured for this checkpoint. No host credentials or
private profiles were accessed. The prior DSH prepare-error diagnosis/approval
request is not a fresh DSH run and remains separate from this evidence.

## Known limits and sign-off

This closes background-launcher ownership only, not the overall finish goal.
Foreground diagnostic mode remains non-PID-managed; its lifecycle mutex is
released before the foreground process runs. Foreground concurrency, at-logon,
clean installation, strict wall-clock startup bounds, browser-tree shutdown and
broad stress still need work. Readiness remains at most 30 attempts with 500ms
spacing and two-second HTTP timeouts, not a strict 15-second guarantee.
Legacy PID-record compatibility is intentionally less exact than schema 2.
No production restart was needed: only launcher scripts changed, not service Python.

Security review: PID, repository, executable, command, time and listener ownership
validated; no route/auth change; no secret fields or credential reads added; no
eval or unsafe deserialization added (existing JSON parsing retained); no new
dependency, so new-dependency vulnerability review is not applicable. Repository
credential-pattern scan and commit/CI identities are recorded at delivery, not
inferred from this local test gate. Private checkpoint only; no new version/tag
or public package, and no licensing decision.

README, changelog, user manual, scope/finish list, progress and implementation
status are updated. Operator/recovery copies are synchronized at delivery.

## Verification log

All commands ran from C:\Users\scott\Desktop\Code\halo-research-gateway.
Full captured summaries/failures follow. Pytest itself abbreviates some Python
reprs in assertion diagnostics; no tool-output truncation is substituted for them.

### Baseline

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
80 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 39%]
........................................................................ [ 78%]
.......................................                                  [100%]
183 passed in 14.79s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

### Assertion RED against original start/stop scripts

```powershell
uv run --locked python -m pytest -q tests/unit/test_launcher_ownership.py
```

```text
FFFFFFFFFFFFFFFFFFFF                                                     [100%]
================================== FAILURES ===================================
_ test_stop_refuses_unowned_process_and_preserves_record[reused_pid-powershell.exe] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_refuses_unowned_proc0')
shell = 'powershell.exe', case = 'reused_pid'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
    def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway stopped.
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\...stop_refuses_unowned_proc0\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway stopped.\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:149: AssertionError
_ test_stop_refuses_unowned_process_and_preserves_record[reused_pid-pwsh.exe] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_refuses_unowned_proc1')
shell = 'pwsh.exe', case = 'reused_pid'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
    def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway stopped.
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['pwsh.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\...stop_refuses_unowned_proc1\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway stopped.\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:149: AssertionError
_ test_stop_refuses_unowned_process_and_preserves_record[lookalike-powershell.exe] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_refuses_unowned_proc2')
shell = 'powershell.exe', case = 'lookalike'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
    def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway stopped.
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\...stop_refuses_unowned_proc2\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway stopped.\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:149: AssertionError
_ test_stop_refuses_unowned_process_and_preserves_record[lookalike-pwsh.exe] __

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_refuses_unowned_proc3')
shell = 'pwsh.exe', case = 'lookalike'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
    def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway stopped.
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['pwsh.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\...stop_refuses_unowned_proc3\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway stopped.\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:149: AssertionError
_ test_stop_refuses_unowned_process_and_preserves_record[foreign_executable-powershell.exe] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_refuses_unowned_proc4')
shell = 'powershell.exe', case = 'foreign_executable'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
    def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway stopped.
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\...stop_refuses_unowned_proc4\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway stopped.\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:149: AssertionError
_ test_stop_refuses_unowned_process_and_preserves_record[foreign_executable-pwsh.exe] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_refuses_unowned_proc5')
shell = 'pwsh.exe', case = 'foreign_executable'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
    def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway stopped.
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['pwsh.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\...stop_refuses_unowned_proc5\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway stopped.\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:149: AssertionError
_ test_stop_refuses_unowned_process_and_preserves_record[wrong_repository-powershell.exe] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_refuses_unowned_proc6')
shell = 'powershell.exe', case = 'wrong_repository'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
    def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway stopped.
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\...stop_refuses_unowned_proc6\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway stopped.\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:149: AssertionError
_ test_stop_refuses_unowned_process_and_preserves_record[wrong_repository-pwsh.exe] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_refuses_unowned_proc7')
shell = 'pwsh.exe', case = 'wrong_repository'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
    def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway stopped.
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['pwsh.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\...stop_refuses_unowned_proc7\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway stopped.\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:149: AssertionError
__ test_start_refuses_false_already_running_claim[reused_pid-powershell.exe] __

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_start_refuses_false_alrea0')
shell = 'powershell.exe', case = 'reused_pid'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
    def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway already running (PID 1234500).
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\...rea0\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway already running (PID 1234500).\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:159: AssertionError
_____ test_start_refuses_false_already_running_claim[reused_pid-pwsh.exe] _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_start_refuses_false_alrea1')
shell = 'pwsh.exe', case = 'reused_pid'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
    def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway already running (PID 1234500).
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['pwsh.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\...rea1\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway already running (PID 1234500).\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:159: AssertionError
__ test_start_refuses_false_already_running_claim[lookalike-powershell.exe] ___

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_start_refuses_false_alrea2')
shell = 'powershell.exe', case = 'lookalike'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
    def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway already running (PID 1234500).
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\...rea2\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway already running (PID 1234500).\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:159: AssertionError
_____ test_start_refuses_false_already_running_claim[lookalike-pwsh.exe] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_start_refuses_false_alrea3')
shell = 'pwsh.exe', case = 'lookalike'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
    def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway already running (PID 1234500).
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['pwsh.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\...rea3\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway already running (PID 1234500).\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:159: AssertionError
_ test_start_refuses_false_already_running_claim[wrong_repository-powershell.exe] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_start_refuses_false_alrea4')
shell = 'powershell.exe', case = 'wrong_repository'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
    def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway already running (PID 1234500).
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\...rea4\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway already running (PID 1234500).\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:159: AssertionError
__ test_start_refuses_false_already_running_claim[wrong_repository-pwsh.exe] __

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_start_refuses_false_alrea5')
shell = 'pwsh.exe', case = 'wrong_repository'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
    def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway already running (PID 1234500).
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['pwsh.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\...rea5\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway already running (PID 1234500).\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:159: AssertionError
__ test_start_refuses_false_already_running_claim[unhealthy-powershell.exe] ___

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_start_refuses_false_alrea6')
shell = 'powershell.exe', case = 'unhealthy'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
    def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway already running (PID 1234500).
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\...rea6\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway already running (PID 1234500).\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:159: AssertionError
_____ test_start_refuses_false_already_running_claim[unhealthy-pwsh.exe] ______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_start_refuses_false_alrea7')
shell = 'pwsh.exe', case = 'unhealthy'

    @pytest.mark.parametrize("shell", SHELLS)
    @pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
    def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
        wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
>       assert result.returncode != 0, result.stdout + result.stderr
E       AssertionError: Halo Research Gateway already running (PID 1234500).
E         
E       assert 0 != 0
E        +  where 0 = CompletedProcess(args=['pwsh.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', 'C:\\Users\...rea7\\launcher-fixture.ps1'], returncode=0, stdout='Halo Research Gateway already running (PID 1234500).\n', stderr='').returncode

tests\unit\test_launcher_ownership.py:159: AssertionError
____ test_stop_uses_held_process_object_for_valid_identity[powershell.exe] ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_uses_held_process_ob0')
shell = 'powershell.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_stop_uses_held_process_object_for_valid_identity(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "valid", "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
        assert result.returncode == 0, result.stdout + result.stderr
        stopped = json.loads((tmp_path / "trace" / "stopped.json").read_text(encoding="utf-8-sig"))
>       assert stopped["held_object"], "stop must retain the validated process handle, not look up PID again"
E       AssertionError: stop must retain the validated process handle, not look up PID again
E       assert False

tests\unit\test_launcher_ownership.py:171: AssertionError
_______ test_stop_uses_held_process_object_for_valid_identity[pwsh.exe] _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_stop_uses_held_process_ob1')
shell = 'pwsh.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_stop_uses_held_process_object_for_valid_identity(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "valid", "Stop-HaloResearch.ps1")
        result = invoke(shell, wrapper, env)
        assert result.returncode == 0, result.stdout + result.stderr
        stopped = json.loads((tmp_path / "trace" / "stopped.json").read_text(encoding="utf-8-sig"))
>       assert stopped["held_object"], "stop must retain the validated process handle, not look up PID again"
E       AssertionError: stop must retain the validated process handle, not look up PID again
E       assert False

tests\unit\test_launcher_ownership.py:171: AssertionError
_______ test_concurrent_starts_launch_only_one_process[powershell.exe] ________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_concurrent_starts_launch_0')
shell = 'powershell.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_concurrent_starts_launch_only_one_process(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "concurrent", "Start-HaloResearch.ps1", record=False)
        command = [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(wrapper)]
        processes = [subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        try:
            outputs = [process.communicate(timeout=35) for process in processes]
>           assert all(process.returncode == 0 for process in processes), outputs
E           AssertionError: [('Halo Research Gateway ok (PID 30100).
E             ', ''), ('', 'Set-Content : Stream was not readable.
E             At C:\\Users\\scott\\D...on
E                 + FullyQualifiedErrorId : GetContentWriterArgumentError,Microsoft.PowerShell.Commands.SetContentCommand
E              
E             ')]
E           assert False
E            +  where False = all(<generator object test_concurrent_starts_launch_only_one_process.<locals>.<genexpr> at 0x0000020832FE5BE0>)

tests\unit\test_launcher_ownership.py:182: AssertionError
__________ test_concurrent_starts_launch_only_one_process[pwsh.exe] ___________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_concurrent_starts_launch_1')
shell = 'pwsh.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_concurrent_starts_launch_only_one_process(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "concurrent", "Start-HaloResearch.ps1", record=False)
        command = [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(wrapper)]
        processes = [subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        try:
            outputs = [process.communicate(timeout=35) for process in processes]
            assert all(process.returncode == 0 for process in processes), outputs
>           assert len(list((tmp_path / "trace").glob("started-*"))) == 1, "concurrent launch duplicated the provider"
E           AssertionError: concurrent launch duplicated the provider
E           assert 2 == 1
E            +  where 2 = len([WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_concurrent_starts_launch_1/trace/star...h('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_concurrent_starts_launch_1/trace/started-44996')])
E            +    where [WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_concurrent_starts_launch_1/trace/star...h('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_concurrent_starts_launch_1/trace/started-44996')] = list(<generator object Path.glob at 0x0000020832F32240>)
E            +      where <generator object Path.glob at 0x0000020832F32240> = glob('started-*')
E            +        where glob = (WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1922/test_concurrent_starts_launch_1') / 'trace').glob

tests\unit\test_launcher_ownership.py:183: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_launcher_ownership.py::test_stop_refuses_unowned_process_and_preserves_record[reused_pid-powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_refuses_unowned_process_and_preserves_record[reused_pid-pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_refuses_unowned_process_and_preserves_record[lookalike-powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_refuses_unowned_process_and_preserves_record[lookalike-pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_refuses_unowned_process_and_preserves_record[foreign_executable-powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_refuses_unowned_process_and_preserves_record[foreign_executable-pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_refuses_unowned_process_and_preserves_record[wrong_repository-powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_refuses_unowned_process_and_preserves_record[wrong_repository-pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_refuses_false_already_running_claim[reused_pid-powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_refuses_false_already_running_claim[reused_pid-pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_refuses_false_already_running_claim[lookalike-powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_refuses_false_already_running_claim[lookalike-pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_refuses_false_already_running_claim[wrong_repository-powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_refuses_false_already_running_claim[wrong_repository-pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_refuses_false_already_running_claim[unhealthy-powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_refuses_false_already_running_claim[unhealthy-pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_uses_held_process_object_for_valid_identity[powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_stop_uses_held_process_object_for_valid_identity[pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_concurrent_starts_launch_only_one_process[powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_concurrent_starts_launch_only_one_process[pwsh.exe]
20 failed in 10.88s
```

### Stop-only GREEN

```powershell
uv run --locked python -m pytest -q tests/unit/test_launcher_ownership.py -k stop
```

```text
..........                                                               [100%]
10 passed, 10 deselected in 5.16s
```

### Intermediate start implementation, not GREEN

```powershell
uv run --locked python -m pytest -q tests/unit/test_launcher_ownership.py
```

```text
..................FF                                                     [100%]
================================== FAILURES ===================================
_______ test_concurrent_starts_launch_only_one_process[powershell.exe] ________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1924/test_concurrent_starts_launch_0')
shell = 'powershell.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_concurrent_starts_launch_only_one_process(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "concurrent", "Start-HaloResearch.ps1", record=False)
        command = [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(wrapper)]
        processes = [subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        try:
            outputs = [process.communicate(timeout=35) for process in processes]
>           assert all(process.returncode == 0 for process in processes), outputs
E           AssertionError: [('', 'Port 8765 is already owned by PID .
E             At C:\\Users\\scott\\Desktop\\Code\\halo-research-gateway\\scripts\\Start-... owned by PID .:String) [], RuntimeException
E                 + FullyQualifiedErrorId : Port 8765 is already owned by PID .
E              
E             ')]
E           assert False
E            +  where False = all(<generator object test_concurrent_starts_launch_only_one_process.<locals>.<genexpr> at 0x0000027ABF0BCE10>)

tests\unit\test_launcher_ownership.py:182: AssertionError
__________ test_concurrent_starts_launch_only_one_process[pwsh.exe] ___________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1924/test_concurrent_starts_launch_1')
shell = 'pwsh.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_concurrent_starts_launch_only_one_process(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "concurrent", "Start-HaloResearch.ps1", record=False)
        command = [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(wrapper)]
        processes = [subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
        try:
            outputs = [process.communicate(timeout=35) for process in processes]
>           assert all(process.returncode == 0 for process in processes), outputs
E           AssertionError: [('', 'Exception: C:\\Users\\scott\\Desktop\\Code\\halo-research-gateway\\scripts\\Start-HaloResearch.ps1:21
E             Line |
E             ...             ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
E                  | Port 8765 is already owned by PID .
E             ')]
E           assert False
E            +  where False = all(<generator object test_concurrent_starts_launch_only_one_process.<locals>.<genexpr> at 0x0000027ABF0BDA40>)

tests\unit\test_launcher_ownership.py:182: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_launcher_ownership.py::test_concurrent_starts_launch_only_one_process[powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_concurrent_starts_launch_only_one_process[pwsh.exe]
2 failed, 18 passed in 12.18s
```

### Configured-port RED; cleanup fixture not yet reaching intended assertion

```powershell
uv run --locked python -m pytest -q tests/unit/test_launcher_ownership.py -k 'configured_listener or failed_new_start'
```

```text
FFFF                                                                     [100%]
================================== FAILURES ===================================
____ test_start_checks_configured_listener_and_health_path[powershell.exe] ____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1925/test_start_checks_configured_l0')
shell = 'powershell.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_start_checks_configured_listener_and_health_path(tmp_path, shell):
        wrapper, env, _ = fixture(tmp_path, "valid", "Start-HaloResearch.ps1")
        (tmp_path / "config.toml").write_text(
            '[server]\nport = 18765\nhealth_path = "/alive"\n', encoding="utf-8"
        )
        result = invoke(shell, wrapper, env)
        assert result.returncode == 0, result.stdout + result.stderr
>       assert (tmp_path / "trace" / "port.txt").read_text(encoding="utf-8-sig").strip() == "18765"
E       AssertionError: assert '8765' == '18765'
E         
E         - 18765
E         ? -
E         + 8765

tests\unit\test_launcher_ownership.py:202: AssertionError
_______ test_start_checks_configured_listener_and_health_path[pwsh.exe] _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1925/test_start_checks_configured_l1')
shell = 'pwsh.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_start_checks_configured_listener_and_health_path(tmp_path, shell):
        wrapper, env, _ = fixture(tmp_path, "valid", "Start-HaloResearch.ps1")
        (tmp_path / "config.toml").write_text(
            '[server]\nport = 18765\nhealth_path = "/alive"\n', encoding="utf-8"
        )
        result = invoke(shell, wrapper, env)
        assert result.returncode == 0, result.stdout + result.stderr
>       assert (tmp_path / "trace" / "port.txt").read_text(encoding="utf-8-sig").strip() == "18765"
E       AssertionError: assert '8765' == '18765'
E         
E         - 18765
E         ? -
E         + 8765

tests\unit\test_launcher_ownership.py:202: AssertionError
_______ test_failed_new_start_cleans_its_own_pid_record[powershell.exe] _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1925/test_failed_new_start_cleans_i0')
shell = 'powershell.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_failed_new_start_cleans_its_own_pid_record(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "exited", "Start-HaloResearch.ps1", record=False)
        result = invoke(shell, wrapper, env)
        assert result.returncode != 0, result.stdout + result.stderr
>       assert len(list((tmp_path / "trace").glob("started-*"))) == 1
E       AssertionError: assert 0 == 1
E        +  where 0 = len([])
E        +    where [] = list(<generator object Path.glob at 0x0000010967C21470>)
E        +      where <generator object Path.glob at 0x0000010967C21470> = glob('started-*')
E        +        where glob = (WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1925/test_failed_new_start_cleans_i0') / 'trace').glob

tests\unit\test_launcher_ownership.py:211: AssertionError
__________ test_failed_new_start_cleans_its_own_pid_record[pwsh.exe] __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1925/test_failed_new_start_cleans_i1')
shell = 'pwsh.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_failed_new_start_cleans_its_own_pid_record(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "exited", "Start-HaloResearch.ps1", record=False)
        result = invoke(shell, wrapper, env)
        assert result.returncode != 0, result.stdout + result.stderr
>       assert len(list((tmp_path / "trace").glob("started-*"))) == 1
E       AssertionError: assert 0 == 1
E        +  where 0 = len([])
E        +    where [] = list(<generator object Path.glob at 0x0000010967C21AD0>)
E        +      where <generator object Path.glob at 0x0000010967C21AD0> = glob('started-*')
E        +        where glob = (WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1925/test_failed_new_start_cleans_i1') / 'trace').glob

tests\unit\test_launcher_ownership.py:211: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_launcher_ownership.py::test_start_checks_configured_listener_and_health_path[powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_start_checks_configured_listener_and_health_path[pwsh.exe]
FAILED tests/unit/test_launcher_ownership.py::test_failed_new_start_cleans_its_own_pid_record[powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_failed_new_start_cleans_its_own_pid_record[pwsh.exe]
4 failed, 20 deselected in 2.38s
```

### Cleanup assertion RED after null-listener correction

```powershell
uv run --locked python -m pytest -q tests/unit/test_launcher_ownership.py -k 'concurrent or failed_new_start'
```

```text
..FF                                                                     [100%]
================================== FAILURES ===================================
_______ test_failed_new_start_cleans_its_own_pid_record[powershell.exe] _______

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1926/test_failed_new_start_cleans_i0')
shell = 'powershell.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_failed_new_start_cleans_its_own_pid_record(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "exited", "Start-HaloResearch.ps1", record=False)
        result = invoke(shell, wrapper, env)
        assert result.returncode != 0, result.stdout + result.stderr
        assert len(list((tmp_path / "trace").glob("started-*"))) == 1
>       assert not record.exists(), "failed new start must not leave its own stale record"
E       AssertionError: failed new start must not leave its own stale record
E       assert not True
E        +  where True = exists()
E        +    where exists = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1926/test_failed_new_start_cleans_i0/HaloResearchGateway/run/gateway.json').exists

tests\unit\test_launcher_ownership.py:212: AssertionError
__________ test_failed_new_start_cleans_its_own_pid_record[pwsh.exe] __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1926/test_failed_new_start_cleans_i1')
shell = 'pwsh.exe'

    @pytest.mark.parametrize("shell", SHELLS)
    def test_failed_new_start_cleans_its_own_pid_record(tmp_path, shell):
        wrapper, env, record = fixture(tmp_path, "exited", "Start-HaloResearch.ps1", record=False)
        result = invoke(shell, wrapper, env)
        assert result.returncode != 0, result.stdout + result.stderr
        assert len(list((tmp_path / "trace").glob("started-*"))) == 1
>       assert not record.exists(), "failed new start must not leave its own stale record"
E       AssertionError: failed new start must not leave its own stale record
E       assert not True
E        +  where True = exists()
E        +    where exists = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1926/test_failed_new_start_cleans_i1/HaloResearchGateway/run/gateway.json').exists

tests\unit\test_launcher_ownership.py:212: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_launcher_ownership.py::test_failed_new_start_cleans_its_own_pid_record[powershell.exe]
FAILED tests/unit/test_launcher_ownership.py::test_failed_new_start_cleans_its_own_pid_record[pwsh.exe]
2 failed, 2 passed, 20 deselected in 4.23s
```

### Targeted GREEN

```powershell
uv run --locked python -m pytest -q tests/unit/test_launcher_ownership.py
```

```text
........................                                                 [100%]
24 passed in 18.75s
```

### Falsification

```powershell
uv run --locked python -m pytest -q tests/unit/test_launcher_ownership.py
```

```text
............................................                             [100%]
44 passed in 30.17s
```

### Native lifecycle acceptance

```powershell
uv run --locked python -m pytest -q tests/acceptance/test_launcher_native.py
```

```text
..                                                                       [100%]
2 passed in 20.37s
```

### Full gate

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
82 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 31%]
........................................................................ [ 63%]
........................................................................ [ 95%]
...........                                                              [100%]
227 passed in 44.86s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

