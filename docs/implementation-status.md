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
