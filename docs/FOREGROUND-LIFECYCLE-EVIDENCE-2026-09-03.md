# Foreground lifecycle evidence — September 3, 2026

Foreground startup now uses the same process/PID identity and readiness checks
as background startup. Its console waits without holding the lifecycle mutex;
normal stop and duplicate-start can run from another terminal. Child exit returns
the actual exit code and cleanup removes only the exact record for that launch.
A replacement record is preserved. This closes the unmanaged foreground gap,
not the whole reliability or DSH/release acceptance list.

Base: `4b68816dd4ef58bf9eb8a200be5796bd65995343`. The final commit is recorded in
the operator delivery receipt. No installed service, task, host settings, DSH
configuration, denied installed reference, account or paid provider was changed.

## Verification

Working directory: `C:\Users\scott\Desktop\Code\halo-research-gateway`.
Full command/output chunks, including all six RED failures, are retained in
[raw verification](evidence/foreground-20260903.json).

Untouched baseline:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_launcher_ownership.py tests/acceptance/test_launcher_native.py -q --tb=short
46 passed in 49.50s
```

Native RED, before production changes:

```text
.\.venv\Scripts\python.exe -m pytest tests/acceptance/test_launcher_native.py -k foreground -q --tb=short
6 failed, 2 deselected in 20.63s
```

Every case failed on `Healthy foreground Gateway has no managed PID record`
after the actual fixture Gateway returned healthy. This was an assertion failure,
not a missing executable/import or mocked health result. Cleanup identified only
descendants of the fixture's held launcher and left the installed service alone.

Initial GREEN, before adding the fourteen intercepted-boundary falsification cases:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_launcher_ownership.py tests/acceptance/test_launcher_native.py -q --tb=short
52 passed in 93.37s (0:01:33)
```

Widened final lifecycle run:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_launcher_ownership.py tests/acceptance/test_launcher_native.py -q --tb=short
66 passed in 104.22s (0:01:44)
```

The native suite has eight cases across Windows PowerShell 5.1 and PowerShell 7:
the existing background duplicate-start/stop/restart checks plus foreground
ordinary-stop, child termination and replacement-record checks. Foreground checks
launch the real venv/Gateway, inspect actual health and process ancestry, verify
duplicate start, and require listener closure. Terminated native children return
nonzero; precise 0/37 exit codes are separately tested with intercepted processes.
Native replacement uses a deliberately different fixture record, not a claim that
a second full replacement Gateway was started in that case.

Canonical full gate ([complete output](evidence/foreground-gate-20260903.json)):

```text
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/Invoke-QualityGate.ps1 -Scope Full
589 passed in 109.56s (0:01:49)
[GATE] PASS (Full)
```

Lock, format, lint and bundled skill validation also passed. The gate executes
unit/fixture tests; native acceptance remains the separate 66-case run above.

## Falsification, review and boundaries

- Intercepted-boundary tests alter each PID identity field independently: PID,
  creation time (one 100-nanosecond tick), repository, executable and schema. The
  exiting foreground command preserves those changed records byte-for-byte.
- Existing tests still cover unowned/reused PID refusal, invalid commands,
  foreign listeners, stale records, failed starts, access errors and legacy
  creation-time precision. Their assertions were not weakened.
- Native fixtures use different ports, temporary config/storage, and explicit
  application-data/module-cache paths. No provider/account/browser call is needed.
- Source/readiness/cleanup were reviewed together with Stop-HaloResearch and the
  Gateway's Windows Job Object. That object contains Gateway descendants; it does
  not prove that forcibly killing the parent console triggers graceful cleanup.
- Blast radius: both start modes share launch/readiness and failure cleanup;
  stop semantics and fourteen research tools are unchanged. Installer tests import
  the native test environment helper, which now also isolates module-cache and
  platformdirs overrides; this checkpoint does not rerun the full fresh installer.
- No new dependency, endpoint/authentication boundary, rendering/eval, secret
  handling or network policy is introduced. PID removal validates exact identity
  under the same lifecycle lock. Logs/evidence contain only disposable identities
  and service-health information, not account content or credentials.
- README, manual, operations, current status, scope and the repository-bundled
  scope reference are updated. Installed reference copies are not overwritten.

Remaining: Ctrl+C/forced console closure, actual scheduled logon, strict wall-clock
startup bounds, broad browser-tree/hung-process cleanup, longer stress, real-login
and full DSH acceptance. The source-only checkpoint does not reload the installed
Gateway. Product version stays 0.2.0; final push/merge/site/0.3.0 tagging remain
conditional on the full acceptance list.
