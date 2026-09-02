# Changelog

All notable Halo Research Gateway product releases are recorded here.

## Unreleased — research-only scope correction (2026-09-02)

- Remove Gmail compose/draft/send, GitHub issue/comment writes, general form submission, the two action MCP tools, and the general action approval endpoint/UI.
- Remove full/personal Chrome import; retain cookie-only research sessions and their import-specific review/receipts.
- Preserve existing runtime data and historical receipts; old action plans cannot execute through import review.
- Correct current documentation and agent instructions. DSH native permissions are unchanged.
- Fix GitHub fallback cursor continuation and exact-target local browser/WebSocket request checks.
- Fix Exa text-result attribution so each excerpt stays with its own URL; unidentified text yields discovery links only. Apply domain filters to Exa and route freshness/non-web requests to the provider that accepts those controls.
- Route Reddit RSS through bounded HTTP retrieval and persist rate-limit backoff with visible retry delays.
- Cancel an active retrieval when its last caller leaves, while preserving reads still needed by another caller. The DSH acceptance runner now rejects an errored completed turn.
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
