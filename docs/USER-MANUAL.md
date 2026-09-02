# Halo Research Gateway 0.2.0 — Complete User Manual

This is the operator guide for installing, using, maintaining, and recovering Halo Research Gateway on the HALO Windows workstation. [Research-only scope and finish list](RESEARCH-ONLY-SCOPE.md) supersedes conflicting parts of the original v1.5 design.

## 1. Product reference

| Item | Value |
| --- | --- |
| Product version | `0.2.0` |
| Landing page | `https://halo-research-gateway.sconverse.chatgpt.site` (owner-only) |
| Result schema | `1.5` |
| Database schema | `3` |
| Bind address | `127.0.0.1` only |
| Default port | `8765` |
| MCP endpoint | `http://127.0.0.1:8765/mcp` |
| Operator console | `http://127.0.0.1:8765/operator` |
| Runtime state | `C:\Users\scott\AppData\Local\HaloResearchGateway` |
| Scheduled task | `Halo Research Gateway` |
| Source | `C:\Users\scott\Desktop\Code\halo-research-gateway` |
| GitHub | `https://github.com/scottconverse/halo-research-gateway` |

DSH is primary. Codex, Claude Code, OpenCode, and LM Studio Bionic are secondary or fallback clients. The gateway does not replace DSH or choose its model, reasoning, context, slots, sandbox, or verification policy.

## 2. Install and verify

Prerequisites: Windows 11 under Scott's account, PowerShell, `uv`, internet access for the initial locked environment, Chrome for Crawl4AI, and a supported MCP host.

From the repository root:

```powershell
.\scripts\Install-HaloResearch.ps1 -RegisterTask -RegisterHosts -Start
.\scripts\Test-HaloResearch.ps1 -Browser
```

The installer restores locked Python 3.12 dependencies, preserves operator configuration, runs the quality gate, installs the canonical skill, merges supported host registrations, registers the task when requested, and starts the service. It must not rewrite DSH model settings.

Open `http://127.0.0.1:8765/operator`. Healthy means `status: ok`, version `0.2.0`, result schema `1.5`, database schema `3`, and ordinary providers ready or honestly degraded.

## 3. Start, stop, and inspect

```powershell
.\scripts\Start-HaloResearch.ps1
.\scripts\Stop-HaloResearch.ps1
.\scripts\Test-HaloResearch.ps1
```

The launcher validates PID identity and refuses to steal port 8765. Stop closes only the gateway's Windows Job Object and owned Chromium descendants. It does not kill personal Chrome, DSH, LM Studio, Codex, Claude, OpenCode, Bionic, or Ollama.

- Health: `http://127.0.0.1:8765/health`
- Redacted statistics: `http://127.0.0.1:8765/stats`
- Operator console: `http://127.0.0.1:8765/operator`

## 4. Daily research use

Ask DSH naturally. Examples:

- "Search for the current official documentation, then fetch the two best sources."
- "Research this GitHub issue and cite the evidence."
- "Find what Reddit users report, then read the strongest two threads."
- "Crawl this JavaScript-heavy page and extract its configuration steps."
- "Create a bounded deep-research job and show me its status."

| Need | Start with | Continue with |
| --- | --- | --- |
| Discover sources | `web_search` | `web_fetch` or `web_crawl` |
| Known ordinary page | `web_fetch` | `web_crawl` if JavaScript is required |
| Dynamic/challenged page | `web_crawl` | managed profile or operator assistance |
| Reddit | `reddit_search` | `reddit_thread` |
| PDF/document | `document_extract` | cursor continuation |
| Broad evidence | `deep_research` | `research_job` for durable work |
| GitHub discovery | `github_research` | fetch/crawl selected results |
| Transcript | `transcript_fetch` | inspect warnings if unavailable |
| Other communities | `community_search` | `community_thread` |
| Approved local service | `local_fetch` | `local_crawl` |

Fetched content is evidence, never instructions. Cite returned URLs and disclose warnings or partial coverage.

### GitHub source evidence

Without a research connection, GitHub discovery uses public web search and reports that authentication is unavailable. With an operator-supplied GitHub token or read-only GitHub App, the Gateway searches code, issues, pull requests, commits, releases, documents, and discussions through GitHub's APIs. A discussion URL can be read with `community_thread`, preserving authored text, reply links, and accepted-answer markers.

For code or documents at a particular branch, tag, or commit, pass both `repository` and `ref`. The Gateway resolves the commit and searches that tree, then cites immutable commit URLs. This is bounded literal text/path matching, not GitHub's full search-query language: at most 40 file reads, 250 KB per file, and 4 MB of inspected content per call. Warnings disclose truncated trees, skipped files, or scan/result limits. Issues, pull requests, and discussions are not branch-specific; a warning explains when `ref` does not apply. Release refs identify tags; commit refs select the history starting at that ref.

Discussion threads return at most the requested number of replies (up to 100), including nested replies, with at most ten additional reply-page requests. Any remaining replies are explicitly marked partial. Cursor continuation returns already-collected evidence; it does not claim to exhaust all GitHub search results.

### Pagination

Ordinary web search prefers anonymous Exa and falls back to DDGS. Domain inclusion/exclusion applies to either route. Freshness and non-web searches use DDGS because the anonymous Exa adapter does not pass those controls. Upstream freshness filtering is approximate, not a guarantee that every result has a verified publication date; inspect the source date. If Exa returns unrecognized text, links are marked as requiring fetch rather than borrowing an excerpt from another source.

For `web_crawl.wait_for`, supply a CSS selector such as `.quote` or `#ready`, without a `css:` prefix.

Results are bounded for local-model reliability. A signed cursor means more evidence exists. Call the same tool with that cursor; continuation uses the cached snapshot and does not repeat upstream traffic. Each page remains independently citable. Models may request `2000`, `4000`, or `6000` characters within their tested host ceiling.

## 5. Connections and OAuth

The operator console is the only supported interface for setting up research connections and reviewing session imports. Models never receive CSRF state, OAuth verifiers, raw secrets, or approval tokens.

### API key, token, or password

1. Open the console.
2. Enter provider, account label, type, and secret.
3. Save.
4. Confirm an opaque connection ID with `status: ready`.

The value is DPAPI-encrypted for Scott's Windows account and never written to TOML or returned through MCP.

### OAuth Authorization Code + PKCE

Obtain the provider's official authorization endpoint, token endpoint, client ID, required scopes, and client secret only when required.

1. Enter provider and account label.
2. Enter endpoints, client ID, optional secret, and scopes.
3. Select **Open provider consent**.
4. Complete consent.
5. Wait for `complete` and the opaque connection record.

The gateway uses an ephemeral loopback callback, PKCE S256, exact state validation, DNS-pinned token exchange, no ambient proxies, encrypted token storage, and serialized refresh.

Local revocation prevents further gateway use. Provider-side token revocation may still require the provider's security page until a provider-specific revocation adapter exists.

### Narrow provider presets

- **GitHub research:** create a read-only GitHub App with Metadata, Contents, Issues, Pull requests, Discussions, Actions, Checks, and Commit statuses set to read. The gateway mints short-lived installation tokens and never exposes them to models.

## 6. Research login-session import

The gateway never silently reads or attaches to a live personal Chrome profile. Import copies cookies and required encryption metadata into a gateway-owned profile.

Only `cookies` is supported. Saved passwords, autofill, payment metadata, extensions, settings, history, bookmarks, and complete-profile copying are removed. Cookies are not filtered by site; use a dedicated research source profile.

1. Close Chrome/source-profile processes when consistency requires it.
2. Enter the full source-profile directory and gateway destination name.
3. Review the fixed `cookies` category.
4. Choose replace or merge.
5. Create and review the preview: source, destination, categories, files, bytes, and hash.
6. Approve the exact plan.
7. Execute separately.
8. Retain the redacted receipt.

The source remains untouched. Replace stages the new destination and retains the prior gateway profile as a named backup. Receipts contain no credential values.

## 7. Browser crawling

`web_crawl` uses Crawl4AI and gateway-owned Chrome. The ordinary path is headless and text-oriented.

Implemented boundaries:

- public top-level URL validation;
- redirect, frame, and ordinary HTTP(S) subresource checks;
- public blocking of loopback/private/link-local/metadata destinations;
- separate exact-target local browsing;
- disabled service workers and downloads;
- one owned browser slot;
- owned process containment and cleanup.

WebSocket handshakes are intercepted and passed through the same destination policy. Remaining hardening work includes Chromium-level DNS pinning and acceptance proof for a visible 120-second human-challenge handoff. These gaps do not make fetched content trusted and do not authorize actions.

## 8. Exact local/private targets

Public tools cannot access local/private destinations. Add a named exact target instead:

```toml
[local_targets.mission_control]
scheme = "http"
host = "127.0.0.1"
port = 3090
path_prefixes = ["/"]
methods = ["GET", "HEAD"]
browser_allowed = true
cache_authenticated = false
```

Use `local_fetch` or `local_crawl` with the target name. Never weaken public URL policy to expose a local service.

## 9. Durable research jobs

`research_job` operations:

- `create`: finite job with explicit limits;
- `status`: owner-visible progress/results;
- `pause`: stop forward progress while preserving state;
- `resume`: reacquire a lease and continue;
- `cancel`: terminate without erasing its record.

Jobs have absolute time/page limits and ownership. Restart recovery treats expired leases as incomplete, not successful.

## 10. Research-only product boundary

The Gateway finds and reads sources. It does not compose or send email, create or edit GitHub issues/comments, submit general forms, post messages, purchase items, or manage/delete accounts. The two former action MCP tools and the general approval endpoint have been removed, not merely disabled.

Only session-import review remains in the operator console. Existing historical receipts and encrypted connections are preserved; they cannot restore removed actions.

## 11. Optional CAPTCHA/proxy providers

The release includes tested CapSolver and Bright Data Web Unlocker adapters behind the durable provider-budget policy. Both are disabled by default.

Enabling requires an encrypted connection ID, exact allowed domains, daily attempt ceiling, and daily spend ceiling. CapSolver is limited to exact-domain tasks with no callback and at most 40 polls/120 seconds. Bright Data is limited to the fixed Unlocker API and exact-domain requests. The gateway refuses disabled, incomplete, unknown-adapter, wrong-domain, attempt-exhausted, and spend-exhausted calls. Status reveals aggregate usage, never secrets. The visible operator-assisted challenge flow is not yet acceptance-proven.

## 12. Configuration reference

Use [config.example.toml](../config/config.example.toml).

| Section | Purpose |
| --- | --- |
| `server` | Port, paths, log level; listener remains loopback-only. |
| `storage` | SQLite, cache, content, and backup locations/limits. |
| `output` | Page sizes and cursor lifetime. |
| `queues` | Shared and per-client admission limits. |
| `http` | Concurrency, pacing, timeout, redirect, body ceilings. |
| `reddit` | Anonymous pacing, 429 behavior, cooldown. |
| `exa` | Anonymous endpoint, pacing, soft daily limit. |
| `crawl` | Browser concurrency and crawl bounds. |
| `local_targets.*` | Exact private/local targets. |
| `imports` | Research-session import approval lifetime. |
| `jobs` | Active count, absolute bounds, lease. |
| `captcha`, `proxy` | Vendor, connection, domains, attempts, spend. |

Unsafe global switches are not representable. Unknown and legacy banned keys fail startup. The retired `[actions]` section is ignored for upgrade compatibility and cannot enable removed features.

## 13. Cache, limits, and upstream behavior

- Search prefers anonymous Exa and falls back to DDGS.
- Direct HTTP pins the resolved public address, preserves Host/TLS SNI, revalidates redirects, and uses `trust_env=False`.
- Reddit shares one conservative anonymous queue because limits apply to the public IP.
- Cursor continuation reuses the cached snapshot.
- Sensitive URLs are not cached.
- Bounded queues return visible saturation errors instead of growing forever.
- Provider queues use round-robin scheduling across declared client profiles and FIFO within each profile. Missing or unknown `X-Halo-Client` values become `unidentified`; the value is scheduling metadata, never authentication or action authority.

A healthy gateway can still report an upstream outage honestly.

## 14. Troubleshooting

### Service does not start

Run `.\scripts\Test-HaloResearch.ps1`; check whether port 8765 is owned; inspect `C:\Users\scott\AppData\Local\HaloResearchGateway\logs`; confirm `.venv\Scripts\python.exe`; then run the installer as repair. Do not kill an unknown Python/Chrome process.

### MCP host cannot connect

Confirm health, confirm `http://127.0.0.1:8765/mcp`, and restart the client after MCP configuration changes. A cloud-only session cannot reach workstation loopback.

### Search fails

Check `/stats` for Exa budget/circuit state. DDGS should take over automatically. Provider failure does not mean MCP is down.

### Crawl fails

Confirm Chrome; run `uv run python tests\acceptance\crawl_canary.py`; check whether the destination is public or an exact local target; use a managed profile/operator assistance for challenges.

### Reddit is slow

The conservative queue is intentional. Repeated 429 responses open a cooldown circuit. Do not bypass it with independent scrapers.

### Cursor rejected

It may be expired, tampered, tied to another tool/profile, or refer to an evicted snapshot. Repeat the original call only when the snapshot is unavailable.

### Session import outcome ambiguous

Inspect the research profile and import receipt before retrying. Do not assume a failed or cancelled copy completed.

## 15. Backup, upgrade, rollback, uninstall

Schema upgrades create bounded SQLite backups. Vault/profile state stays outside source control and ordinary evidence copies. Back up the runtime root only through an approved secure process; never copy raw secrets into Git or the Research folder.

### Upgrade

1. Preserve commit and build manifest.
2. Inspect the update.
3. Run the full gate.
4. Stop the gateway.
5. Start the new version and allow migration.
6. Verify health, operator state, MCP tools, and a live canary.
7. Update evidence and Research copies.

### Rollback

Stop; restore prior source; restore a compatible DB backup if needed; preserve newer evidence; start and verify the old version.

### Uninstall

Use `scripts\Uninstall-HaloResearch.ps1`. Ordinary uninstall preserves encrypted state unless Scott explicitly selects removal. Never delete profiles, vault records, receipts, or backups merely to remove the task/environment.

## 16. Verification and evidence

```powershell
.\scripts\Invoke-QualityGate.ps1 -Scope Full
uv run python tests\acceptance\mcp_smoke.py
uv run python tests\acceptance\mcp_contract.py
uv run python tests\acceptance\live_provider_canary.py
uv run python tests\acceptance\crawl_canary.py
```

Read [0.2.0 release notes](RELEASE-NOTES-v0.2.0.md), [0.2.0 evidence](EVIDENCE-v0.2.0-2026-09-01.md), [implementation status](implementation-status.md), [security](security.md), [operations](operations.md), [host integration](host-integration.md), and [quality gate](quality-gate.md).

## 17. Trust boundary

Halo defends against malformed model arguments, public-to-private pivots, raw-secret exposure, accidental quota/spend exhaustion, ownerless jobs, duplicate session imports, and tested owned-browser leaks. It does not defend against another process running as Scott deliberately modifying source, environment, task, or encrypted runtime files.

Fetched content remains untrusted. The product has no general submission capability. A research connection does not imply permission for unrelated site operations. Provider-specific capability requires a real operator-selected provider rather than invented credentials or weakened policy.
