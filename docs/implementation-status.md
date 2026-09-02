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

Removal, retrieval repairs, active cancellation, DSH failure reporting and job controls are pushed to private main through `2aa748e`; CI run 33694089968 passed for that exact revision. Version remains 0.2.0; no new tag or PR merge is claimed. See [progress](FINISH-PROGRESS-2026-09-02.md) for evidence by capability.

GitHub cursor/discussion/ref and exact local-browser/WebSocket repairs have tests; public-source live MCP/adapter probes returned useful evidence. A disposable real-Chrome v10 cookie-only login fixture passed. Real login/app-bound cookies, human challenge handling, optional-provider routing and complete DSH acceptance are not proved.

DSH failed before Gateway dispatch because host and agent-loop resolve distinct tools-package scheduler symbols. Repair/restart approval was requested; no DSH settings, packages, permissions, models, presets or existing conversations were changed. See [DSH failure evidence](DSH-WORKFLOW-CANCELLATION-2026-09-02.md).

Research-job controls stop the async worker, enforce admission/argument bounds, protect terminal states and preserve honest empty/partial outcomes. The new continuation checkpoint adds saved sources/frontier, cumulative budgets, lease renewal and bounded pageable status. A native process-crash/restart fixture recovered evidence without repeating completed discovery/pages. Broader provider cancellation (especially synchronous DDGS), production/DSH jobs, stress and startup ownership remain unproved. See DURABLE-JOB-EVIDENCE-2026-09-02.md; source/test evidence requires a verified deployment before it applies to the live process.

The six-part [finish list](RESEARCH-ONLY-SCOPE.md#needs-to-be-done-to-finish) covers DSH, durable continuation, login/challenges, reliability/install, source-provider gaps and final website/delivery. No outbound actions or general personal-assistant features belong in it.
