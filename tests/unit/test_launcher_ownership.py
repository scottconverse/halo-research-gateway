"""Exercise the real PowerShell scripts with process/network boundaries intercepted.

All records/markers live under tmp_path. No native service process is started
or stopped by these deterministic tests; native lifecycle acceptance is separate.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
STARTED = "2026-09-02T00:00:00.0000000Z"
SHELLS = [name for name in ("powershell.exe", "pwsh.exe") if shutil.which(name)]
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows-native launcher contract")

SHIM = r"""
$ErrorActionPreference = 'Stop'
$global:haloFixturemode = $env:HALO_TEST_CASE
$global:haloFixturerun = Join-Path $env:LOCALAPPDATA 'HaloResearchGateway\run'
$global:haloFixturerecord = Join-Path $global:haloFixturerun 'gateway.json'
$global:haloFixturetrace = Join-Path $env:LOCALAPPDATA 'trace'
$global:haloFixturepython = Join-Path $env:HALO_TEST_REPO '.venv\Scripts\python.exe'
$global:haloFixturestarted = [DateTimeOffset]::Parse('2026-09-02T00:00:00.0000000Z').UtcDateTime
$global:haloFixturecreated = $null
function New-FakeProcess([int]$Number) {
    $date = $global:haloFixturestarted
    if ($global:haloFixturemode -eq 'reused_pid') { $date = $date.AddMinutes(10) }
    $value = [pscustomobject]@{
        Id=$Number; Handle=[IntPtr]1; StartTime=$date
        HasExited=($global:haloFixturemode -eq 'exited'); ExitCode=7
    }
    $value | Add-Member -MemberType ScriptMethod -Name Dispose -Value {}
    return $value
}
function global:Get-CimInstance {
    param($ClassName, $Filter, $ErrorAction)
    if ($global:haloFixturemode -eq 'cim_error') { throw 'fixture CIM access denied' }
    if ($global:haloFixturemode -eq 'stale') { return $null }
    $number = [int]($Filter -replace '^ProcessId\s*=\s*','')
    if (-not (Test-Path -LiteralPath $global:haloFixturerecord) -and -not $global:haloFixturecreated) { return $null }
    $exe = $global:haloFixturepython
    $command = '"' + $exe + '" -m halo_research_gateway'
    if ($global:haloFixturemode -eq 'lookalike') { $command = 'python.exe -m other --label halo_research_gateway' }
    if ($global:haloFixturemode -eq 'foreign_executable') { $exe = 'C:\unrelated\python.exe' }
    $fake = New-FakeProcess $number
    return [pscustomobject]@{
        ProcessId=$number; ParentProcessId=0; ExecutablePath=$exe
        CommandLine=$command; CreationDate=$fake.StartTime
    }
}
function global:Get-Process {
    param($Id, $ErrorAction)
    return New-FakeProcess ([int]$Id)
}
function global:Start-Process {
    param($FilePath, $ArgumentList, $WorkingDirectory, $WindowStyle, [switch]$PassThru,
          [switch]$NoNewWindow, $ErrorAction)
    Set-Content -LiteralPath (Join-Path $global:haloFixturetrace "started-$PID") -Value $FilePath
    if ($global:haloFixturemode -eq 'concurrent') { Microsoft.PowerShell.Utility\Start-Sleep -Milliseconds 400 }
    $global:haloFixturecreated = New-FakeProcess $PID
    return $global:haloFixturecreated
}
function global:Stop-Process {
    param($Id, $InputObject, [switch]$Force, $ErrorAction)
    if ($global:haloFixturemode -eq 'stop_error') { throw 'fixture process access denied' }
    $number = $Id
    if ($InputObject) { $number = $InputObject.Id; $InputObject.HasExited = $true }
    @{number=$number; held_object=($null -ne $InputObject)} | ConvertTo-Json |
        Set-Content -LiteralPath (Join-Path $global:haloFixturetrace 'stopped.json')
}
function global:Wait-Process { param($Id, $InputObject, $Timeout, $ErrorAction) }
function global:Get-NetTCPConnection {
    param($LocalPort, $State, $ErrorAction)
    Set-Content -LiteralPath (Join-Path $global:haloFixturetrace 'port.txt') -Value $LocalPort
    if ($global:haloFixturemode -eq 'foreign_listener') { return [pscustomobject]@{OwningProcess=987654;LocalPort=$LocalPort} }
    if ($global:haloFixturemode -eq 'unhealthy') { return $null }
    if (Test-Path -LiteralPath $global:haloFixturerecord) {
        $stored = Get-Content -LiteralPath $global:haloFixturerecord -Raw | ConvertFrom-Json
        return [pscustomobject]@{OwningProcess=$stored.pid;LocalPort=$LocalPort}
    }
    if ($global:haloFixturemode -eq 'concurrent') { Microsoft.PowerShell.Utility\Start-Sleep -Milliseconds 400 }
    return $null
}
function global:Invoke-RestMethod {
    param($Uri, $TimeoutSec, $ErrorAction)
    Set-Content -LiteralPath (Join-Path $global:haloFixturetrace 'health.txt') -Value $Uri
    if ($global:haloFixturemode -eq 'unhealthy') { throw 'fixture health unavailable' }
    return @{status='ok';version='0.2.0'}
}
& (Join-Path $env:HALO_TEST_REPO ('scripts\' + $env:HALO_TEST_SCRIPT))
"""


def fixture(tmp_path, case, script, record=True):
    runtime = tmp_path / "HaloResearchGateway" / "run"
    runtime.mkdir(parents=True, exist_ok=True)
    (tmp_path / "trace").mkdir(exist_ok=True)
    record_path = runtime / "gateway.json"
    if record:
        identity = {
            "schema": 2,
            "pid": 1234500,
            "executable": str(REPO / ".venv" / "Scripts" / "python.exe"),
            "repository": str(REPO),
            "started_at": STARTED,
        }
        if case == "foreign_executable":
            identity["executable"] = "C:\\unrelated\\python.exe"
        if case == "wrong_repository":
            identity["repository"] = "C:\\unrelated"
        record_path.write_text(json.dumps(identity), encoding="utf-8")
    wrapper = tmp_path / "launcher-fixture.ps1"
    wrapper.write_text(SHIM, encoding="utf-8")
    config = tmp_path / "config.toml"
    config.write_text("[server]\nport = 8765\n", encoding="utf-8")
    env = dict(os.environ)
    env.update(
        LOCALAPPDATA=str(tmp_path),
        HALO_TEST_CASE=case,
        HALO_TEST_REPO=str(REPO),
        HALO_TEST_SCRIPT=script,
        HALO_RESEARCH_CONFIG=str(config),
    )
    # Windows PowerShell must not inherit PowerShell 7's incompatible modules.
    env["PSModulePath"] = os.pathsep.join(
        [
            str(Path(os.environ["SystemRoot"]) / "System32/WindowsPowerShell/v1.0/Modules"),
            str(Path(os.environ["ProgramFiles"]) / "WindowsPowerShell/Modules"),
        ]
    )
    return wrapper, env, record_path


def invoke(shell, wrapper, env):
    return subprocess.run(
        [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(wrapper)],
        env=env,
        capture_output=True,
        text=True,
        timeout=35,
        check=False,
    )


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("case", ["reused_pid", "lookalike", "foreign_executable", "wrong_repository"])
def test_stop_refuses_unowned_process_and_preserves_record(tmp_path, shell, case):
    wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
    result = invoke(shell, wrapper, env)
    assert result.returncode != 0, result.stdout + result.stderr
    assert record.exists(), "mismatched identity must remain for operator review"
    assert not (tmp_path / "trace" / "stopped.json").exists(), "unowned process was stopped"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("case", ["reused_pid", "lookalike", "wrong_repository", "unhealthy"])
def test_start_refuses_false_already_running_claim(tmp_path, shell, case):
    wrapper, env, record = fixture(tmp_path, case, "Start-HaloResearch.ps1")
    result = invoke(shell, wrapper, env)
    assert result.returncode != 0, result.stdout + result.stderr
    assert record.exists()
    assert not list((tmp_path / "trace").glob("started-*"))
    assert not (tmp_path / "trace" / "stopped.json").exists()


@pytest.mark.parametrize("shell", SHELLS)
def test_stop_uses_held_process_object_for_valid_identity(tmp_path, shell):
    wrapper, env, record = fixture(tmp_path, "valid", "Stop-HaloResearch.ps1")
    result = invoke(shell, wrapper, env)
    assert result.returncode == 0, result.stdout + result.stderr
    stopped = json.loads((tmp_path / "trace" / "stopped.json").read_text(encoding="utf-8-sig"))
    assert stopped["held_object"], "stop must retain the validated process handle, not look up PID again"
    assert not record.exists()


@pytest.mark.parametrize("shell", SHELLS)
def test_concurrent_starts_launch_only_one_process(tmp_path, shell):
    wrapper, env, record = fixture(tmp_path, "concurrent", "Start-HaloResearch.ps1", record=False)
    command = [shell, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", str(wrapper)]
    processes = [
        subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)
    ]
    try:
        outputs = [process.communicate(timeout=35) for process in processes]
        assert all(process.returncode == 0 for process in processes), outputs
        assert len(list((tmp_path / "trace").glob("started-*"))) == 1, "concurrent launch duplicated the provider"
        assert json.loads(record.read_text(encoding="utf-8-sig"))["schema"] == 2
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()  # Only this fixture's intercepted PowerShell process.
            process.wait(timeout=5)


@pytest.mark.parametrize("shell", SHELLS)
def test_start_checks_configured_listener_and_health_path(tmp_path, shell):
    wrapper, env, _ = fixture(tmp_path, "valid", "Start-HaloResearch.ps1")
    (tmp_path / "config.toml").write_text('[server]\nport = 18765\nhealth_path = "/alive"\n', encoding="utf-8")
    result = invoke(shell, wrapper, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (tmp_path / "trace" / "port.txt").read_text(encoding="utf-8-sig").strip() == "18765"
    assert (tmp_path / "trace" / "health.txt").read_text(encoding="utf-8-sig").strip() == "http://127.0.0.1:18765/alive"


@pytest.mark.parametrize("shell", SHELLS)
def test_failed_new_start_cleans_its_own_pid_record(tmp_path, shell):
    wrapper, env, record = fixture(tmp_path, "exited", "Start-HaloResearch.ps1", record=False)
    result = invoke(shell, wrapper, env)
    assert result.returncode != 0, result.stdout + result.stderr
    assert len(list((tmp_path / "trace").glob("started-*"))) == 1
    assert not record.exists(), "failed new start must not leave its own stale record"


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("recorded", [False, True])
def test_start_never_uses_unrelated_listener(tmp_path, shell, recorded):
    wrapper, env, record = fixture(tmp_path, "foreign_listener", "Start-HaloResearch.ps1", recorded)
    result = invoke(shell, wrapper, env)
    assert result.returncode != 0, result.stdout + result.stderr
    assert record.exists() is recorded
    assert not list((tmp_path / "trace").glob("started-*"))
    assert not (tmp_path / "trace" / "stopped.json").exists()


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize("case", ["cim_error", "stop_error"])
def test_stop_access_error_preserves_record(tmp_path, shell, case):
    wrapper, env, record = fixture(tmp_path, case, "Stop-HaloResearch.ps1")
    result = invoke(shell, wrapper, env)
    assert result.returncode != 0, result.stdout + result.stderr
    assert record.exists()


@pytest.mark.parametrize("shell", SHELLS)
def test_stop_removes_only_stale_record(tmp_path, shell):
    wrapper, env, record = fixture(tmp_path, "stale", "Stop-HaloResearch.ps1")
    result = invoke(shell, wrapper, env)
    assert result.returncode == 0, result.stdout + result.stderr
    assert not record.exists()
    assert not (tmp_path / "trace" / "stopped.json").exists()


@pytest.mark.parametrize("shell", SHELLS)
@pytest.mark.parametrize(
    "schema,started,accepted",
    [
        (None, "2026-09-02T00:00:01.5000000Z", True),
        (None, "2026-09-02T00:00:02.0000001Z", False),
        (None, "2026-09-01T23:59:59.9999999Z", False),
        (2, "2026-09-02T00:00:00.0000001Z", False),
        (3, STARTED, False),
    ],
)
def test_creation_time_precision_and_legacy_window(tmp_path, shell, schema, started, accepted):
    wrapper, env, record = fixture(tmp_path, "valid", "Stop-HaloResearch.ps1")
    identity = json.loads(record.read_text(encoding="utf-8"))
    if schema is None:
        identity.pop("schema")
    else:
        identity["schema"] = schema
    identity["started_at"] = started
    record.write_text(json.dumps(identity), encoding="utf-8")
    result = invoke(shell, wrapper, env)
    assert (result.returncode == 0) is accepted, result.stdout + result.stderr
    assert record.exists() is not accepted
    assert (tmp_path / "trace" / "stopped.json").exists() is accepted
