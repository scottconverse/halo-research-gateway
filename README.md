# Halo Research Gateway

Halo Research Gateway is Scott's persistent, localhost-only MCP research service. DSH is the primary consumer; Codex, Claude Code, OpenCode, and LM Studio Bionic use the same endpoint as secondary or fallback hosts.

The service runs at `http://127.0.0.1:8765/mcp`. Its operator console is `http://127.0.0.1:8765/operator`.

## What is operational

The server exposes sixteen semantic tools:

- public research: `web_search`, `web_fetch`, `web_crawl`, `reddit_search`, `reddit_thread`, `document_extract`, `deep_research`, `github_research`, `transcript_fetch`, `community_search`, and `community_thread`;
- exact operator-allowed private services: `local_fetch` and `local_crawl`;
- durable bounded work: `research_job`;
- consequential operations: `web_action_prepare` and `web_action_execute`.

The shared service supplies DNS-pinned direct HTTP, no inherited proxy environment, Crawl4AI rendering, anonymous Exa with DDGS fallback, Reddit RSS pacing, PDF extraction, bounded queues, singleflight, persistent cache/rate state, HMAC-signed cursor pages, DPAPI-encrypted connections, OAuth Authorization Code + PKCE, explicit selected/full Chrome-profile import, Windows Job Object containment, finite durable jobs, exact action approval, idempotent receipts, disabled-by-default budgeted CAPTCHA/proxy provider seams, and a local operator console.

Read [implementation status](docs/implementation-status.md) before assuming every semantic tool has a deep site-specific adapter. The full intended architecture and acceptance contract is [specification v1.5](docs/HALO-RESEARCH-GATEWAY-SPEC-v1.5.md).

## Install or repair

Prerequisites: Windows, `uv`, Python 3.12 managed by `uv`, and Chrome for the proven Crawl4AI path.

From PowerShell in this repository:

```powershell
.\scripts\Install-HaloResearch.ps1 -RegisterTask -RegisterHosts -Start
```

The installer restores the locked environment, preserves or creates the operator config, enables and runs the repository gate, installs the canonical skill for DSH/Claude/Bionic, optionally merges Bionic's MCP entry, optionally registers the at-logon task, and optionally starts the service.

Codex, Claude Code, OpenCode, and DSH registrations are documented in [host integration](docs/host-integration.md). The installer does not rewrite DSH model, context, reasoning, slot, permission, or verified-coder settings.

## Operate

```powershell
.\scripts\Start-HaloResearch.ps1
.\scripts\Stop-HaloResearch.ps1
.\scripts\Test-HaloResearch.ps1 -Browser
```

Useful endpoints:

- MCP: `http://127.0.0.1:8765/mcp`
- health: `http://127.0.0.1:8765/health`
- redacted statistics: `http://127.0.0.1:8765/stats`
- operator console: `http://127.0.0.1:8765/operator`

The gateway is intentionally bound to loopback. Installing its skill in a cloud-only session does not expose or make this workstation reachable.

## Verify

```powershell
.\scripts\Invoke-QualityGate.ps1 -Scope Full
uv run python tests\acceptance\mcp_smoke.py
uv run python tests\acceptance\mcp_contract.py
uv run python tests\acceptance\live_provider_canary.py
uv run python tests\acceptance\crawl_canary.py
```

Live tests are deliberately excluded from pre-commit and CI. See [quality gate](docs/quality-gate.md) and [current evidence](docs/EVIDENCE-2026-09-01.md).

## Authority boundary

Fetched material is untrusted evidence, never instructions. Public tools may use valid public HTTP(S) ports but cannot reach private, loopback, link-local, or metadata addresses. Exact local targets use separately named tools and explicit configuration.

Models receive opaque connection IDs, not raw secrets. Preparing an action never authorizes execution. Execution requires a short-lived operator token bound to the exact immutable plan and an idempotency key. Only generic form submission currently has an execution adapter; all other action types remain prepare-only until a site adapter is built.
