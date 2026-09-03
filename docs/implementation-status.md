# Implementation status — 2026-09-02

Current scope is [research-only](RESEARCH-ONLY-SCOPE.md). Previous 0.2.0 receipts describe older code, not proof of full current acceptance.

## Current code

Fourteen research MCP tools: discovery/fallback, direct fetch, JavaScript crawl, Reddit, PDF/documents, deep research, read-only GitHub, transcripts, communities, exact local targets, and bounded research jobs. Shared caching/queues, encrypted research connections, OAuth, and optional disabled challenge/proxy adapters remain.

Removed: Gmail, GitHub writes, general form submission, general action preparation/approval/execution, and broad personal Chrome import. Cookie-only research-session import has its own review route. Old data and receipts are preserved; legacy actions cannot execute there.

## Evidence for this revision

The untouched baseline passed 128 tests. Nine new scope assertions failed on the unwanted features before removal. The first post-removal unit/fixture run passed 124 tests; the count falls because tests exercising intentionally removed features were replaced with removal checks. Final gate/deployment evidence is recorded separately; these counts do not prove DSH, live accounts, or paid-provider use.

## Still required

The final gate passed `131 passed in 3.98s`. The live service exposes fourteen tools, public fetch passed, and the retired action approval endpoint returns 404. See [removal evidence](RESEARCH-ONLY-REMOVAL-EVIDENCE-2026-09-02.md). These are not end-to-end DSH or live-account acceptance claims.

## Current checkpoints

GitHub whole-operation bounds now cover token setup and all follow-up requests
with one HTTP elapsed-time and aggregate decoded-byte budget. Explicit failures
do not return partial source collections as successful or trigger public fallback.
Twelve new unit cases plus a native two-MCP-client/fake-API fixture cover timeout,
overflow, independent callers, cancellation, disconnect and successful follow-up.
No installed authenticated GitHub or DSH pass is implied; the installed service
has not been reloaded for this source change. See
GITHUB-OPERATION-BOUNDS-EVIDENCE-2026-09-03.md.

Job request/status bounds now have source and native concurrent-client evidence:
finite question/profile/ID fields, only the three numeric limits, explicit
misdirected-cursor rejection, whole-status output sizing, marked previews and
lossless continuation at all supported sizes. Formatting/retention failures
retain the actual control identity/state. Installed/DSH proof is separate.
See JOB-BOUNDS-EVIDENCE-2026-09-03.md for failures, commands and limits.

September 3 DSH job trials: two real jobs completed with partial public evidence
and exact continuation reads, but both finished before pause. No DSH lifecycle
pass is claimed. The observed generic control errors are repaired in source:
six known codes use safe error envelopes; unexpected errors stay sanitized.
The full gate and disposable native MCP check pass; installed evidence requires
a separate reload receipt. See DSH-JOB-EVIDENCE-2026-09-03.md.

Compact cursor repair: source now emits 51-character authenticated references,
with bounded visible metadata, public-cache restart recovery and memory-only
private references. Legacy layout-3 inline cursors remain usable, including as a
storage-pressure fallback. Expiry, tamper, tool, budget and immutable-evidence
checks remain. Source/native acceptance and installed/DSH acceptance must be
reported separately; shortening a token is not proof of model completion.

September 3 DSH repair: the shadow tools package was preserved as a backup and
replaced with a junction to the identical existing package used by the agent loop.
The real identity assertion changes from failure to success. All 121 prior sessions
and 130 protected files survive the idle DSH-only restart unchanged. Real search,
source reading and one exact-cursor continuation now dispatch. The broad six-minute
run still failed to finish, with four miscopied cursor rejections and seven
compactions. A stricter result-based acceptance checker has five new regression
tests; it does not turn that failed run green. See
DSH-RESOLUTION-EVIDENCE-2026-09-03.md. Final target is `0.3.0`, not yet released.

Handoff followup before push: completion responses now retain their original
session identity across a concurrent new start, and the exposed deadline uses
the lower configured limit. Cancellation during Playwright startup no longer
abandons its driver in profile loading or visible handoff. Nineteen focused
unit cases pass; four new native handoff/UI/startup-cancellation cases pass.
The earlier race-test attempt accidentally entered real driver startup and hung;
only its verified test driver and isolated pytest process were stopped. That run
has no completed pytest summary and is not counted as a pass. Replayed assertion
failures, corrected results and cleanup commands are retained in the evidence.

September 3 human-handoff source checkpoint: a public research URL and existing
owned profile can be opened by the operator in isolated visible Chrome, followed
by Done/Cancel and a managed-profile retry using bounded memory-only cookies.
Fifteen new unit cases cover operator authority, state, cancellation, timeout,
cookie retention/caps, profile import ownership and redaction. Full gate:
`466 passed in 78.72s (0:01:18)`. Separate native browser/UI plus prior traversal/
challenge regression: `11 passed in 24.51s`. The synthetic challenge button is
test-automated: this is not a real operator login, network-MCP or DSH handoff
proof, paid use, installed reload or final release. See
HUMAN-HANDOFF-EVIDENCE-2026-09-03.md. Earlier "human handoff unfinished" statements
below describe their dated checkpoints, not the newer fixture-tested source.

Local-reader policy followup: GET now requires operator permission before any
network contact; recognized sensitive query values are redacted in citation and
snapshot URLs; IPv6 brackets survive redaction. Native two-client MCP reads
preserve all 3400 characters across 13 pages at ERROR/INFO/DEBUG log levels and
do not expose the synthetic query secret in Gateway stdout/stderr. The previous
response-limit/restart/cancellation native checks also pass. See
LOCAL-READER-POLICY-EVIDENCE-2026-09-03.md. Installed identity is proved separately
in the operator delivery record; no DSH/full-project completion is claimed.

September 3 source-only response-bound checkpoint: local/GitHub HTTP streaming,
per-response decoded-body caps and active request deadlines are implemented.
Local reads now share HTTP admission/origin pacing and cancellation. Native
disposable Gateway/two-MCP-client checks and a real unauthenticated GitHub API
check pass. This is not installed-service, authenticated-account or DSH proof.
See RESPONSE-BOUNDS-EVIDENCE-2026-09-03.md for exact runs and remaining limits.
This earlier source-only receipt is historical; subsequent installed identity
belongs to the latest operator reload/delivery record. Site v4 is still dated.

The owner-only landing page was republished on September 3 as Sites version 4,
source `b7bd4ff`, reflecting Gateway runtime `7cdfe72` and its 423-test CI proof.
It distinguishes native/installed/fake-vendor checks and explicitly marks the
DSH workflow and real-login/human-challenge/install gaps. Existing design and
access are unchanged. Publication is verified, not browser visual acceptance.
See SITE-EVIDENCE-ALIGNMENT-2026-09-03.md. This website/documentation checkpoint
does not change or restart Gateway or DSH; a later docs SHA is not a new runtime.

Recognized gate pages fail explicitly and auto public crawl reaches configured
Bright Data. Estimated-cost reservations, bounded streaming/deadlines and honest
redirect metadata have regressions. Native Chrome/network MCP with a public
header echo and local fake vendor proves two-client routing, 25-page fixture
reassembly and budget recovery after service reconstruction. No real vendor was
called. Human handoff, real login and CapSolver browser-token application remain
unfinished. Exact evidence: CHALLENGE-ROUTING-EVIDENCE-2026-09-02.md.

The first challenge-routing commit hook failed in the earlier cache concurrency
test. A real SQLite journal-mode initialization race was reproduced and repaired
without changing that test or the frozen cache/migration tests. Cache construction
now prepares WAL with bounded busy retries; requests do not reconfigure it. The
failure and subsequent verification belong to the challenge-routing evidence,
not the earlier cache checkpoint's green receipt.

Shared disk-cache capacity now applies atomically to every Gateway write, with
expiry/lowered-limit pruning on ordinary reads. Oversized source/job evidence stays
readable without advertising disk recovery. Positive limits and visible caps have
regressions; the low-level manual-eviction API remains compatible. The full local
gate passes 382 tests. Native two-client public fetches, actual eviction, process
restart and lowered limits pass. Physical SQLite/WAL size, synchronous I/O,
native memory and broad DSH acceptance remain open. See
CACHE-LIMITS-EVIDENCE-2026-09-02.md for baseline, assertion failures and exact results.

Transcript metadata-aware paging fixes the installed 2000-character rejection
and repeated-segment behavior. The first nine corrected assertion failures were
observed before implementation; focused regression and real native public-source
MCP now preserve text and timestamps at every supported budget and across a new
process/client. Cursor layout 3 rejects earlier layouts explicitly. Provider
5000-content-segment/200-structured-segment limits and unrelated oversized metadata
remain unchanged; this is not full source-size or DSH acceptance. Full local gate:
359 tests. Exact commands, test-author mistakes, native SDK error and corrected results are retained in
TRANSCRIPT-PAGING-EVIDENCE-2026-09-02.md.

Live authenticated MCP caught cursor-only requests being rejected at the interface
for deep research, transcripts and community search/threads. Four schemas/service
signatures are corrected; 29 new cases exercise all thirteen pageable readers,
missing-input errors and invalid cursors. Full local gate: 343 tests. Real native
MCP quota-driven Exa/DDGS fallback, authenticated GitHub discussion/nested replies
and commit-pinned content pagination pass in disposable instances. DSH was rerun
in session-21cc0995-f351-4d3e-ab03-7cac579cfd96 using its existing local Halo model:
the same prepare error occurs before any tool result; all 120 prior sessions remain.
No installed connection or DSH configuration was changed. Exact failures/results:
CURSOR-CONTRACT-AND-SOURCE-EVIDENCE-2026-09-02.md. Full acceptance remains open.

Immutable, bounded pagination snapshots prevent refreshed/provider-mutated results
from replacing existing cursor evidence. Count/byte/retention budgets and statistics
are implemented; disk recovery requires a matching hash and is absent for private
results. Formatter pagination retains collected snippet/content text, including at
2000 characters; oversized metadata fails explicitly. Final direct-HTTP/non-PDF
sensitive citations are redacted and not cached, with legacy namespaces bypassed.
Local full gate: 314 tests; separate native regression: 13 tests. A native Gateway/two-client/exact-local-HTTP fixture
proves lossless wire pages, shared eviction and private restart behavior; the
existing native job-crash canary still passes. Exact failures, limits and upgrade
behavior: RESULT-RETENTION-EVIDENCE-2026-09-02.md. This is not full DSH acceptance.

Crawl page/depth/site controls now govern collection; local wrapper controls and
option-specific cache keys are preserved. Scrolling is separate from navigation.
Partial failures/timeouts retain useful evidence, public navigation shares the
HTTP origin slot, managed public results bypass disk cache, and browser cleanup
survives repeated cancellation. Native Chrome fixtures prove dynamic multi-page
reading, path/scope and response-stage redirect checks, scroll/page limits and
owned-process exit, with existing cookie/HTTP/WebSocket fixtures retained. See
CRAWL-TRAVERSAL-EVIDENCE-2026-09-02.md for exact RED/GREEN and boundaries.
Unimplemented advanced interactions/captures/modes now return explicit errors;
their implementation remains open, alongside challenge escalation, DNS/OOPIF,
subresource scheduling/bytes, hard native memory and broad lifecycle acceptance.

Document table/OCR options now reach the provider and use distinct cache keys.
Native PDF tables retain page citations. English OCR, mixed text/image pages,
empty scans, process isolation, cancellation, input/output/raster/text limits,
page validation and verified local OCR-data setup have tests. Recognized sensitive
PDF redirects are redacted and bypass disk cache. Exact commands, outputs and
limits are in DOCUMENT-EXTRACTION-EVIDENCE-2026-09-02.md. The explicit native OCR
fixture invokes the real MCP dispatcher but replaces the download with generated
PDF bytes: it is not live-upstream, network-MCP or DSH acceptance. Advanced crawl
interactions/captures and sensitive intermediate-hop/embedded-URL handling remain open.

The background-launcher checkpoint passes 227 unit/fixture tests and two explicit
native lifecycle tests (one per PowerShell version). It fixes process identity,
duplicate startup, configured health/port and failed-launch cleanup without
restarting production Gateway or DSH. Exact RED/GREEN, baseline, security review,
and remaining foreground/logon/install limits are in
LAUNCHER-OWNERSHIP-EVIDENCE-2026-09-02.md. Commit/CI identity is recorded in the
operator checkpoint after delivery; these tests alone are not a CI claim.

The coordinator cancellation checkpoint adds seven deterministic cases (183
total passing tests) and a real loopback HTTPX cancellation/restart fixture.
New calls cannot inherit an abandoned flight, and cancellation cannot strand
queue settlement or waiter cleanup. The native job process-crash fixture was
rerun successfully. See COORDINATOR-CANCELLATION-EVIDENCE-2026-09-02.md for
RED/GREEN and exact limits; its deployment/CI identity is recorded separately.

Removal, retrieval repairs, active cancellation, DSH failure reporting, durable jobs and corrected documentation are pushed to private main through `b178cbe`; CI run 33697543325 passed for that exact revision. Gateway-only reload at 2026-09-02T23:59:44.28445Z passed live MCP smoke. Version remains 0.2.0; no new tag or PR merge is claimed. Later evidence-only commits require their own delivery receipt. See [progress](FINISH-PROGRESS-2026-09-02.md) for evidence by capability.

GitHub cursor/discussion/ref and exact local-browser/WebSocket repairs have tests; public-source live MCP/adapter probes returned useful evidence. A disposable real-Chrome v10 cookie-only login fixture passed. Real login/app-bound cookies, human challenge handling, optional-provider routing and complete DSH acceptance are not proved.

DSH failed before Gateway dispatch because host and agent-loop resolve distinct tools-package scheduler symbols. Repair/restart approval was requested; no DSH settings, packages, permissions, models, presets or existing conversations were changed. See [DSH failure evidence](DSH-WORKFLOW-CANCELLATION-2026-09-02.md).

Research-job controls stop the async worker, enforce admission/argument bounds, protect terminal states and preserve honest empty/partial outcomes. The continuation checkpoint adds saved sources/frontier, cumulative budgets, lease renewal and bounded pageable status. A native process-crash/restart fixture recovered evidence without repeating completed discovery/pages. After reload, a live Gateway MCP job passed pause/frozen-state/resume, budget and evidence-cursor checks. Broader provider cancellation (especially synchronous DDGS), DSH jobs, stress and foreground/logon/install remain unproved. See DURABLE-JOB-EVIDENCE-2026-09-02.md and LIVE-CHECKPOINT-2026-09-02.md.

The six-part [finish list](RESEARCH-ONLY-SCOPE.md#needs-to-be-done-to-finish) covers DSH, durable continuation, login/challenges, reliability/install, source-provider gaps and final website/delivery. No outbound actions or general personal-assistant features belong in it.
