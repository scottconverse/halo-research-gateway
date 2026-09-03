# Research-job request and output bounds — September 3

## What is proved

The source now rejects oversized/unknown job request fields before record or
worker creation. Whole status replies obey their requested character budget,
including nested evidence. The full stored question/evidence is unchanged.
Known formatting/retention failures preserve actual control identity/state
rather than hiding a successful pause/cancel.

Three concurrent native MCP clients read the same seeded job at 2000, 4000 and
6000 characters and recovered identical complete evidence. This is a disposable
native fixture, not public upstream, installed DSH or pause/resume acceptance.
The installed baseline during source testing was 7bf71e0, version 0.2.0.
A new installed revision requires a separate reload/DSH receipt.

## Behavior and deliberate choices

- Question/profile/ID maximums are 8192/64/128 characters. Profile labels must
  be nonempty; they remain labels, not routing/permission settings.
- Only max_sources, max_pages and timeout_seconds are accepted in limits.
  Existing positive-integer validation and lower ceilings are preserved.
  A nonempty research_job cursor is rejected; use deep_research for evidence.
- The question preview is at most 128 characters and explicitly marked when
  shortened, including its original length. The full question stays in SQLite.
- A first nested page may defer all evidence to its next_cursor when metadata
  and evidence cannot fit together. It reports zero returned items and
  incomplete coverage; the next standalone page starts with the first item.
  A normal standalone page must fit before this deferral is allowed.
- Continuation binds the caller's supported budget and original chunk identity,
  not the smaller nested-page allowance. Omitting max_chars also works.
  Default status retains the previous 4000-character evidence-page budget.
- Optional metadata omissions are marked JOB_STATUS_METADATA_OMITTED. Larger
  legacy fields can produce a minimal control reply with
  JOB_STATUS_FIELDS_OMITTED. Underlying rows are not deleted or rewritten.
- Unformattable metadata/retention produces OUTPUT_ITEM_TOO_LARGE or
  SNAPSHOT_TOO_LARGE inside partial progress, while actual job ID/state remains.
- Other readers still require nonempty evidence pages. The new deferral is
  opt-in only for a nested job page after its standalone page fits.

The initial tests expected a nonempty nested page at every size. A stronger
native fixture with a title, SHA, MIME type and seven real-shaped warnings
proved that all metadata and evidence do not fit at 2000. The selected contract
explicitly defers that initial evidence page. Tests allow only an initial empty
page with a real cursor/zero returned coverage/incomplete coverage; subsequent
pages must contain evidence and concatenation must equal the entire source.
No complete-source, coverage, owner mapping or lifecycle assertion was removed.

## Exact verification

Complete commands, summaries, failures and warnings are in
[evidence/job-bounds-20260903.json](evidence/job-bounds-20260903.json).
Only passing-test progress chunks are omitted. The first output-truncated RED
capture was repeated before source changes to preserve the entire failure log.

| Run | Exact summary |
| --- | --- |
| Baseline job suite | `29 passed in 5.05s` |
| Full RED capture | `10 failed, 1 passed in 1.81s` |
| First small-page implementation | `1 failed, 39 passed in 5.43s` |
| First focused green | `40 passed in 5.38s` |
| Retention falsification, fixture mistake retained | `2 failed, 1 passed, 11 deselected in 1.14s` |
| Corrected active legacy fixture | `1 failed, 2 passed, 11 deselected in 1.18s` |
| Retention fix | `43 passed in 5.68s` |
| First full gate | `4 failed, 507 passed in 77.13s (0:01:17)` |
| Cache/ownership/job compatibility | `71 passed in 7.57s` |
| Final deferred-page/envelope suite | `36 passed in 4.23s` |
| Final warning-heavy native test | `1 passed in 3.21s` |
| Final full gate | `511 passed in 77.00s (0:01:17)` |

The first full gate exposed two minimal cache fixtures missing request metadata
and two ownership-test stubs with the old service signature. The renderer now
tolerates absent preview metadata. Only the stubs' accepted keywords changed;
the configured/unknown-header owner assertions are intact, with added default
argument assertions. No ownership/routing code changed.

The active legacy fixture was corrected instead of changing terminal rules:
the original incorrectly attempted to cancel a complete job. The native
diagnostic also exposed premature test cleanup when a peer failed; all clients
are now awaited with return_exceptions before stopping the owned fixture process.
The entire original teardown error is retained in the evidence JSON.

Final native command:
```powershell
uv run --locked ruff format src/halo_research_gateway/service.py src/halo_research_gateway/envelope.py tests/unit/test_job_bounds.py tests/acceptance/test_job_bounds_native.py
uv run --locked python -m pytest -q tests/unit/test_job_bounds.py tests/unit/test_job_continuation.py tests/unit/test_envelope.py
uv run --locked python -m pytest -q -s tests/acceptance/test_job_bounds_native.py
```

| Requested | Actual status characters | Pages, including deferred first page | Source hash |
| --- | --- | --- | --- |
| 2000 | 1894 | 23 | 96d1bb17272664a0fb044fda6181569fd022329a7254985dcfc05fba106bac36 |
| 4000 | 3984 | 4 | same |
| 6000 | 5984 | 2 | same |

One fixture job remained paused, no invalid request created another job, no
public egress occurred, and the exact fixture process was cleaned up.

Final full command:
```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```
```text
511 passed in 77.00s (0:01:17)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)
```

## Scope, security and limits

Read before changes: Gateway AGENTS/current scope, job manager/control/status,
shared envelope/cursor path, output config, existing lifecycle/cache/ownership
tests, native MCP fixture, README/manual/changelog/status and bundled scope.

Trust-boundary lengths/known fields are validated before job creation; errors
do not echo the submitted payload. Existing MCP owner mapping and job state
guards remain. No endpoint/auth model, unsafe rendering/eval, dependency,
credential, private profile, paid provider, DSH model/preset/context/permission
or schema/version change was introduced. Dependency vulnerability review is
N/A because no dependency changed. Existing secret/ignore checks remain required
before checkpoint/release.

This bounds job input persistence and response serialization, not pre-parsed
HTTP request allocation, legacy-database size, total/native RAM, all provider
deadlines or synchronous DDGS termination. Config-wide validation and broader
provider/browser/concurrency/installer checks remain separate. The entire
research-only finish list remains RESEARCH-ONLY-SCOPE.md. No full DSH lifecycle,
release, push, merge or 0.3.0 tag is claimed by this source record.
