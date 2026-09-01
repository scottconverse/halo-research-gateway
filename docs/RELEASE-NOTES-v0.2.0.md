# Halo Research Gateway 0.2.0 release notes

Halo Research Gateway 0.2.0 expands the deployed DSH-first research plane while preserving the localhost-only sixteen-tool contract and explicit operator authority boundary.

## Highlights

- Deep research now applies bounded breadth-first collection, freshness/domain/source controls, canonicalization, near-duplicate removal, and honest partial coverage.
- GitHub research can use a read-only GitHub App with short-lived installation tokens; public discovery remains available without credentials.
- Transcript and community tools now normalize public caption tracks, Stack Exchange, Hacker News, and bounded forum material without downloading audio or video.
- Gmail compose and GitHub issue/comment actions use narrow, separate identities and the existing preview/approval/receipt flow.
- Action execution reserves the plan durably before the upstream call, preventing duplicate execution across concurrent idempotency keys.
- Gateway-owned imported Chrome profiles are used by the crawler, and WebSocket handshakes pass through destination policy.
- CapSolver and Bright Data adapters are present but disabled until an operator selects credentials, domains, and budgets.
- DSH's no-reasoning picker opens directly to the model choices through a reproducible immutable package.

## Compatibility

- MCP result schema remains `1.5`.
- Database schema remains `3`; no new migration is required.
- The semantic MCP surface remains exactly sixteen tools.
- DSH remains the primary host; Codex, Claude Code, OpenCode, and LM Studio Bionic remain fallback hosts.

## Operator action required for live authenticated features

No credentials or personal browser data are enabled by upgrading. Use the loopback operator console to configure a Gmail OAuth client, read-only GitHub Research App, separate GitHub Actions App, selected Chrome import, Reddit application, or paid provider. Do not put secrets in prompts, TOML, Git, or release evidence.

## Known boundaries

- GitHub Discussions GraphQL and exact non-default-ref code search are partial.
- Captionless media does not trigger audio/video download or local speech-to-text.
- Chromium-level DNS pinning and the visible 120-second human-challenge acceptance path remain open.
- Authenticated Reddit actions, purchases, account-security changes, and deletion remain unreleased.
