# Halo Research Gateway 0.2.0 evidence — 2026-09-01

This release record separates deterministic, deployed, DSH, website, and external-release evidence. It records the source-wired and live proofs that existed before the final release tag was created; the tag target, exact-commit Windows CI result, and GitHub Release are the authoritative publication receipts.

## Deterministic implementation

- Source implementation commit `0a4d799e92c2a41c3cd00d8f73eac7596dd72c96` introduced the expanded provider/action surface.
- Release-candidate commit `37a1d4b9d2f542e365709fe689abe5580494b5cf` aligned product, runtime, package, website, manual, and manifest metadata on `0.2.0`.
- The pre-release source gate passed 128 deterministic unit/fixture tests, lock validation, Ruff format/lint, canonical skill validation, and the staleness guard.
- Windows CI runs `33570287242` and `33570439348` passed on the implementation and evidence commits respectively.

## Deployed Gateway

- The ownership-checked Windows service restart loaded version `0.2.0` without changing model aliases, DSH route settings, or unrelated services.
- `GET /health` returned `status: ok`, `version: 0.2.0`, result schema `1.5`, database schema `3`, ready search/HTTP/Reddit/vault/action subsystems, zero queued/running jobs, and paid optional providers disabled.
- The live MCP acceptance script completed against `http://127.0.0.1:8765/mcp`: 16 tools listed and `web_fetch` returned `ok` with 1,381 characters.

## Current DSH end-to-end acceptance

- Fresh DSH session: `session-c0854553-e24a-42d4-ab2a-8b09889f229b`, preset `halo-orchestrator`.
- Actual model route reported by DSH: provider `lmstudio`, model `unsloth/qwen3.8-27b`, context 32,768. This records the current configured route; it does not claim a different historical alias.
- The model made exactly one research call: `mcp__halo_research__deep_research` with domain `modelcontextprotocol.io`, `max_sources: 2`, `max_pages: 2`, `max_depth: 0`, and `max_chars: 2000`.
- The Gateway returned schema `1.5`, `ok: true`, tool `deep_research`, provider `halo-deep`, request ID `c07183d5-8c21-42f2-94ad-628051d2025c`, and one citable official architecture result from `https://modelcontextprotocol.io/docs/2026-07-28/learn/architecture`.
- The bounded result honestly reported `DEPTH_LIMIT_REACHED`, `PROVIDER_FALLBACK_USED`, and `RESULT_TRUNCATED`; those warnings did not invalidate the requested one-source acceptance condition.
- DSH completed the turn with the exact marker `HALO-GATEWAY-0.2.0-DSH-OK https://modelcontextprotocol.io`.

## Landing page

- `npm run lint` and the five-stage Vinext production build passed from the committed website source.
- Website-only source commit `81acf3b68c818b3f44b813e615d102444257a273` was pushed to the existing Sites source repository.
- The packaged build contained 71 files, 2,775,040 bytes, with content hash `sha256:927030ec9e451e8bc567e8841d560e8da7119066aa925b22cccf16c5180a242a`.
- Owner-only Sites version 2 (`appgver_7e28829881b88191b30be4e67637d84e`) deployed successfully as deployment `appgdep_6a9768153da08191a5705aa2ff20b106` at `https://halo-research-gateway.sconverse.chatgpt.site`.
- Access was verified as custom owner-only: the signed-in owner was the sole allowed account, no groups were allowed, and there were zero external visitors.
- An authenticated in-app-browser render verified the `Halo Research Gateway 0.2.0` title, `v0.2.0` label, primary hero, 16-tool/128-test proof, and the documented GitHub, captions, WebSockets, queues, Gmail, CapSolver, and Bright Data boundaries.

## Final publication contract

- The annotated `v0.2.0` tag and GitHub Release target the final documentation commit on `main` only after the Windows quality-gate workflow passes for that exact commit.
- The GitHub tag, Release page, and workflow run are the external receipts for publication because a commit cannot embed its own object ID or the future CI run ID without changing that identity.
- The companion DSH picker/documentation commits remain local because `C:\Users\scott\Desktop\Code\dsh-halo-research` has no configured Git remote; no remote repository was invented for this release.

## Boundaries not claimed by 0.2.0

- No live Gmail/GitHub/Reddit credential grant, personal Chrome import, or paid-provider call is claimed.
- No captionless-media speech-to-text, Chromium-level DNS pinning, visible human-challenge proof, or arbitrary consequential-action adapter is claimed.
