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
- DPAPI-encrypted generic API-key/token/password/OAuth-shaped secret records; MCP returns only opaque metadata.
- Exact configured local fetch/crawl target boundary.
- Finite durable deep-research jobs with create/status/pause/resume/cancel and crash recovery.
- Action preparation, local operator approval, immutable plan binding, idempotent receipts, and generic form POST execution without automatic retry.
- Windows Job Object containment with kill-on-close inheritance proof.
- DSH planner integration and a real local-model call through `mcp__halo_research__web_search`.
- Claude Code and OpenCode registration; Codex config installed for the next process; LM Studio Bionic registration packaged by the installer.

## Present but intentionally shallow

- `github_research` uses public web discovery constrained to GitHub, not the authenticated GitHub API.
- `transcript_fetch` can retrieve the page but has no universal media-caption adapter and reports `TRANSCRIPT_UNAVAILABLE` when appropriate.
- Community tools are source-routing wrappers, not authenticated community APIs.
- `deep_research` builds a bounded evidence packet; it does not return an uncited synthesized answer.
- Browser mode/profile fields are recorded, but stealth, undetected, managed-profile login, challenge handoff, screenshots, and PDFs are not all distinct proven execution paths.
- The operator console supports encrypted generic connections, state, jobs, plans, receipts, and exact action approval. It is not yet a full OAuth/profile-import wizard.

## Not implemented or not released

- Generic OAuth authorization-code/PKCE initiation, callback, refresh, provider discovery, and external revocation.
- Selected-category or full Chrome-profile import, including saved-password import.
- Paid CAPTCHA-solver and proxy-provider adapters, budgets, and receipts.
- Site-specific post, message, purchase, account-change, and delete execution adapters.
- Comprehensive Chromium subresource/frame/service-worker/WebSocket interception. Public top-level URL and redirect policy is enforced; this deeper browser boundary remains a documented hardening gap.
- Hybrid content-addressed filesystem storage for large cache bodies; current payloads are compressed in SQLite.
- Strict fair round-robin scheduling; queues are bounded per provider/client but are not a formal fairness scheduler.
- Universal structured request logging and negotiated-protocol telemetry.
- Live proof from LM Studio Bionic and a newly restarted Codex process.

Provider/site-specific credential and consequential-action work requires Scott to select the actual provider, scopes, import category, vendor, domain, and budget before live use.

## Release meaning

The DSH-first public research release is operational. Full v1.5 is not yet complete because provider-selected OAuth/import/paid-challenge/site-action adapters and deeper browser interception remain outstanding. The stable contracts and local operator authority seams are in place so those additions do not require redesigning DSH or the core service.
