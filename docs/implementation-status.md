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
