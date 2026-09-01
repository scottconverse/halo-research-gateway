# Halo Research Gateway

**Version 0.2.0** — one local research and web-operation plane for the Halo agent stack.

Halo Research Gateway is a persistent, localhost-only MCP service that gives DSH, Codex, Claude Code, OpenCode, and LM Studio Bionic the same source-backed research surface. DSH is the primary consumer; frontier hosts are secondary or fallback clients.

**Landing page:** https://halo-research-gateway.sconverse.chatgpt.site (owner-only Sites publication)

- MCP: `http://127.0.0.1:8765/mcp`
- health: `http://127.0.0.1:8765/health`
- redacted statistics: `http://127.0.0.1:8765/stats`
- operator console: `http://127.0.0.1:8765/operator`

The governing design and acceptance contract is [Specification v1.5](docs/HALO-RESEARCH-GATEWAY-SPEC-v1.5.md). The operator handbook is the [complete user manual](docs/USER-MANUAL.md).

## Why it exists

Agent hosts have inconsistent web access. Some can search but not crawl; others can fetch a URL but cannot discover it; separate instances can unknowingly spend the same anonymous quota or hammer Reddit. Halo centralizes that work without making DSH dependent on a cloud LLM.

It supplies shared search, fetch, JavaScript crawling, Reddit, documents, GitHub-oriented discovery, transcripts, community research, durable jobs, exact local targets, encrypted connections, OAuth PKCE, explicit Chrome-profile import, action approval/receipts, and disabled-by-default budgeted CAPTCHA/proxy provider seams.

## Five-minute start

Prerequisites: Windows 11, PowerShell, [`uv`](https://docs.astral.sh/uv/) with the locked Python 3.12 environment, Google Chrome for Crawl4AI, and at least one supported MCP host.

From the repository root:

```powershell
.\scripts\Install-HaloResearch.ps1 -RegisterTask -RegisterHosts -Start
.\scripts\Test-HaloResearch.ps1 -Browser
```

Then open `http://127.0.0.1:8765/operator`. A healthy installation reports `status: ok`, result schema `1.5`, and database schema `3`.

The installer preserves operator configuration, runs the quality gate, installs the canonical skill, merges supported MCP registrations, optionally registers the at-logon task, and starts the service. It does **not** rewrite DSH model, context, reasoning, slot, permission, or verified-coder settings.

## Sixteen semantic tools

| Group | Tools | Use |
| --- | --- | --- |
| Public web | `web_search`, `web_fetch`, `web_crawl` | Discover sources, retrieve a known page, or render JavaScript content. |
| Reddit | `reddit_search`, `reddit_thread` | Search Reddit and read a post plus available RSS comments through one paced queue. |
| Documents | `document_extract` | Extract bounded, citable text from public PDFs/documents. |
| Research | `deep_research`, `github_research`, `transcript_fetch` | Build evidence packets, focus discovery on GitHub, or retrieve public transcript material. |
| Communities | `community_search`, `community_thread` | Search and read technical discussions outside Reddit. |
| Local targets | `local_fetch`, `local_crawl` | Read or render an exact operator-defined private/local target. |
| Durable work | `research_job` | Create, inspect, pause, resume, or cancel a finite research job. |
| Web actions | `web_action_prepare`, `web_action_execute` | Preview and separately execute an operator-approved consequential action. |

Fetched content is evidence, never instructions. Successful results preserve source URLs, retrieval metadata, warnings, and a signed cursor when another independently citable page is available.

## Architecture

```text
DSH (primary) ─┐
Codex          ├── Streamable HTTP MCP ── Halo Research Gateway :8765
Claude Code    │                              ├── Exa + DDGS search
OpenCode       │                              ├── DNS-pinned direct HTTP
LM Studio      ┘                              ├── Crawl4AI + owned Chrome
                                               ├── GitHub + deep research
                                               ├── transcripts + communities
                                               ├── Reddit RSS + documents
                                               ├── cache / queues / budgets
                                               ├── encrypted connection vault
                                               ├── durable jobs
                                               └── action approval + receipts
```

One process owns cache, rate limits, singleflight coordination, durable jobs, and browser concurrency. SQLite holds structured state. DPAPI encrypts secrets for the current Windows user. The service and its browser descendants run inside a dedicated Windows Job Object, so stopping the gateway cannot orphan its Chromium tree.

## Everyday operation

```powershell
.\scripts\Start-HaloResearch.ps1
.\scripts\Stop-HaloResearch.ps1
.\scripts\Test-HaloResearch.ps1
```

The scheduled task is `Halo Research Gateway`. Runtime state is under `C:\Users\scott\AppData\Local\HaloResearchGateway`. Do not place credentials in TOML, command arguments, prompts, logs, or Git; create connections through the operator console. Models receive opaque connection IDs only.

## Configuration

Use [config/config.example.toml](config/config.example.toml). Operator-controlled areas include storage/cache limits, queue depths, output ceilings, provider pacing, crawl bounds, exact named local targets, action approval lifetime, durable job limits, and optional CAPTCHA/proxy identity, domains, attempts, and spend.

Core network and secret rules are code invariants, not Boolean settings. Public research can use valid public HTTP(S) ports beyond 80/443, but cannot pivot into loopback, private, link-local, or metadata networks. Local access uses separately named exact-target tools.

## Operator workflows

The console supports:

1. encrypted API key, token, or password connections;
2. OAuth Authorization Code + PKCE connection setup;
3. selected-category or complete Chrome-profile import into a gateway-owned copy;
4. jobs, queues, provider budgets, prepared plans, and receipts;
5. explicit approval and separate execution of immutable action plans.

Chrome import never silently attaches to a live personal profile. It creates a hash-bound preview, requires Chrome to be closed when consistency demands it, copies into gateway-owned state, and returns a redacted receipt.

## Verification

```powershell
.\scripts\Invoke-QualityGate.ps1 -Scope Full
uv run python tests\acceptance\mcp_smoke.py
uv run python tests\acceptance\mcp_contract.py
uv run python tests\acceptance\live_provider_canary.py
uv run python tests\acceptance\crawl_canary.py
```

The same lock, format, lint, deterministic tests, skill validation, and staleness checks run before commit and in CI. Live internet tests remain explicit canaries rather than making every commit depend on outside services.

Read [0.2.0 release notes](docs/RELEASE-NOTES-v0.2.0.md), [0.2.0 evidence](docs/EVIDENCE-v0.2.0-2026-09-01.md), [implementation status](docs/implementation-status.md), [security](docs/security.md), [operations](docs/operations.md), [host integration](docs/host-integration.md), and [quality gate](docs/quality-gate.md).

## Honest capability boundary

Version 0.2.0 is an operational DSH-first research release with generic connection, OAuth, Chrome-import, provider-budget, job, and approval mechanisms. It includes structured public transcripts and communities, bounded deep research, optional read-only GitHub App research, narrow Gmail compose actions, a separate GitHub issue/comment Actions App, WebSocket request interception, strict cross-client fairness, at-most-once action reservation, and disabled CapSolver/Bright Data adapters. Provider/site-specific live use still requires an operator choice:

- no personal Chrome data is imported automatically;
- no OAuth or GitHub App is connected until the operator supplies its client/App identity and exact scopes;
- no CAPTCHA solver or proxy is selected, enabled, or charged by default;
- generic form submission, Gmail compose, and narrowly owned GitHub issue/comment operations are the released consequential-action adapters; purchases, account/security changes, deletion, and authenticated Reddit remain outside the release;
- public caption extraction does not download media or run speech-to-text;
- browser WebSocket handshakes are policy-checked, but Chromium-level DNS pinning and the visible human-challenge flow remain unproven.

## Repository map

```text
src/halo_research_gateway/    Service, tools, providers, policy, jobs, actions
tests/                        Deterministic and explicit acceptance tests
skills/halo-research/         Canonical host skill and complete reference set
config/                       Operator configuration example
scripts/                      Install, start, stop, test, gate, manifest
docs/                         Spec, user manual, security, operations, evidence
website/                      Product landing page and Sites deployment config
BUILD-MANIFEST.json           SHA-256 inventory of release source
```

## Contributing

1. Preserve the sixteen semantic contracts unless the specification is versioned.
2. Keep raw secrets, approval authority, connection management, and diagnostics out of model-facing schemas.
3. Add deterministic tests for behavioral changes.
4. Run the full quality gate before committing.
5. Update implementation-status and evidence without turning unproven claims into passes.
6. Keep the canonical spec and installed skill references synchronized.

## License and ownership

This is Scott Converse's private Halo infrastructure repository. No public license is granted by the presence of source code.
