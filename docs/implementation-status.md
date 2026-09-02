# Implementation status — 2026-09-02

Current scope is [research-only](RESEARCH-ONLY-SCOPE.md). Previous 0.2.0 receipts describe older code, not proof of full current acceptance.

## Current code

Fourteen research MCP tools: discovery/fallback, direct fetch, JavaScript crawl, Reddit, PDF/documents, deep research, read-only GitHub, transcripts, communities, exact local targets, and bounded research jobs. Shared caching/queues, encrypted research connections, OAuth, and optional disabled challenge/proxy adapters remain.

Removed: Gmail, GitHub writes, general form submission, general action preparation/approval/execution, and broad personal Chrome import. Cookie-only research-session import has its own review route. Old data and receipts are preserved; legacy actions cannot execute there.

## Evidence for this revision

The untouched baseline passed 128 tests. Nine new scope assertions failed on the unwanted features before removal. The first post-removal unit/fixture run passed 124 tests; the count falls because tests exercising intentionally removed features were replaced with removal checks. Final gate/deployment evidence is recorded separately; these counts do not prove DSH, live accounts, or paid-provider use.

## Still required

The final gate passed `131 passed in 3.98s`. The live service exposes fourteen tools, public fetch passed, and the retired action approval endpoint returns 404. See [removal evidence](RESEARCH-ONLY-REMOVAL-EVIDENCE-2026-09-02.md). These are not end-to-end DSH or live-account acceptance claims.

Use the six-part [finish list](RESEARCH-ONLY-SCOPE.md#needs-to-be-done-to-finish): finish removal delivery; fix retrieval defects; prove source tools; prove research login/challenges; prove an end-to-end DSH workflow; finish reliability and release evidence. No outbound actions or general personal-assistant features belong in that list.

Known research gaps include GitHub cursor identity and discussion/ref coverage, local-browser request/WebSocket handling, imported-profile/Chrome encryption compatibility, visible human challenge handling, paid adapter routing, full multi-step DSH acceptance, and concurrency/recovery evidence. Do not label these complete based on isolated unit tests or old receipts.
