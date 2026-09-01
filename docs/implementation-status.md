# Implementation status — 2026-09-01

This file distinguishes operational code from registered configuration and deferred adapter work. A tool appearing in MCP is not, by itself, proof that every upstream source or workflow is implemented deeply.

## Operational and proven locally

- One Streamable HTTP MCP process on loopback with all sixteen v1.5 tool names.
- Search using anonymous Exa when available and DDGS fallback on quota/failure.
- DNS-pinned direct fetch with original Host/TLS SNI, redirect revalidation, no environment proxies, public-address policy, bounded body size, cache, singleflight, per-origin concurrency, and pacing.
- Crawl4AI 0.9.x using a gateway-owned isolated Chrome profile; ordinary JavaScript extraction passes a live Windows canary.
- Reddit RSS search/thread and PDF extraction using PyMuPDF.
- Complete-envelope limits, signed cursor-only continuation, cache snapshot reuse, and tamper/expiry rejection.
- SQLite cache and durable provider budget/circuit state.
- DPAPI-encrypted generic API-key/token/password secret records; MCP returns only opaque metadata.
- OAuth 2.0 Authorization Code with PKCE using an ephemeral loopback callback, exact state validation, DNS-pinned token exchange, encrypted token storage, refresh locking, and operator-visible status.
- Explicit selected-category and complete Chrome-profile import into a gateway-owned destination, with a hash-bound preview, approval, closed-source-profile check, staged replacement, and redacted receipt.
- Exact configured local fetch/crawl target boundary.
- Finite durable deep-research jobs with create/status/pause/resume/cancel and crash recovery.
- Action preparation, local operator approval, immutable plan binding, idempotent receipts, and generic form POST execution without automatic retry.
- Windows Job Object containment with kill-on-close inheritance proof.
- Browser request routing validates public top-level, redirect, frame, and ordinary subresource HTTP(S) destinations; service workers and downloads are disabled for the gateway-owned Chrome process.
- Browser WebSocket handshakes are intercepted and checked by the same public/local destination policy. Gateway-owned imported profiles are now used as persistent Crawl4AI contexts rather than merely labeled in results; switching back to standard mode recreates an isolated context.
- Strict per-provider round-robin scheduling across configured `X-Halo-Client` buckets, FIFO within a client, singleflight before admission, per-client/global bounds, pacing, and queued cancellation. Unknown identities collapse to `unidentified`; the header grants no authority.
- `deep_research` honors pages/depth/sources/domain/freshness bounds, expands exact-host links breadth-first, canonicalizes URLs, deduplicates near-identical bodies, and preserves partial failures.
- Optional read-only GitHub App research uses short-lived installation tokens, current REST version headers, structured repository/path/SHA/issue metadata, single-mint locking, and public discovery fallback when no App is configured.
- Public transcript adapters normalize YouTube/HTML5 VTT, TTML/XML, and JSON3 captions without downloading media. Stack Exchange/Stack Overflow and Hacker News have bounded structured search/thread adapters; forums retain a Crawl4AI fallback.
- Gmail compose actions freeze exact MIME bytes/hashes and preserve distinct draft, draft-message, sent-message, and thread IDs. A separate GitHub Actions App supports reviewed issue/comment operations; edit/state changes are limited to Halo-receipted objects.
- Action execution reserves a plan durably before the upstream call. Concurrent different-key submissions run at most once; timeout/cancellation produces a secret-safe ambiguous receipt and is never automatically retried.
- Disabled-by-default CapSolver and Bright Data adapters enforce exact domains through the durable daily attempt/spend policy. No provider is enabled or charged by default.
- DSH planner integration and a real local-model call through `mcp__halo_research__web_search`.
- Claude Code and OpenCode registration; Codex config installed for the next process; LM Studio Bionic registration packaged by the installer.

## Present but intentionally partial

- GitHub discussions currently hand off to the authenticated adapter but disclose `GITHUB_KIND_UNSUPPORTED`; GraphQL discussion retrieval and exact non-default-ref code search remain partial.
- Caption support is public-caption only. It intentionally returns `TRANSCRIPT_UNAVAILABLE` rather than downloading audio/video for local speech-to-text.
- `deep_research` returns evidence, coverage, and warnings; the calling model still synthesizes the cited conclusion.
- Managed profile use is source- and fixture-proven. Scott has not selected/imported a personal Chrome profile or completed a live authenticated crawl in this release pass.
- WebSocket interception is implemented, but browser-level address pinning across Chromium's own DNS resolution remains an explicit hardening gap.
- CapSolver and Bright Data adapters are implemented behind disabled policy. Automatic challenge extraction/injection and the visible 120-second human challenge handoff are not yet acceptance-proven.

## Not implemented or not released

- Provider-side OAuth revocation calls. Generic PKCE/refresh/local revocation and a narrow Gmail compose preset are implemented.
- Live Chrome-profile import from Scott's personal profile. The mechanism is fixture-proven, but no personal data was copied without a separate operator choice.
- Live paid CAPTCHA/proxy credentials or calls. CapSolver and Bright Data adapters are code/test-proven only; no vendor, domain, or budget was selected.
- Authenticated Reddit actions. Reddit's current external-app path requires Scott's account/application choice; the release does not invent or bypass that grant.
- Purchase, account-security, deletion, and arbitrary site adapters beyond generic form submission, Gmail compose, and GitHub issue/comment operations.
- Complete browser-level DNS-rebinding pinning and a proven visible human challenge window.
- Hybrid content-addressed filesystem storage for large cache bodies; current payloads are compressed in SQLite.
- Universal structured request logging and negotiated-protocol telemetry.
- Live proof from LM Studio Bionic and a newly restarted Codex process.

Provider/site-specific credential and consequential-action work requires Scott to select the actual provider, scopes, import category, vendor, domain, and budget before live use.

## Release meaning

Halo Research Gateway 0.2.0 is the DSH-first release of the expanded research and operator-authorized action surface. Provider adapters and authority seams are implemented without enabling credentials or spend. Full specification v1.5 remains open on Scott-owned live grants/imports, authenticated Reddit, paid-provider canaries, the visible human-challenge proof, browser-level DNS pinning, and remaining fallback-host evidence.
