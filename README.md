# Halo Research Gateway

**Version 0.2.0** — one local search and research service for the Halo agent stack.

Halo Research Gateway is a persistent, localhost-only MCP service that gives DSH, Codex, Claude Code, OpenCode, and LM Studio Bionic the same source-backed research surface. DSH is the primary consumer; frontier hosts are secondary or fallback clients.

**Landing page:** https://halo-research-gateway.sconverse.chatgpt.site (owner-only Sites publication)

The published page was aligned on September 3 with verified runtime checkpoint
`7cdfe72`: 423 local/CI regression tests, separately labeled installed/native
checks, and explicit unfinished DSH/login/provider/install work. This is a
dated evidence snapshot, not a live dashboard or full-acceptance claim. See
[publication evidence](docs/SITE-EVIDENCE-ALIGNMENT-2026-09-03.md).

- MCP: `http://127.0.0.1:8765/mcp`
- health: `http://127.0.0.1:8765/health`
- redacted statistics: `http://127.0.0.1:8765/stats`
- operator console: `http://127.0.0.1:8765/operator`

The governing product scope and finish list are [Research-only scope](docs/RESEARCH-ONLY-SCOPE.md); this supersedes conflicting requirements in the original v1.5 design. The operator handbook is the [complete user manual](docs/USER-MANUAL.md).

Current acceptance is partial. The DSH tools-package mismatch was repaired on September 3 without changing models, presets, permissions or existing conversations. Real DSH search, multiple source reads and one exact-cursor continuation now dispatch successfully. The broad run nevertheless timed out without a final answer, after repeated token-copy errors and compaction; it is not a workflow pass. The acceptance checker now requires successful returned evidence, an actually issued continuation and distinct source pages. See [DSH repair and acceptance evidence](docs/DSH-RESOLUTION-EVIDENCE-2026-09-03.md). Real login, optional paid-provider use and wider installation/stress checks remain separately unproved. The final target is `0.3.0`, but it has not been released or tagged.

## Why it exists

The source now streams local HTTP and GitHub API responses with the configured
decoded-body limit and per-request deadline. Local reads also share HTTP admission
and per-origin pacing. Oversize/timeout failures return no partial source as
successful evidence. Native two-client local reads and unauthenticated GitHub
checks pass. These response bounds were introduced in `a640549`; source/native
evidence is separate from the later installed-service reload receipt. The
published page remains a dated `7cdfe72` snapshot. See
[response-bound evidence and limits](docs/RESPONSE-BOUNDS-EVIDENCE-2026-09-03.md).

Local GET reads now enforce the operator's allowed methods before contacting a
source. Recognized session-query values are used only for the source request,
then redacted from citation URLs and continuation snapshots. IPv6 citations keep
their brackets. Native MCP checks preserve complete source text and verify no
synthetic query secret in Gateway output at ERROR/INFO/DEBUG log levels. See
[local policy evidence and limits](docs/LOCAL-READER-POLICY-EVIDENCE-2026-09-03.md).

Recognized challenge pages no longer count as research evidence. Auto public
crawling can use configured Bright Data retrieval with exact requested-domain
checks and reserved attempt/cost budgets. Native Chrome/two-client MCP tests
use a public header echo and local fake vendor, not a paid endpoint. See
[challenge routing evidence](docs/CHALLENGE-ROUTING-EVIDENCE-2026-09-02.md).

The operator can now open a public research page in an isolated visible browser,
complete a login/challenge, then retain temporary cookies for a managed-profile
retry. No model click/form API is added. The two-minute flow and controlled
Chrome fixture pass; real-account, installed and DSH acceptance are separate.
Cookies stay in memory and the imported profile is not updated. See the
[plain-English instructions](docs/USER-MANUAL.md#human-login-or-challenge-handoff)
and [exact evidence and limits](docs/HUMAN-HANDOFF-EVIDENCE-2026-09-03.md).

Ordinary research traffic now keeps the shared disk cache within its configured
compressed-payload limits. Expired or over-limit entries are removed atomically;
results too large to save remain readable with an explicit uncached warning.
Two native clients and restart/lowered-limit tests pass. This does not bound the
physical database file or total process memory. See
[cache-limit evidence and operating limits](docs/CACHE-LIMITS-EVIDENCE-2026-09-02.md).
The later challenge-routing commit gate exposed a cache journal-initialization
race. Cache setup now completes before requests, with bounded startup contention;
ordinary reads and writes no longer attempt to change the journal mode.

Transcript timing metadata now continues across bounded pages instead of making
short captions fail or repeating every segment. Native MCP returns identical
text and timestamps at 2000/4000/6000 characters and after process/client restart.
Older cursor layouts require a fresh request; no jobs or source data are deleted.
See [transcript paging evidence and limits](docs/TRANSCRIPT-PAGING-EVIDENCE-2026-09-02.md).

All thirteen pageable readers now accept cursor-only continuation, including
transcripts, communities and deep/job evidence. Native MCP checks prove real
Exa-to-DDGS quota fallback and authenticated public GitHub discussion/nested-reply/
commit-pinned document pagination in disposable instances. The September 3 DSH
repair restores dispatch, but a complete workflow remains a separate check. See
[cursor and source evidence](docs/CURSOR-CONTRACT-AND-SOURCE-EVIDENCE-2026-09-02.md).

Continuation now binds immutable evidence and retains all collected prose across
bounded output pages. Refreshed sources cannot silently replace an older cursor's
evidence. In-memory snapshots have configurable count/byte/idle-retention limits
and visible statistics; unavailable snapshots fail explicitly. Recognized sensitive
final direct-HTTP/document URLs are redacted and bypass disk cache. See
[retention evidence and upgrade limits](docs/RESULT-RETENTION-EVIDENCE-2026-09-02.md).

Browser crawling now follows a bounded page/depth frontier, returns each source
with its own citation, distinguishes scrolling from page traversal, and retains
usable pages when another fails. Native Chrome fixtures cover redirect checks,
exact local paths, scrolling, cookie reuse, WebSockets and cancellation cleanup.
Advanced interactions/captures and real-account human challenge acceptance remain open;
unimplemented options return explicit errors. See [crawl evidence and limits](docs/CRAWL-TRAVERSAL-EVIDENCE-2026-09-02.md).

Agent hosts have inconsistent web access. Some can search but not crawl; others can fetch a URL but cannot discover it; separate instances can unknowingly spend the same anonymous quota or hammer Reddit. Halo centralizes that work without making DSH dependent on a cloud LLM.

It supplies shared search, fetch, JavaScript crawling, Reddit, documents, GitHub-oriented discovery, transcripts, community research, durable jobs, exact local targets, encrypted connections, OAuth PKCE, cookie-only research-session import, and disabled-by-default budgeted CAPTCHA/proxy provider seams.

## Quick start

Prerequisites: Windows 11, PowerShell, [`uv`](https://docs.astral.sh/uv/) with the locked Python 3.12 environment, Google Chrome for Crawl4AI, and at least one supported MCP host.

From the repository root:

```powershell
.\scripts\Install-HaloResearch.ps1 -RegisterTask -RegisterHosts -Start
.\scripts\Test-HaloResearch.ps1 -Browser
```

Then open `http://127.0.0.1:8765/operator`. A healthy installation reports `status: ok`, result schema `1.5`, and database schema `3`.

The installer preserves operator configuration, runs the quality gate, installs the canonical skill, merges supported MCP registrations, optionally registers the at-logon task, and starts the service. It does **not** rewrite DSH model, context, reasoning, slot, permission, or verified-coder settings.

PDF reading uses the existing PyMuPDF dependency. Setup also verifies and installs pinned English OCR data and its license inside `.venv/share/tessdata`; reading scanned PDFs stays local, without WSL, a separate OCR application, or a paid service. See [document options and limits](docs/USER-MANUAL.md#pdf-text-tables-and-local-ocr) and [document verification](docs/DOCUMENT-EXTRACTION-EVIDENCE-2026-09-02.md).

## Fourteen research tools

| Group | Tools | Use |
| --- | --- | --- |
| Public web | `web_search`, `web_fetch`, `web_crawl` | Discover sources, retrieve a known page, or render JavaScript content. |
| Reddit | `reddit_search`, `reddit_thread` | Search Reddit and read a post plus available RSS comments through one paced queue. |
| Documents | `document_extract` | Extract bounded, citable text from public PDFs/documents. |
| Research | `deep_research`, `github_research`, `transcript_fetch` | Build evidence packets, retrieve read-only GitHub evidence, or retrieve public transcript material. |
| Communities | `community_search`, `community_thread` | Search and read technical discussions outside Reddit. |
| Local targets | `local_fetch`, `local_crawl` | Read or render an exact operator-defined private/local target. |
| Durable work | `research_job` | Create, inspect, pause, resume, or cancel a finite research job. |

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
                                               └── durable research jobs
```

One process owns cache, rate limits, singleflight coordination, durable jobs, and browser concurrency. SQLite holds structured state. DPAPI encrypts secrets for the current Windows user. The service and its browser descendants run inside a dedicated Windows Job Object, so stopping the gateway cannot orphan its Chromium tree.

## Everyday operation

```powershell
.\scripts\Start-HaloResearch.ps1
.\scripts\Stop-HaloResearch.ps1
.\scripts\Test-HaloResearch.ps1
```

The scheduled task is `Halo Research Gateway`. Runtime state is under `C:\Users\scott\AppData\Local\HaloResearchGateway`. Do not place credentials in TOML, command arguments, prompts, logs, or Git; create connections through the operator console. Models receive opaque connection IDs only.

Background start/stop operations are serialized. The launcher checks the configured port and health path, while stop verifies the repository, executable, module command and process creation time before using a held process handle. A mismatched record is preserved for inspection, not silently deleted. See the [launcher evidence and remaining limits](docs/LAUNCHER-OWNERSHIP-EVIDENCE-2026-09-02.md).

## Configuration

Use [config/config.example.toml](config/config.example.toml). Operator-controlled areas include storage/cache limits, queue depths, output ceilings, provider pacing, crawl bounds, exact named local targets, session-import review lifetime, durable job limits, and optional CAPTCHA/proxy identity, domains, attempts, and spend.

Core network and secret rules are code invariants, not Boolean settings. Public research can use valid public HTTP(S) ports beyond 80/443, but cannot pivot into loopback, private, link-local, or metadata networks. Local access uses separately named exact-target tools.

## Operator workflows

The console supports:

1. encrypted API key, token, or password connections;
2. OAuth Authorization Code + PKCE connection setup;
3. cookie-only research-session import into a gateway-owned copy;
4. research jobs, queues, and provider budgets;
5. review and confirmation of session imports only;
6. a bounded, operator-started public research-login handoff with temporary cookies.

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

The current working revision removes non-research features from the 0.2.0 codebase. It retains search, structured transcripts and communities, bounded deep research, read-only GitHub, research connections, and disabled optional retrieval providers. It does not send email, post to GitHub, submit general forms, buy things, or manage accounts. Provider/site-specific live use still requires an operator choice:

- no personal Chrome data is imported automatically;
- no OAuth or GitHub App is connected until the operator supplies its client/App identity and exact scopes;
- no CAPTCHA solver or proxy is selected, enabled, or charged by default;
- research-session import copies cookies and encryption metadata only, not passwords or other personal profile data; it is not site-filtered;
- public caption extraction does not download media or run speech-to-text;
- browser WebSocket handshakes are policy-checked; human handoff has a controlled visible-Chrome fixture, not real-account or DSH proof. Chromium-level DNS pinning remains open.

## Repository map

```text
src/halo_research_gateway/    Service, research tools, providers, policy, jobs, connections
tests/                        Deterministic and explicit acceptance tests
skills/halo-research/         Canonical host skill and complete reference set
config/                       Operator configuration example
scripts/                      Install, start, stop, test, gate, manifest
docs/                         Spec, user manual, security, operations, evidence
website/                      Product landing page and Sites deployment config
BUILD-MANIFEST.json           SHA-256 inventory of release source
```

## Contributing

1. Preserve the fourteen research contracts and the research-only scope. Do not add non-research features.
2. Keep raw secrets, approval authority, connection management, and diagnostics out of model-facing schemas.
3. Add deterministic tests for behavioral changes.
4. Run the full quality gate before committing.
5. Update implementation-status and evidence without turning unproven claims into passes.
6. Keep the canonical spec and installed skill references synchronized.

## License and ownership

This is Scott Converse's private Halo infrastructure repository. No public license is granted by the presence of source code.
