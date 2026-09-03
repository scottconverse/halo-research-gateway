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

The installer restores locked Python 3.12 dependencies, installs hash-verified English OCR language data and its license in the environment, preserves operator configuration, runs the quality gate, installs the canonical skill, merges supported host registrations, registers the task when requested, and starts the service. It must not rewrite DSH model settings.

Open `http://127.0.0.1:8765/operator`. Healthy means `status: ok`, version `0.2.0`, result schema `1.5`, database schema `3`, and ordinary providers ready or honestly degraded.

## 3. Start, stop, and inspect

```powershell
.\scripts\Start-HaloResearch.ps1
.\scripts\Stop-HaloResearch.ps1
.\scripts\Test-HaloResearch.ps1
```

Background start/stop operations share a Windows lock. The launcher uses the configured server port (8765 by default) and health path, verifies listener ancestry and health before saying "already running", and refuses to steal an unrelated listener. Stop checks this repository's executable, the exact Gateway module command, and recorded process creation time; it retains that validated process handle through termination instead of looking up the PID again. A mismatched record or process-access error leaves the record and process untouched for inspection.

New PID records use schema 2 and exact creation times. Legacy records written just after process creation are accepted only within a one-sided two-second compatibility window, with all other identity checks retained. Failed new starts stop only the process created by that invocation and remove its record after exit. Missing processes allow stale-record removal. Normal start/stop does not erase research state.

A disposable native test proved background duplicate-start prevention, listener closure, restart, and preservation of an unrelated process in Windows PowerShell and PowerShell 7. The Gateway process uses a Windows Job Object for its descendants; this test did not open Chrome or prove all browser shutdown paths. No DSH, LM Studio, personal Chrome or other live stack process was stopped by that test.

`-Foreground` remains the older diagnostic mode and is not PID-managed; use ordinary background start for managed lifecycle. Full foreground/logon/clean-install acceptance remains open. The readiness loop is bounded by attempts and per-request timeouts, not a strict 15-second wall-clock guarantee. See [launcher evidence](LAUNCHER-OWNERSHIP-EVIDENCE-2026-09-02.md).

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

### PDF text, tables, and local OCR

`document_extract` reads a public PDF and returns text with page citations. `pages`
selects one-based pages or ranges, for example `"1,3-5"`; missing, backwards,
zero, or overlong page selections return `PAGE_SELECTION_INVALID` rather than
silently clipping. With no selection it reads at most the first 300 pages and
warns if more exist. `include_tables=true` (the default) adds separate Markdown
tables when the PDF's native layout supports detection; `false` omits those table
items without removing ordinary page text. Table items cite their source page.

`ocr="never"` uses existing text only. `"auto"` (default) attempts local English
OCR for an empty-text page or a page with an image covering at least 20% of its
area. `"force"` OCRs the full selected page. Auto preserves available native text
and warns if OCR cannot run; force returns an explicit error. Image-only pages
without usable text do not return an empty success. OCR is recognition, not a
guarantee of correct wording: verify important passages against the page image.
Scanned table grids are not reconstructed into structured tables by this change.

The parser runs in a separate owned native Python process, with a 120-second
parse deadline and cancellation cleanup. Download time is separate. Limits are
20 MiB input, 300 selected pages, 150-DPI OCR capped at 20 million page pixels,
50 tables, 100 rows/30 columns/500 characters per cell, 50,000 characters per
item, 400,000 per document, and 2 MiB worker output. Warnings disclose retained
partial text/table output; ordinary MCP character limits and cursors still apply.
These are input/output/raster/time bounds, not a hard native-parser RAM sandbox.

Non-PDF sources retain plain-text/HTML fallback with `DOCUMENT_TEXT_FALLBACK`;
page selection and forced OCR require a PDF and otherwise return explicit errors.
Recognized sensitive PDF URLs, including final redirect URLs, have query values
redacted in citations and bypass disk caching. Such redacted links may require
the operator's original URL to open. Sensitive-value recognition is pattern-based,
not a promise to recognize every secret or private phrase in document prose.

To install or verify the pinned local English language data after updating source:

```powershell
uv run --locked python -m halo_research_gateway.ocr_data
```

This downloads about 4.1 MB once into `.venv/share/tessdata`, verifies SHA-256 and
size, and preserves any unrecognized existing file instead of replacing it.
No global Tesseract installation, cloud OCR, WSL, Docker, or account is required.
Restart an idle Gateway through its normal launcher after an update. See
[document evidence and remaining limits](DOCUMENT-EXTRACTION-EVIDENCE-2026-09-02.md).

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

For an imported session, installed Chrome reads the encrypted cookie copy and passes cookies in memory to the isolated research browser. No plaintext cookie export is saved. Session changes in that research browser last for its current context; they are not written back to the source or imported profile. Chrome may create fresh empty housekeeping databases in the owned copy; those are not imported passwords/history. A real-Chrome loopback fixture passed, but site-specific login and Chrome app-bound cookie compatibility still require validation with the operator's chosen dedicated profile.

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

Reddit requests use the shared bounded HTTP downloader, including redirect revalidation and response-size limits. A rate-limit response reports `RATE_LIMITED` and a retry delay; the durable cooldown applies to all clients before another request is allowed.

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
- `pause`: stop the active worker before returning, without erasing the job record;
- `resume`: continue a paused/recoverable job from saved sources; already-running and terminal jobs cannot be resumed;
- `cancel`: terminate without erasing its record.

Create/resume share the configured active-job ceiling and deep-research provider queue across clients. `max_sources`, `max_pages`, and `timeout_seconds` must be positive integers; returned limits show applied ceilings (currently 50 sources and at most 250 page attempts, or a lower configured ceiling). Saturation returns `JOB_CAPACITY_REACHED`; invalid lifecycle operations return `JOB_STATE_CONFLICT`. Page attempts and active elapsed time are cumulative across pause/resume. An interrupted in-flight page consumes its attempt; retrying it consumes another. Paused time does not consume the active-time budget.

Failed retrieval is a failed job, and an empty result is `NO_RESEARCH_EVIDENCE`. Usable results with warnings or more cursor pages are marked `progress.partial: true`; read the retained warnings and follow result cursors before claiming full coverage. Completion means the worker finished, not that every source was available or a final answer was verified.

Completed pages, discovery results, remaining sources, deduplication inputs and budgets are checkpointed locally. Resume does not repeat completed discovery or completed pages, even when their cache entries have been removed. An interrupted page is retried only if budget remains. If interruption occurred before discovery finished, discovery may need to run again.

Running jobs renew their leases. Graceful shutdown leaves interrupted workers `paused_recoverable`; startup also recovers jobs interrupted before worker start. A running job whose lease has not yet expired remains incomplete until expiry; the next job-control/status request checks recovery again. After a crash, the unobserved remainder of the lease is conservatively charged to the time budget, not the entire downtime. An operator pause/cancel cannot be overwritten by a late timeout.

Status returns checkpoint counts and a bounded evidence page instead of the whole stored packet. Follow that page's cursor with `deep_research`; cached evidence cursors survive restart until expiry/eviction. A status request can create a fresh evidence cursor from the retained checkpoint. Check the job's `state` and `error_code`: a failed/timed-out job can still return useful partial source evidence.

Checkpoint size is bounded by `storage.entry_max_bytes`; overflow reports `JOB_CHECKPOINT_TOO_LARGE` and retains the previous checkpoint. Sources and extracted links with recognized sensitive query parameters are excluded from durable jobs with `SENSITIVE_SOURCE_NOT_PERSISTED`. This is pattern-based protection, not a guarantee that arbitrary page prose contains no sensitive information. Use jobs for public research.

A disposable native Windows process-crash/restart fixture passed, including preserved evidence, no completed-source re-fetch, and cumulative attempts. Full DSH/live-provider job acceptance remains separate. DDGS performs synchronous work in a thread: cancellation stops the async research worker, but cannot forcibly terminate an already-running synchronous provider call. Broader provider cancellation/stress remains open. Background launcher ownership now has the separate native acceptance described in section 3; foreground/logon/clean-install acceptance remains open.

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
- Recognized sensitive original URLs bypass disk caching. PDF extraction also
  checks the final redirect URL and redacts sensitive citation query values.
  Equivalent final-redirect protection in generic HTTP/non-PDF fallback remains
  a recorded hardening gap; do not treat this as universal secret detection.
- Bounded queues return visible saturation errors instead of growing forever.
- Provider queues use round-robin scheduling across declared client profiles and FIFO within each profile. Missing or unknown `X-Halo-Client` values become `unidentified`; the value is scheduling metadata, never authentication or action authority.
- Identical requests share an upstream read. Cancelling one caller leaves that read running for other callers. Once its last caller cancels, a new request gets fresh work rather than inheriting the old cancellation. The stopping provider keeps its active slot until it actually exits; cancellation does not allow temporary concurrency-limit overruns. Repeated cancellation cannot interrupt queue bookkeeping.

These cancellation rules have deterministic race coverage and a real loopback
HTTPX connection test. They do not forcibly stop synchronous DDGS work already
running in a thread, or prove every external provider/browser shutdown path.

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
