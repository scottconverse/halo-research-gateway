# Changelog

All notable Halo Research Gateway product releases are recorded here.

## Unreleased — research-only scope correction (2026-09-02)

- Stream local HTTP and GitHub API responses instead of buffering whole downloads. Apply the configured decoded-body cap and per-request deadline, including GitHub DNS. Local fetches now use shared HTTP admission, cancellation and per-origin pacing. Preserve ordinary evidence/pagination; return precise oversize/timeout errors without partial evidence. This source-only checkpoint does not restart the installed service or claim total process-memory bounds.

- Align the owner-only landing page with the September 3 verified runtime checkpoint: replace stale test counts, distinguish installed/native/fake-vendor evidence, link exact CI and the research-only finish list, and prominently disclose the blocked DSH workflow. Preserve design, access and product version 0.2.0; this is not full acceptance or a new package release.

- Fix a cache-locking race exposed by the challenge-routing commit gate: prepare SQLite WAL before requests instead of changing journal mode during normal traffic. Bound simultaneous initialization waits; preserve existing eviction/concurrency assertions and database migration behavior.

- Reject recognized challenge pages as evidence and connect auto public crawling to the existing disabled-by-default Bright Data adapter. Preserve earlier sources on later failures; do not outsource managed/private/sensitive sessions. Require positive operator request-cost estimates, reserve rounded-up cost atomically and label it estimated. Request structured JSON by default while retaining raw support; bound streaming responses and total API/solver time. Native Chrome/network MCP/local fake-vendor checks pass without paid calls. Human handoff, CapSolver browser-token application and live paid acceptance remain unfinished; unverified vendor final redirects are explicit.

- Enforce shared compressed cache capacity atomically on every Gateway write; ordinary cache hits/misses also remove expired and over-limit rows. Reject nonpositive limits, expose configured limits in statistics, and reconcile previously oversized entries after lowering limits. Oversized research/job results remain readable with `RESULT_NOT_CACHED_TOO_LARGE` and no disk-recovery key. Native two-client/restart/lowered-limit checks pass. Physical SQLite/WAL size, synchronous cache I/O, broader source bounds and DSH acceptance remain separate.

- Page retained transcript timing metadata and long caption text without loss or repeated segments. Preserve citations, timestamp values, empty timing records and explicit fragment offsets at every supported output size. Native public-source MCP and process/client restart prove identical evidence at 2000/4000/6000 characters. Cursor layout 3 rejects older cursors explicitly; restart the original request. Provider collection limits and unrelated oversized metadata remain unchanged.

- Fix MCP cursor-only continuation for deep research, transcripts and community search/threads; initial requests still require their starting question/query/URL. Add all-reader regression coverage and explicit native live scripts for real Exa-to-DDGS quota fallback and authenticated GitHub discussion/nested-reply/ref pagination. Fresh DSH acceptance still fails before dispatch; no DSH settings, models or permissions changed.

- Bind pagination to immutable evidence; keep collected text across bounded pages instead of trimming it away or repeating snippets. Bound retained snapshots by count, serialized bytes and idle age, expose usage, and reject oversized/unavailable results explicitly. Public disk continuation requires the original content hash; private results cannot recover old disk entries. Redact recognized sensitive final direct-HTTP/non-PDF citation URLs and bypass legacy fetch/document cache namespaces. Old cursors need a fresh request; durable jobs and historical data remain intact. Total native/process memory, broader source limits and full DSH acceptance remain separate.

- Make crawl page/depth limits perform real traversal, preserve site scope and option-specific caches, and separate bounded scrolling from page count. Retain good evidence across failed/empty/timeout pages, share public navigation's HTTP origin slot, close owned browsers reliably, and keep managed public results out of disk cache. Check HTTP redirects at Chromium's response stage before following them; preserve final citation URLs and redact recognized sensitive citation query values. Unimplemented advanced interactions, captures and anti-bot modes now fail explicitly and remain unfinished research work. No account actions or general submissions added.

- Honor document table/OCR options through MCP, service and option-specific cache keys. Return page-cited native PDF tables and local English OCR; reject unsupported page selections and forced OCR on non-PDF sources. Bound parser input/output, page/image/text/table work, isolate parsing in a cancellable native child, and redact recognized sensitive PDF redirect URLs while bypassing disk caching. Setup installs pinned, size/SHA-verified English language data and license; no cloud OCR or virtualization. Full DSH, arbitrary scan/layout, native peak-memory and clean-install acceptance remain separate.

- Fix background launcher ownership: serialize simultaneous start/stop, validate repository/executable/module/creation time, retain a process handle through stop, refuse unrelated listeners, honor the configured port/health path, and clean up a failed new launch. Mismatched existing instances are left untouched. Native disposable start/stop/restart passed in Windows PowerShell and PowerShell 7; foreground, logon and clean-install acceptance remain separate.

- Remove Gmail compose/draft/send, GitHub issue/comment writes, general form submission, the two action MCP tools, and the general action approval endpoint/UI.
- Remove full/personal Chrome import; retain cookie-only research sessions and their import-specific review/receipts.
- Preserve existing runtime data and historical receipts; old action plans cannot execute through import review.
- Correct current documentation and agent instructions. DSH native permissions are unchanged.
- Fix GitHub fallback cursor continuation and exact-target local browser/WebSocket request checks.
- Fix Exa text-result attribution so each excerpt stays with its own URL; unidentified text yields discovery links only. Apply domain filters to Exa and route freshness/non-web requests to the provider that accepts those controls.
- Route Reddit RSS through bounded HTTP retrieval and persist rate-limit backoff with visible retry delays.
- Cancel an active retrieval when its last caller leaves, while preserving reads still needed by another caller. The DSH acceptance runner now rejects an errored completed turn.
- Fix cancellation races: new callers cannot join a stopping read, completed/cancelled providers release their queue slots, and repeated caller cancellation cannot interrupt waiter cleanup. A stopping provider retains its active slot until it exits.
- Make research-job pause/cancel stop the async worker; enforce positive limits and shared admission, reject invalid resume transitions, and keep late failures from overwriting paused/cancelled records. Empty retrieval is failed and partial evidence is marked.
- Persist completed/remaining research sources, cumulative attempt/time budgets and renewable job leases. Resume retains evidence across process interruption; status returns bounded evidence pages with cursors. Checkpoint overflow fails explicitly, and recognized sensitive source/link URLs are excluded from durable storage. Full DSH/provider stress acceptance remains separate from the native restart fixture.
- Fix cookie-only research-session reuse: closed Chrome's stale database LOCK file no longer falsely blocks import, and installed Chrome loads the encrypted copy before an in-memory handoff to the research context.
- Add authenticated read-only GitHub discussion search/thread retrieval, bounded nested replies, and branch/tag/commit-pinned documentation/code retrieval. Operator token connections now work as well as GitHub Apps.
- See [current scope and remaining acceptance](docs/RESEARCH-ONLY-SCOPE.md). Entries below describe historical releases, not the current capability contract.

## 0.2.0 — 2026-09-01

### Added

- Strict per-provider round-robin scheduling across declared client profiles, FIFO ordering within a client, bounded admission, and cancellation cleanup.
- Bounded deep research with exact-host breadth-first expansion, freshness/domain/source controls, URL canonicalization, near-duplicate removal, and partial-failure evidence.
- Optional read-only GitHub App research with short-lived installation tokens and structured repository, code, issue, commit, release, and documentation metadata.
- Public YouTube/HTML5 VTT, TTML/XML, and JSON3 transcript extraction without media downloads.
- Structured Stack Exchange and Hacker News research, plus bounded forum fallback.
- Narrow Gmail compose draft/send actions and a separate GitHub Actions App for approved issue/comment operations.
- Durable at-most-once action reservation with immutable ambiguous receipts after timeout or cancellation.
- Gateway-owned imported Chrome profiles, WebSocket destination interception, and disabled service workers/downloads.
- Disabled-by-default CapSolver and Bright Data Web Unlocker adapters with exact-domain and durable attempt/spend enforcement.
- Direct-open DSH model picker package and recovery evidence.

### Proven before release

- 128 deterministic unit/fixture tests and the full Windows quality gate.
- Loopback-only service recovery through the registered Windows task.
- Sixteen-tool MCP surface and live public fetch.
- DSH picker behavior and an earlier DSH planner `web_search` selection.

### Known boundaries

- Gmail, GitHub, Reddit, personal Chrome import, and paid-provider live use still require operator-owned credentials or choices.
- GitHub Discussions GraphQL, captionless-media speech-to-text, Chromium-level DNS pinning, and the visible human-challenge flow remain open work.
- Paid adapters remain disabled until the operator supplies credentials, exact domains, and budgets.
