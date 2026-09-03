# Native installer and repair evidence — September 3

This checkpoint fixes actual installer defects and tests fresh native Windows
checkouts/virtual environments with disposable host profiles. It does not change
the running Gateway, DSH, real host settings, scheduled task or denied installed
skill references. Version remains 0.2.0; this is not a push/merge/release receipt.
Base source: `70f083d40b72c663b2388b849a0b9b8cc58809b6`.

## What changed and why

- New sample configurations leave storage/browser paths at the current Windows
  user's defaults instead of pointing at the developer's absolute profile.
  Existing runtime configuration is never rewritten by repair.
- LM Studio registration works in Windows PowerShell 5.1 and PowerShell 7,
  preserves unrelated settings and uses the active configured MCP port/path.
  Existing settings get a unique original-file backup; complete serialized
  output is staged before replacement. Detected concurrent changes are refused.
- Malformed JSON, non-object roots (including singleton arrays) and invalid
  `mcpServers` types are rejected without changing the host file or echoing its
  contents. Close host settings during registration: the final hash check is
  not an atomic lock respected by other applications.
- Git hook setup errors now stop installation before skill/host registration
  instead of being silently cleared by later successful commands.

No dependency, model configuration, research tool, permissions policy or account
action was added. The configured Git commit hook still requires PowerShell 7;
the installer supports either shell. Installation can partially complete before
a later registration failure; it does not promise a whole-install rollback.

## Test scope

Read before changes: installer/uninstaller/start/stop/lifecycle scripts,
configuration loader/sample, OCR installer and tests, existing native/fixture
launcher tests, service runtime paths, installed platformdirs Windows resolver,
quality/skill validation scripts, README/manual/operations and governing scope.
The existing loader resolves the configured server address; no parallel parser
or hard-coded registration address remains.

Deterministic tests execute the real installer script against copied inputs with
package setup/service boundaries intercepted. The endpoint query uses the real
Python config loader. Temporary USERPROFILE/LOCALAPPDATA paths prevent real host
registration. Windows module paths are normalized for each shell. Fixtures check
Unicode/date-like settings, exact backup contents, malformed/singleton JSON,
unknown host preservation, config preservation and early Git failure.

The separate native test creates a new source checkout and virtual environment,
runs actual locked dependency/OCR installation and the full quality gate, installs
skills into a disposable profile, registers a disposable LM Studio JSON file and
starts a real loopback Gateway. A new-environment MCP client verifies fourteen
tools, actual HTTP source reading and Chrome-rendered JavaScript text. It then
stops, checks listener closure, repairs without changing the stored database or
operator/host config, restarts with a new process identity and stops again.

The active test config selects random non-8765 ports and an exact loopback source;
the separately generated default config is loaded and its resolved paths checked
inside the disposable profile. `WIN_PD_OVERRIDE_LOCAL_APPDATA` isolates the
Windows known-folder resolver as well as shell paths. Existing Windows 11,
Python 3.12, uv and Chrome are prerequisites; no WSL/container/VM or global browser
installation is performed. This is fresh application installation on the current
OS, not evidence from a clean OS or another user's real profile.

## Exact retained verification

Commands, full failure diagnostics and output chunks are retained in
[execution records](evidence/installer-20260903.json). Native stage records include
dependency/gate output, probe output, cleanup and per-file source-code hashes.
Initial long-string assertion output was shortened by pytest; clean diagnostics
were rerun before the corresponding fixes. No truncated output is called complete.

Baseline:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_launcher_ownership.py tests/acceptance/test_launcher_native.py -q --tb=short
46 passed in 50.35s

.\.venv\Scripts\python.exe -m pytest tests/unit/test_ocr_data.py -q
7 passed in 1.32s
```

Actual installer assertion RED, after compacting diagnostics without changing
the assertions:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_installer_contract.py -q --tb=short
6 failed in 3.75s
```

Final isolated installer boundary checks:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_installer_contract.py -q --tb=short
23 passed in 19.29s
```

Widened installer/OCR/launcher regression before the final array/preflight additions:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/test_installer_contract.py tests/unit/test_ocr_data.py tests/unit/test_launcher_ownership.py -q --tb=short
71 passed in 50.22s
```

Final native run (its exact shell command also performs format/lint and sets the
evidence directory; the full command is retained in the execution record):

```text
.\.venv\Scripts\python.exe -m pytest tests/acceptance/test_install_native.py -q --tb=short
2 passed in 504.33s (0:08:24)
```

Both shells completed all assertions, including actual HTTP/JavaScript research
through the fresh environment's network MCP, byte-identical state/config after
repair and stop/restart. The four nested actual full-gate summaries are:

```text
# Windows PowerShell 5.1: initial installation, then repair
575 passed in 108.07s (0:01:48)
[GATE] PASS (Full)
575 passed in 103.93s (0:01:43)
[GATE] PASS (Full)
# PowerShell 7: initial installation, then repair
575 passed in 109.05s (0:01:49)
[GATE] PASS (Full)
575 passed in 102.67s (0:01:42)
[GATE] PASS (Full)
```

The installer invokes `scripts/Invoke-QualityGate.ps1 -Scope Full` in each fresh
checkout. All 56 captured source/script/config/dependency file hashes match the
final working source in each accepted native receipt (zero mismatches). Full
native stage output is under [accepted receipts](evidence/installer-native/accepted/).
The local commit containing this report identifies the checkpoint; its separate
commit-hook receipt belongs to the operator delivery record. No CI is implied.

After these accepted native runs, final inventory found a 4641-byte Windows
PowerShell ModuleAnalysisCache created during testing in the repository. It was
moved intact into task output (`installer-unintended-module-cache.bin`, SHA256
`46350DBE29CAAB10F65CAE3F93F81B26EB5C0ACCB6F2C489CE0027C449EEFDE3`). New test
helpers now explicitly isolate cache and working directories; no product code
changed. Their follow-up was `23 passed in 20.40s`, and repository status showed
no recreated cache. Exact command/output: [cache-isolation record](evidence/installer-cache-isolation-20260903.json).
The binary cache is not release source and is excluded from the regenerated
manifest. No user data was deleted.

## Failure and falsification inventory

1. Six original failures reproduced unavailable `-AsHashtable` in Windows
   PowerShell, wrong configured endpoint, developer-specific paths and ignored
   Git failure. No unrelated existing assertions were removed or weakened.
2. The first implementation run failed because the new test inherited incompatible
   PowerShell 7 module paths into Windows PowerShell. Normalized the fixture's
   module path, matching the existing native launcher fixture; no fake hash
   function replaced the real one.
3. Malformed host JSON printed a synthetic credential-like marker in Windows
   PowerShell. The exact failure was rerun with full diagnostic output, then
   the parse failure was sanitized. No real credential was used.
4. A singleton JSON array was unwrapped into an object by the shell pipeline.
   Both shells failed the preservation assertion before explicit object-root
   validation. Empty arrays/null and invalid nested types remain covered.
5. An embedded native MCP probe had a quoting error. The installer itself
   completed, but both widened tests failed before reading sources. A cheap
   compile preflight reproduced the syntax error; the probe was corrected.
6. The corrected probe then exposed the synthetic page's single-word content:
   Chrome rendered it, but Crawl4AI reported `Structural: minimal_text on small
   page (279 bytes, 28 chars visible)` and success=false. Gateway correctly kept
   that failure explicit (`CRAWL_NO_EVIDENCE`). A direct traced native run proved
   the cause. The fixture was changed to a normal article and directly verified
   before another full run; no crawler success flag or rejection policy changed.
   Extremely small pages may still be rejected by Crawl4AI; direct HTTP reading
   is distinct from that browser classifier.

Earlier native first-pass receipt (before the diagnostic/array fixes and before
the browser-reading probe) was `1 passed, 1 deselected in 242.65s (0:04:02)`.
Its nested gates were `570 passed in 104.99s (0:01:44)` and
`570 passed in 100.21s (0:01:40)`. It is a historical installation/repair receipt,
not the final source or browser acceptance. The subsequent probe-error run was
`2 failed in 268.03s (0:04:28)`; the too-small-page run was
`2 failed in 282.65s (0:04:42)`. All stay recorded, not converted into passes.

## Security and remaining boundaries

- Inputs: current config loader, validated host JSON shape, exact scoped files,
  pre-replacement hash check and complete serialization. General cross-app
  concurrent-write arbitration is not guaranteed.
- Auth/routes: no new service route/tool. Only explicit installer registration
  touches the named host entry; native tests use synthetic files and local targets.
- Secrets: parse errors do not echo settings. Backups may hold real host secrets
  in actual use and must stay local. `.gitignore` excludes runtime/vault/config/
  private evidence; native committed evidence contains synthetic settings only.
- Rendering/deserialization: JSON conversion only; no input evaluation. Browser
  JavaScript in the test is a fixed local article fixture.
- Dependencies: none added. Existing locked dependencies and hash-pinned OCR
  assets are installed; this is not a new repository-wide vulnerability audit.
- Performance: setup runs a full gate and may download dependencies; it is not
  promised to complete within five minutes or transactionally undo every step.
- Live state: the installed service remains on version0.2.0 with start
  `2026-09-03T10:29:12.730843Z`, five complete/one cancelled jobs and no active jobs;
  both paid providers are disabled with zero attempts/spend. No production reload,
  real task registration, personal profile import, reboot, DSH change or release.

Foreground ownership, actual scheduled logon, long-running stress and broader
process/browser bounds remain on the reliability list. DSH supported synthesis/
job lifecycle, real selected login and installed authenticated-source acceptance
remain separate. This checkpoint does not waive the research-only finish list.
