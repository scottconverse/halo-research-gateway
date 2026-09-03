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

Run it from a Git checkout. Git hook setup failures stop installation instead of
being ignored; the configured commit hook requires PowerShell 7. The installer
itself supports Windows PowerShell 5.1 and PowerShell 7. A newly copied sample
configuration omits absolute storage/browser paths, so the service uses the
current Windows user's local application-data directory. Existing configuration
is preserved byte-for-byte; deliberate path overrides remain your responsibility.

`-RegisterHosts` updates only the `halo-research` entry in LM Studio's `mcp.json`,
using the active server port and MCP path (including `HALO_RESEARCH_CONFIG` when
set). Other server entries and settings remain. The original file gets a unique
`mcp.json.halo-backup-*` sibling; a temporary output is fully serialized before
replacement. Malformed/non-object JSON is preserved and errors do not echo its
contents. A changed file detected before replacement is not overwritten. Close
LM Studio settings while registering: the final file check is not a universal
cross-application transaction lock. The installer may already have installed
dependencies/skills before registration fails; it is not an all-or-nothing rollback.

Fresh native checkout/venv testing uses disposable profile paths and ports on
this existing Windows machine. It does not establish clean-OS prerequisites,
actual logon, real personal-profile import or a production deployment. See
[installer evidence](INSTALLER-EVIDENCE-2026-09-03.md).

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

On Halo, a September 3 deployment repair corrected a duplicate DSH tools package
that prevented calls from dispatching. It preserved models, presets, permissions
and all existing conversations. Search and reading now dispatch, but the broad
research acceptance task timed out after cursor-copy errors and compaction. Do
not treat a running server or a selected tool as proof of a supported final answer.
See [the exact repair and acceptance record](DSH-RESOLUTION-EVIDENCE-2026-09-03.md).

Pagination cursors are opaque text. Copy `page.next_cursor` exactly into the same
tool's `cursor` argument; do not decode, shorten, reconstruct or edit it. An error
is not a read page. A partial page can support the facts actually returned; it
does not establish that the whole source was read.

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

`http.max_decompressed_bytes` (default 20 MiB) caps both each streamed GitHub
API response and the sum of decoded response bytes in one research or discussion
operation. `http.total_timeout_seconds` (default 30 seconds) also covers the
whole operation: token-lock waiting/minting, DNS, response reading, and every
REST/GraphQL follow-up share it. Queue admission time is separate. Concurrent
operations receive separate budgets; cached-token reuse does not spend response
bytes, but a new token response does.

Per-request failures remain `GITHUB_RESPONSE_TOO_LARGE`, `GITHUB_REQUEST_TIMEOUT`
and `GITHUB_RESPONSE_INVALID`. Whole-operation exhaustion reports
`GITHUB_OPERATION_TOO_LARGE` or `GITHUB_OPERATION_TIMEOUT`. The failed operation
returns no items or evidence continuation; any sources already read in that
failed attempt are not retained. It does not silently switch to public search
or call an incomplete collection successful. Narrow the query/kinds/ref scan or
deliberately adjust the existing HTTP settings before retrying. Normal completed
collections retain their existing partial warnings and evidence pagination.

These bounds do not preempt synchronous/native parsing or bound JSON expansion,
decompression internals or total process memory. A synchronous over-deadline
result is rejected when control returns. Whole mixed-community searches have
other providers outside this GitHub-specific deadline. Installed/DSH acceptance
requires separate evidence. See [request-level evidence](RESPONSE-BOUNDS-EVIDENCE-2026-09-03.md)
and [whole-operation tests and limits](GITHUB-OPERATION-BOUNDS-EVIDENCE-2026-09-03.md).

### Pagination

Ordinary web search prefers anonymous Exa and falls back to DDGS. Domain inclusion/exclusion applies to either route. Freshness and non-web searches use DDGS because the anonymous Exa adapter does not pass those controls. Upstream freshness filtering is approximate, not a guarantee that every result has a verified publication date; inspect the source date. If Exa returns unrecognized text, links are marked as requiring fetch rather than borrowing an excerpt from another source.

For `web_crawl.wait_for`, supply a CSS selector such as `.quote` or `#ready`, without a `css:` prefix.

Results are bounded for local-model reliability. A signed cursor means more
collected evidence remains. Call the same tool with that cursor; continuation
does not repeat upstream traffic. Each page remains independently citable.
Models may request `2000`, `4000`, or `6000` characters within their host ceiling.
Use the same output budget throughout a continuation.

All thirteen pageable readers accept a cursor without repeating the original
URL, query, target or research question. That includes transcripts, community
search/threads and deep research. A new request without its required starting
information still returns a policy error. For a research job, use the cursor
inside `progress.result` with `deep_research` and the nested page's 4000-character
budget; do not send it to the job-control tool or invent a placeholder question.

Explicit live acceptance scripts are `tests/acceptance/search_fallback_native_live.py`
and `tests/acceptance/github_mcp_native_live.py`. Run them from the repository with
`uv run --locked python <script>`. Both start disposable native Gateway processes;
they do not reconfigure the installed service. The second reuses the existing
`gh` login in a temporary DPAPI-encrypted vault to read public GitHub sources,
then removes that vault. It does not create a production research connection.

The cursor now identifies immutable serialized evidence by SHA-256. Refreshing
the same URL cannot replace an older cursor's text. After restart or memory
eviction, public disk-backed results resume only if the current cache payload
has the identical hash. Non-cacheable/private results have no disk fallback.
Missing/replaced results return `CURSOR_EVICTED`; expired signatures return
`CURSOR_EXPIRED`. Start a fresh request in either case. Unexpired cursors issued
before metadata-aware cursor layout 3 also return `CURSOR_EVICTED`: the paging
layout changed, so old positions must not be silently reinterpreted. This does
not delete durable jobs, vault data or source profiles.

New cursors normally use a 51-character opaque reference beginning `h1_`.
Copy it exactly; the shorter form is not permission to abbreviate or reconstruct
it. It still authenticates the original layout-3 state, output budget, tool and
evidence identity. Existing unexpired layout-3 inline tokens remain accepted.
Tampered/malformed references return `CURSOR_INVALID` before reading saved state;
expired references return `CURSOR_EXPIRED` even after their saved state is gone.
Missing reference metadata returns `CURSOR_EVICTED` rather than fetching a source
again or silently substituting newer evidence.

Reference metadata has its own memory pool, using the same `snapshot_max_entries`,
`snapshot_max_bytes` and `cursor_ttl_seconds` limits as evidence snapshots.
`/stats.cursor_handles` reports its count, serialized bytes and caps, without
reference values or source contents. The two pools are separately bounded, so
their combined retained payload can reach twice the configured byte limit.
Private/non-cacheable metadata never goes to disk. Public metadata uses the
existing cache capacity and expiry rules; both it and the unchanged evidence
must survive for restart continuation. Cache statistics include these metadata
rows. If metadata cannot fit, output uses the existing longer signed cursor and
is refitted to the same character budget. No database migration is needed.

Long `snippet` and `content` fields continue on subsequent pages without silently
trimming their tails or repeating snippets on every content chunk. Partial item
metadata includes `text_offset` and `text_total`; these describe the snippet-plus-
content stream within that evidence chunk. Returned-item counts count emitted
fragments, not unique sources. Provider-level content limits still apply, and
existing link-metadata summaries are not a complete link inventory. If an item's
non-prose fields cannot fit even with a minimal text fragment, the call returns
`OUTPUT_ITEM_TOO_LARGE`; request a larger allowed budget rather than treating an
empty/truncated citation as success.

Transcript pages also carry `metadata.segments` incrementally. Follow every cursor
to collect both the readable transcript and the retained structured timestamps;
some later pages contain timing metadata without additional `content`. Do not
treat an empty `content` field as completion when a cursor remains. Each fragment
still contains the citation and language/source metadata.

For structured reassembly, use each segment's zero-based `segment_index` when
present. A segment split across pages preserves its start/end time and supplies
`text_offset`/`text_total` for its text fragment. Concatenate fragments in offset
order. A complete, unsplit result keeps the ordinary segment array. Item-level
`data_offset`/`data_total` describe the logical snippet/content/segment-text stream;
an empty timing record consumes one position. Ordinary non-caption item offsets
remain `text_offset`/`text_total`. Returned-item counts are fragments, not sources.

Run `uv run --locked python tests/acceptance/transcript_mcp_native_live.py` for
the explicit public-source/native-restart proof. It checks identical text and
timestamps at all three page sizes in disposable processes. No installed service,
account or personal profile is changed. The provider still collects at most 5000
caption segments and retains structured metadata for the first 200; beyond that
it reports truncation warnings while the collected readable transcript keeps its
timestamps. This change does not invent unavailable captions, run speech-to-text,
or make arbitrary oversized titles/publishers/other metadata fit.

Under `[output]`, `snapshot_max_entries` defaults to 128 and
`snapshot_max_bytes` to 67108864 (64 MiB of retained UTF-8 JSON payloads). Oldest
unused snapshots are evicted to stay within both limits. Each stored/continued
snapshot has an idle-retention deadline using `cursor_ttl_seconds` (default 3600);
expired entries are pruned on snapshot operations or statistics reads. Normal
service close releases them. `/stats.snapshots` reports count, payload bytes and
limits without source content. A single result above the configured byte budget
fails with `SNAPSHOT_TOO_LARGE`. These are retained-payload bounds, not a hard
bound on total Python/native RAM, temporary serialization or provider buffers.

Direct HTTP and non-PDF document fallback now redact recognized sensitive final
URL query values and skip disk caching, as PDF/browser results already do. New
fetch/document cache namespaces prevent reuse of older unsafe entries; historical
cache data is not scrubbed. This is not universal redaction of source prose,
embedded links or intermediate redirect hops. See
[evidence and remaining limits](RESULT-RETENTION-EVIDENCE-2026-09-02.md).

### Disk-cache capacity

Under `[storage]`, `cache_max_bytes` defaults to 1073741824 (1 GiB) and
`entry_max_bytes` to 5242880 (5 MiB). Both must be positive. They limit compressed
research payloads, not the physical SQLite file, WAL, backups, logs or total RAM.
`/stats.cache` reports entries, compressed bytes and both configured limits.

Every Gateway cache write removes expired or over-limit entries before committing,
so other clients cannot observe a committed overshoot. Ordinary disk-cache hits
and misses also prune old entries; lowering a limit takes effect on that traffic
or explicit cache maintenance. This is activity-driven, not an idle timer.
Statistics reads alone do not prune disk rows. Compact public continuation may
read or write reference metadata and therefore trigger ordinary cache pruning;
private in-memory continuation does not persist metadata. Least-recently-used
cache entries are discarded first. Other tables, including jobs,
connections, provider limits and historical receipts, are not deleted.

The cache prepares its database journal before serving requests. Another process
holding the database may delay that setup by up to five seconds; if it stays
locked, startup fails instead of passing the setup problem to a research request.
Do not delete the shared database to resolve a lock. Identify the other owner
first. Ordinary reads and writes no longer try to change the journal mode.

When a result cannot fit either cache limit, the source evidence remains readable
and pageable within the existing snapshot limits. It includes
`RESULT_NOT_CACHED_TOO_LARGE` and an empty `cache.key`. That warning means the
result was not saved in this cache; it does not mean retrieval failed. Its cursor
cannot recover after process restart and may expire or be evicted from memory.
Start a fresh request if it becomes unavailable. Durable job checkpoints are
separate; a large job result does not become unreadable merely because its cached
view is too large. Other storage errors are not covered by this guarantee.

Run `uv run --locked python tests/acceptance/cache_limits_native_live.py` for the
explicit native two-client/public-source eviction, restart and lowered-limit test.
It uses disposable loopback instances and changes no installed configuration.
See [exact evidence and limits](CACHE-LIMITS-EVIDENCE-2026-09-02.md).

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

### Human login or challenge handoff

This is an operator control for reading a public research source, not a model
browser-action tool. In the operator console, use **Sign in to a research source**:

1. Enter the public page URL and an existing Gateway research profile name.
2. Choose **Open research page**. An isolated visible Chrome window opens with
   a copy of that profile's research cookies; no personal browser is attached.
3. Complete the login or challenge yourself in that window.
4. Choose **Done — use temporary session** in the console.
5. Ask DSH to retry `web_crawl` with the original URL, `mode="managed_profile"`
   and the same `profile` name. Inspect the returned evidence and warnings.

Done means the cookies are ready to try, **not** that the source is now readable.
The fixture proves cookie transfer and a subsequent read, not a real CAPTCHA,
app-bound account, DSH workflow or universal login compatibility.

Completion responses remain bound to their original session even if another
session starts while the first HTTP response is returning. Status reports the
actual configured deadline. Cancellation during Playwright startup waits for
that driver to initialize and then shuts it down; repeated cancellation does not
abandon the startup/shutdown pair. This does not bound a genuinely hung driver.

One handoff may be active. Its deadline is at most 120 seconds (or a lower
`crawl.job_timeout_seconds`), including waiting for the shared browser slot,
profile loading, browser startup and the human step. Cleanup is separate and
does not yet have a hard wall-clock/hung-browser guarantee. Ordinary reads wait
for the same browser lock. The opening/waiting/ready/cancelled/timed-out/failed
state appears in the console; health and statistics expose only the state name.

Only one completed temporary cookie set is retained, at most 5000 cookies and
2 MiB serialized JSON. It is held in memory until restart, shutdown, a subsequent
completed handoff, or a successful cookie import into that same profile. The
original imported cookie files are not updated. Site session expiry still
applies. Ordinary crawls use a copy; they do not save later cookie changes.
Local storage, passwords, browsing history and other login mechanisms are not
transferred. Profile loading can create Chrome housekeeping files in its owned
copy, as it already did before this handoff.

Cancel, timeout, failure or closing the window discards that attempt's new
cookies and does not replace a prior completed temporary session. Import and
browser access share a lock: an already-started native import copy must settle
and record its receipt before cancellation releases ownership. Check the receipt
rather than retrying a disconnected import blindly.

The handoff accepts public HTTP(S) sources only. Existing public request,
redirect and WebSocket checks are installed before navigating. Same-tab public
login redirects may work; popup logins, local/private targets and downloads are
not supported. There are no model-operated clicks, selectors, form data, paid
solver calls or automatic retry loops in this flow. Chromium DNS pinning, OOPIF
coverage, resource bounds and a real operator-selected account remain separate
acceptance work. See [handoff evidence](HUMAN-HANDOFF-EVIDENCE-2026-09-03.md).

## 7. Browser crawling

Crawl4AI can reject a very small, low-text page as suspicious even when Chrome
rendered it successfully. The Gateway keeps that failure explicit as
`CRAWL_NO_EVIDENCE`; this code alone is not proof of a real CAPTCHA. Direct
`web_fetch`/`local_fetch` reading is separate and may be useful when the source
does not require JavaScript. A synthetic single-word page exposed this limit
during installer acceptance; see [installer evidence](INSTALLER-EVIDENCE-2026-09-03.md).

`max_pages` now limits actual navigation attempts (1..25, or the lower configured
ceiling), including failed pages. `max_depth` is link distance from the starting
page (0..3, or the lower configured ceiling); depth 0 reads only that page even
when `max_pages` is larger. Traversal is breadth-first, with fragment/canonical
duplicate suppression. `same_site_only=true` means the exact starting hostname,
not every subdomain of a registrable domain. It applies to discovered pages and
top-level redirects. `false` allows other public hosts; local crawling still
cannot leave its named target's exact host/port/path policy.

`interaction="scroll"` requests at most five full-page scroll steps. It does not
increase page count. `none` performs no requested interaction. Consent, load-more,
pagination-button/site-search interactions, screenshot/PDF captures, stealth and
undetected modes are **not yet implemented**; requesting them returns
`CRAWL_INTERACTION_UNAVAILABLE`, `CRAWL_CAPTURE_UNAVAILABLE` or
`CRAWL_MODE_UNAVAILABLE`. They remain research acceptance work, not removed scope.
`auto` begins with standard browsing; recognized challenges can use configured
CapSolver token application or Bright Data fallback (section 11).
Metadata says `mode=captcha` or `mode=proxy` when used. Managed profiles,
named local targets, recognized sensitive URLs and explicit scroll interactions
are not outsourced. `standard` stays on the local browser path. Human handoff
has the operator-only flow above; real-account and installed/DSH acceptance
remain unfinished. The token path has controlled native-browser evidence only.

`managed_profile` requires an existing Gateway-owned profile. Supplying a profile
with another mode fails explicitly instead of silently browsing anonymously.
Managed public-crawl results are not disk-cached. Named local targets retain
their explicit `cache_authenticated` policy. Browsers close after each bounded
crawl; in-context cookie changes are not preserved into later calls. Imported
source/copy profiles are not erased. Recognized sensitive final citation URLs are
redacted and excluded from disk cache; arbitrary sensitive prose or Markdown
links are not universally detected/redacted.

`wait_for` is a CSS selector, at most 1024 characters, without a `css:`/`js:`
prefix. It applies to each visited page; use it only when that selector exists
throughout the requested page set. Invalid CSS returns `CRAWL_SELECTOR_INVALID`.
The configured whole-crawl deadline (120 seconds by default) covers validation,
browser startup and collection after admission; per-page work defaults to 45
seconds. Queue waiting and cleanup are separate. Completed evidence is retained
with `CRAWL_TIMEOUT` or page-failure warnings; wholly empty/failed collection is
`CRAWL_NO_EVIDENCE`, never an empty success.

Returned content is bounded to 50,000 characters per page/400,000 per crawl, with
titles capped at 1000 characters, at most 250 inspected link entries per page
and 250 remembered frontier URLs. Warnings disclose truncation and limits. This
does not impose hard browser RAM or subresource byte/request limits. Public
top-level navigation shares the direct-fetch origin concurrency/pacing slot;
redirect destinations and browser subresources do not yet share all those slots.

Chromium response-stage interception checks redirect destinations before they
are followed; ordinary Playwright request routing alone was insufficient. Real
fixtures prove top-level cross-host and JavaScript multi-hop local-path redirects,
alongside the existing HTTP/WebSocket checks. Cross-origin out-of-process iframe
coverage and Chromium DNS pinning still need acceptance. A native cancellation
fixture confirms that its owned Chrome/driver processes exit; this is not a
complete browser crash/hang/long-running stress test. See [crawl evidence](CRAWL-TRAVERSAL-EVIDENCE-2026-09-02.md).

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

WebSocket handshakes are intercepted and passed through the same destination policy. A controlled visible human-handoff fixture passes; real-account and installed acceptance remain open, alongside Chromium-level DNS pinning. These gaps do not make fetched content trusted and do not authorize actions.

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

In the September 3 response-bound source checkpoint, `local_fetch` shares the
HTTP queue, cancellation handling and per-origin pacing with other readers.
Queue saturation is `QUEUE_FULL`. Its active operation, including origin pacing,
uses `http.total_timeout_seconds`; time waiting for shared queue admission is
separate. Each decoded response uses `http.max_decompressed_bytes`.
`LOCAL_RESPONSE_TOO_LARGE`, `LOCAL_REQUEST_TIMEOUT` and `LOCAL_REDIRECT_DENIED`
return no successful partial source. Local reads remain uncached on disk and
successful evidence still pages normally. These are not browser, compressed-wire,
decompression-allocation or whole-process memory limits. Check the latest operator
delivery receipt for the exact revision loaded by the installed service.

`local_fetch` performs a GET, so the named target must explicitly allow `GET`.
A HEAD-only or empty methods list returns `LOCAL_METHOD_NOT_ALLOWED` before any
source request. The tool does not silently switch methods or alter the target.

When a source URL contains a recognized sensitive parameter (such as `token`,
`api_key`, `session` or `X-Amz-Signature`), the original URL is used for that
authorized request, but all query values in returned citation URLs are redacted.
Continuation snapshots retain the redacted citation and complete source text;
`SENSITIVE_URL_NOT_CACHED` explains the policy. Local results are never disk-cached.
The returned redacted URL may not reopen the authenticated source by itself.
This is not universal secret detection or a scrub of fetched prose, arbitrary
embedded links, path secrets, unrecognized query names or historical data.
See [local policy evidence](LOCAL-READER-POLICY-EVIDENCE-2026-09-03.md).

## 9. Durable research jobs

Expected control failures now return a normal error envelope with `ok: false`,
empty `items`, and an explicit `error.code`: `JOB_NOT_FOUND`, `JOB_NOT_OWNED`,
`JOB_STATE_CONFLICT`, `INVALID_JOB_LIMITS`, `JOB_CAPACITY_REACHED` or
`INVALID_ARGUMENT`. Unknown exceptions remain sanitized. A terminal job cannot
be paused/resumed: inspect its status rather than assuming a failed control call
changed the job. September 3 DSH trials created jobs and read retained evidence,
but both completed before pause arrived; DSH pause/resume is not yet proved.
See [DSH job evidence](DSH-JOB-EVIDENCE-2026-09-03.md).

`research_job` operations:

Request bounds: question at most 8192 characters, profile label 1–64 characters,
and supplied job ID at most 128 characters. Only `max_sources`, `max_pages` and
`timeout_seconds` are accepted in `limits`; unknown/nested/invalid limits fail
before creation. The profile is a descriptive label, not a new model or
permission setting. A nonempty `research_job.cursor` is rejected; follow evidence
cursors with `deep_research` instead.

`max_chars` limits the complete status JSON to 2000, 4000 or 6000 characters,
subject to the existing configured ceiling. The full question stays stored;
the status shows at most 128 characters with `question_truncated` and
`question_chars` when shortened. The preview may be empty at a small budget.
Optional timing, owner-label, limits or checkpoint-summary fields can be omitted
with `JOB_STATUS_METADATA_OMITTED`; request a larger status to see more metadata.
When the nested evidence cannot fit beside the job fields, its first page may
contain zero items and a continuation to the first evidence item. Coverage is
explicitly incomplete and the job remains partial; follow the cursor before
claiming to have read any evidence. The service first verifies that a normal
standalone evidence page can fit the continuation budget.
Evidence continuations may omit `max_chars` or use the same requested budget;
the default job status retains a 4000-character continuation budget.

If evidence metadata or snapshot retention cannot fit, the control response
still reports the actual job ID/state and a partial evidence error
(`OUTPUT_ITEM_TOO_LARGE` or `SNAPSHOT_TOO_LARGE`). Particularly large legacy
status fields may be omitted with `JOB_STATUS_FIELDS_OMITTED`. This does not
undo a pause/cancel or delete the underlying job. A larger output budget can
help with formatting, but cannot raise the configured retention cap. See
[job-boundary evidence](JOB-BOUNDS-EVIDENCE-2026-09-03.md).

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

Only session-import approval remains from the former action system. Research connections and the operator's bounded login handoff are separate research controls. Existing historical receipts and encrypted connections are preserved; they cannot restore removed actions.

## 11. Optional CAPTCHA/proxy providers

The release includes tested CapSolver and Bright Data Web Unlocker adapters behind the durable provider-budget policy. Both are disabled by default.

Using a provider requires an encrypted connection ID, exact allowed requested
domains, daily attempt ceiling, estimated-spend ceiling, and positive operator
`request_cost_usd`. Its default zero refuses automatic paid calls. Existing
enabled policies without an estimate load but cannot execute a default-cost
request. The model does not set the price. Reservations round up to the next
microdollar; failed/cancelled attempts retain them because the request may have
already reached the vendor.

`spend_usd_today` reports **reserved estimated cost**, not a reconciled invoice
or guaranteed vendor charge ceiling. Statistics also show `spend_is_estimated`
and `request_cost_usd`. Supply a conservative estimate for the vendor product
and use vendor-side controls for a real billing ceiling. This checkpoint does
not authorize paid calls.

A recognized gate in `web_crawl(mode="auto")` can trigger one Bright Data request
for that page. Returned HTML is extracted without executing its scripts, then
uses normal bounded pagination. The requested URL is revalidated before dispatch.
No imported cookies, browser headers, passwords or local targets are forwarded.
Unsupported modes/interactions, managed/sensitive requests and disabled providers
produce `CRAWL_CHALLENGE_REQUIRED`, not gate-page evidence. Ordinary 404/500 errors
and articles discussing CAPTCHAs do not themselves trigger paid fallback.

Bright Data requests structured JSON by default; explicit raw adapter responses
are also supported. HTTP errors, empty/invalid results and still-challenged pages
are not successful research. The API does not attest its final redirect URL:
`PROXY_FINAL_URL_UNVERIFIED`, `citation_url_kind=requested` and
`final_url_verified=false` disclose that limit. Do not call that URL independently
verified canonical. Relative links are not resolved against an unknown final
base. The vendor controls its own DNS, redirects and subresources; local
requested-domain checks cannot prove the domain of every vendor-side hop.

When `[captcha]` is fully configured with `provider="capsolver"`, automatic public
crawling can apply a returned token to a recognized **standalone** Turnstile or
reCAPTCHA v2 widget. The page must declare one `data-sitekey` and a callable named
`data-callback`. The Gateway fills the widget's response field and invokes that
callback, then reads the resulting page. It does not submit a form, enter a
password, inspect hidden CAPTCHA internals or offer a general script/action tool.
Turnstile `data-action`/`data-cdata`, when declared, accompany the public URL and
site key sent to the solver. No imported cookies, browser headers or connection
secrets are sent to the research page. Solver credentials go only to the vendor.

The existing exact-domain, connection, attempt and estimated-spend policy must
permit the request. Local/sensitive URLs, managed profiles and explicit
non-automatic modes/interactions do not use it. Missing, multiple, oversized or
unsupported widgets return `CRAWL_CHALLENGE_UNSUPPORTED` without a solver attempt.
The page URL and widget identity are checked again after the vendor response;
a changed widget returns `CRAWL_CHALLENGE_CHANGED`. Invalid solutions return
`CRAWL_CHALLENGE_SOLUTION_INVALID`; unexpected solver errors are sanitized.
Configured solver failures do not silently spend against a second provider.

Successful retrieval reports `CAPTCHA_RETRIEVAL_USED`, `mode=captcha` and
`retrieval_provider=capsolver`. A solved callback alone is not success: the final
page must no longer be recognized as a gate and have a successful observed HTTP
status. A DOM change cannot turn an original HTTP 403 into success; a subsequent
real main-frame 200 navigation can. The exact returned token is redacted if
reflected into evidence; token-bearing citation/navigation URLs are rejected.
This is not universal secret detection or a guarantee that every site's script
keeps its own data private.

CapSolver's create/poll sequence has a 120-second deadline and at most 40 polls,
with no vendor callback URL. Each fixed-API request has a 45-second total I/O
deadline and 20 MiB decoded response ceiling. Browser token application also stays
inside the page/job deadline. Cancelled vendor attempts retain their estimated
cost reservation. These are not hard native-memory or CPU-parser guarantees.
Dynamic/enterprise widgets, hCaptcha, invisible/hidden-client integrations,
real-vendor success and installed/DSH usage remain unproved. Both providers remain
disabled on the installed host; this documentation does not enable paid calls.

Earlier evidence survives later challenge/provider failures with visible warnings.
Fresh crawl/forum requests bypass old cache namespaces that could contain gate
pages. Historical data and existing cursors are preserved; start a fresh request
to apply the new classification. Recognition is deliberately specific, not a
universal login/paywall/challenge detector.

The native test uses actual Chrome, network MCP, a public header-echo signal and
a local fake vendor. It proves routing, pagination, shared requests/cache,
durable reservations and browser cleanup—not a real CAPTCHA bypass, live vendor
success or operator login. No paid endpoint was contacted. The newer token tests
use actual Chrome, two network MCP clients and a loopback fake solver to prove
callback/response-field application, readable DOM/navigation results, token
redaction and cleanup. Native cancellation is exercised directly through the
crawler, not by disconnecting an MCP client. Real login/app-bound cookies,
paid-vendor and installed/DSH acceptance remain separate. See
[token evidence](CAPTCHA-TOKEN-EVIDENCE-2026-09-03.md) and the earlier
[proxy-routing evidence](CHALLENGE-ROUTING-EVIDENCE-2026-09-02.md).

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
