# Research-only removal verification — 2026-09-02

## Result and scope

Removed Gmail composition/draft/send, GitHub issue/comment writes, generic form
submission, both action MCP tools, general action approval UI/routes, and broad
personal Chrome import. Research authentication remains; session import accepts
only cookies and Chrome Local State metadata. It is not site-filtered and has
not been proven with Scott's live research login.

The running Gateway was reloaded using its existing scripts after verifying the
launcher PID 28920, child/listener PID 25952, executable, command line, creation
time, and idle jobs. New launcher PID: 38560; service start:
2026-09-02T21:38:41.742701Z. DSH configurations, permissions, model routes, and
other repositories were not changed.

Existing vault records, profiles, DB tables, and historical receipts are preserved.
Deleted source and old tests are recoverable from the baseline Git commit
`41e5b6da1afcde6b6d451f213b32079d26764c0e`.

## Baseline, RED, GREEN

Exact baseline command, repository root:
```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```
Summary: `128 passed in 5.31s`; `[GATE] PASS (Commit)`.

The first sandbox attempt could not access the existing uv cache and ran no tests:
```text
error: Failed to initialize cache at C:\Users\scott\AppData\Local\uv\cache
Caused by: failed to open file C:\Users\scott\AppData\Local\uv\cache\sdists-v9\.git: Access is denied. (os error 5)
lock check failed with exit code 2
```
The successful baseline and all subsequent runs used the existing environment
under Scott's Windows account, not a new dependency installation.

Exact initial RED command:
```powershell
uv run --locked python -m pytest -q tests/unit/test_research_scope.py
```
Summary: `9 failed in 1.47s`. Failures were assertions detecting the two extra
MCP action tools, seven still-accepted personal-data categories, and the shipped
action package. Full failure tracebacks are in this task's tool transcript.
No import/setup error was counted as RED.

First full post-removal command:
```powershell
uv run --locked ruff format src tests
uv run --locked python -m pytest -q tests/unit
```
Summary: `124 passed in 3.91s`.

Seven further falsification cases were added after implementation: legacy
Gmail/GitHub/purchase/form plans, removed HTTP import options, legacy config,
and a cookie-labelled plan attempting to copy passwords. These are post-change
regression checks, not claimed as separate test-first cycles.

An intermediate canonical gate found two cleanup issues: F401 unused
`urllib.parse` in service.py and I001 import ordering in test_research_scope.py.
Both were corrected. The subsequent complete gate reported
`131 passed in 3.91s` and `[GATE] PASS (Commit)`.

Final canonical command:
```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```
Complete output:
```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
67 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 54%]
...........................................................              [100%]
131 passed in 3.98s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

Thirteen tests specifically exercising intentionally removed features were
retired; sixteen research-scope regression cases were added. Retained research,
connection, import, queue, job, browser, and provider tests remain in the suite.

## Live verification

Exact commands:
```powershell
& .\scripts\Stop-HaloResearch.ps1
& .\scripts\Start-HaloResearch.ps1
uv run --locked python tests/acceptance/mcp_smoke.py
```
Observed:
```text
Halo Research Gateway stopped.
Halo Research Gateway ok (PID 38560).
{'tools': 14, 'web_fetch': 'ok', 'chars': 1379}
```

HTTP checks against the live service:
- GET /health: ok; no actions capability property.
- POST /operator/api/actions/legacy/approve: 404.
- GET /operator: no Gmail preset, GitHub write form, complete-profile checkbox,
  or payment-data input.
- Session import remains operator-only under /operator/api/imports/chrome.

This was direct MCP/HTTP verification, **not** a new end-to-end DSH run.

## Documentation and landing-page source

Updated README, manual, operations, security, implementation status, changelog,
canonical skill, current scope, and historical-spec supersession notice.
Installed skill copies were synchronized in .agents, .claude, .lmstudio, and the
Halo Stack Research skill folder. Current Research-folder docs were synchronized;
historical versioned evidence was preserved.

The repository-local AGENTS.md was updated but remains intentionally ignored by
the repository. The same scope rule is committed in RESEARCH-ONLY-SCOPE.md and the
canonical skill, so it is not dependent on that local file.

Landing-page changes are copy/metadata only, with no new dependencies or redesign.
Exact website commands:
```powershell
npm run build
npm run lint
```
Both exited 0. Build warning/disclosure, verbatim:
```text
  Route (app)
  ─ ? /

  ? Unknown

  ? Some routes could not be classified. vinext currently uses static analysis
    and cannot detect dynamic API usage (headers(), cookies(), etc.) at build time.
    Automatic classification will be improved in a future release.
```
No visual browser/console/mobile QA was performed; source and served HTML checks
are not substituted for it. Hosted page publication and GitHub push/merge are
separate delivery steps and are not claimed here.

## Review and security checklist

- Inputs: removed tools/routes cannot submit; import category and copied paths
  are checked; stored non-research plans are rejected before approval/execution.
- Changed routes: import confirmation retains origin and CSRF validation.
  No new model-facing administrative endpoint was introduced.
- Secrets: no real accounts or secrets were used in tests or copied into evidence.
  Vault/runtime paths remain ignored; existing credentials were not revoked.
- Rendering/eval/deserialization: no new eval or executable deserialization;
  operator plan rendering retains HTML escaping. Visual UI verification is open.
- Dependencies: none added or upgraded; new-dependency advisory check is N/A.
- Performance: two model tool schemas and write adapters removed; no performance
  improvement claim was measured.
- Blast radius: complete offline suite, skill consistency, website build/lint,
  live MCP discovery/fetch, and retired HTTP route checks passed.

## What is not finished

See [the research-only finish list](RESEARCH-ONLY-SCOPE.md). Retrieval defects,
authenticated account/browser acceptance, optional challenge/provider wiring,
complete multi-step DSH proof, concurrency/recovery/installer evidence, and remote
delivery remain distinct from this removal. No email, publishing, purchasing,
account-operation, or personal-assistant backlog remains.
