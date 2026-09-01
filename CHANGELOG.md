# Changelog

All notable Halo Research Gateway product releases are recorded here.

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
