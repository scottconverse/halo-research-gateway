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
- Disabled-by-default CAPTCHA/proxy provider seams enforce exact domains and durable daily attempt/spend ceilings. A missing adapter cannot consume budget, and credentials remain opaque DPAPI-vault references.
- DSH planner integration and a real local-model call through `mcp__halo_research__web_search`.
- Claude Code and OpenCode registration; Codex config installed for the next process; LM Studio Bionic registration packaged by the installer.

## Present but intentionally shallow

- `github_research` uses public web discovery constrained to GitHub, not the authenticated GitHub API.
- `transcript_fetch` can retrieve the page but has no universal media-caption adapter and reports `TRANSCRIPT_UNAVAILABLE` when appropriate.
- Community tools are source-routing wrappers, not authenticated community APIs.
- `deep_research` builds a bounded evidence packet; it does not return an uncited synthesized answer.
- Browser mode/profile fields are recorded, but stealth, undetected, managed-profile login, challenge handoff, screenshots, and PDFs are not all distinct proven execution paths.
- The operator console supports encrypted generic connections, OAuth/PKCE connection flow, Chrome import previews and separately approved execution, state, jobs, plans, receipts, and exact action approval.

## Not implemented or not released

- Vendor-specific OAuth discovery presets and external-provider revocation calls. The generic standards-based flow, refresh, and local revocation boundary are implemented.
- Live Chrome-profile import from Scott's personal profile. The mechanism is fixture-proven, but no personal data was copied without a separate operator choice.
- Vendor-specific paid CAPTCHA-solver and proxy adapters. Their disabled configuration seams, exact-domain policy, encrypted connection reference, durable budgets, and visible usage state are implemented; no vendor or spend was selected.
- Site-specific post, message, purchase, account-change, and delete execution adapters.
- Complete Chromium WebSocket and DNS-rebinding pinning. Playwright routing now covers top-level, redirects, frames, and ordinary subresources, and service workers/downloads are disabled; WebSocket handshake interception and browser-level address pinning remain disclosed hardening gaps.
- Hybrid content-addressed filesystem storage for large cache bodies; current payloads are compressed in SQLite.
- Strict fair round-robin scheduling; queues are bounded per provider/client but are not a formal fairness scheduler.
- Universal structured request logging and negotiated-protocol telemetry.
- Live proof from LM Studio Bionic and a newly restarted Codex process.

Provider/site-specific credential and consequential-action work requires Scott to select the actual provider, scopes, import category, vendor, domain, and budget before live use.

## Release meaning

The DSH-first public research release is operational. Full provider-specific v1.5 is not yet complete because Scott has not selected actual OAuth services, a personal Chrome import, CAPTCHA/proxy vendors, or site-specific consequential-action adapters. The generic mechanisms and authority seams are implemented, so those choices do not require redesigning DSH or the core service.
