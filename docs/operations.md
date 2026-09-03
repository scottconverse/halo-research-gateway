# Operations

## Runtime locations

- Repository: `C:\Users\scott\Desktop\Code\halo-research-gateway`
- Runtime root: `C:\Users\scott\AppData\Local\HaloResearchGateway`
- Operator config: `C:\Users\scott\AppData\Local\HaloResearchGateway\config.toml`
- Database: `C:\Users\scott\AppData\Local\HaloResearchGateway\state\gateway.db`
- Backups: `C:\Users\scott\AppData\Local\HaloResearchGateway\state\backups`
- Vault: `C:\Users\scott\AppData\Local\HaloResearchGateway\vault`
- Browser data: `C:\Users\scott\AppData\Local\HaloResearchGateway\browser`
- PID identity: `C:\Users\scott\AppData\Local\HaloResearchGateway\run\gateway.json`

Start and stop only with the repository scripts. The stop script verifies executable and command-line identity before stopping the recorded PID. Do not stop another Python, browser, LM Studio, DSH, or Ollama process by name.

## Recovery

Pagination snapshots now have count, serialized-byte and idle-retention limits
under `[output]`; usage is visible at `/stats.snapshots`. An old or evicted cursor
may require a fresh research request. Public disk recovery checks the original
payload hash; non-cacheable cursors never recover from an old disk entry. Durable
job records are separate and remain intact. Old fetch/document cache namespaces
are no longer served by new requests; this upgrade does not scrub historic data.
See [pagination operation and limits](USER-MANUAL.md#pagination).

The service retains the last three SQLite backups before migrations. A migration failure must leave the previous database intact and stop startup. Do not delete `gateway.db` to clear cache because it also owns provider circuits, connections, jobs, plans, and receipts.

If port 8765 is occupied, identify the owning PID and command line; do not kill it blindly. The Windows Job Object contains the gateway and descendants it launches; it does not adopt unrelated Chrome or Chromium processes.

The registered task is `Halo Research Gateway`. The 2026-09-01 recovery drill performed an ownership-checked stop, invoked the task, restored `status=ok`, and recorded task result `0x00000000`. A future recovery claim must repeat the drill against the current source/installer identity rather than relying on that historical receipt.

## Shared disk-cache limits

The Gateway enforces positive `[storage]` cache/entry limits on compressed payload
bytes. Every write prunes within its SQLite transaction; ordinary cache reads
also reconcile expiry and lowered limits. `/stats.cache` exposes both caps.
Only `cache_entries` rows are pruned. Never delete the shared database to clear
research cache: it also contains durable jobs, connections and provider state.

Cache construction prepares SQLite WAL before request handling. Simultaneous
initializers retry only SQLite busy errors for at most five seconds; failure
stops initialization instead of leaving the first research request to configure
the journal. An existing database transaction can therefore delay startup.
Ordinary request connections do not change journal mode. This fixes the race
recorded in [challenge-routing evidence](CHALLENGE-ROUTING-EVIDENCE-2026-09-02.md);
it does not promise that all database contention or storage errors disappear.

This is not a physical SQLite/WAL/log/backup size cap or idle cleanup timer.
The database may retain allocated free pages; no VACUUM is performed. SQLite I/O
and gzip remain synchronous and do not yet have a strict event-loop deadline or
peak-memory guarantee. In-memory cursor traffic alone does not prune disk rows.

`RESULT_NOT_CACHED_TOO_LARGE` preserves usable evidence without a disk-recoverable
key. An evicted/uncached cursor may need a fresh request after restart. Native
validation and exact bounds: [cache-limit evidence](CACHE-LIMITS-EVIDENCE-2026-09-02.md).

## Research provider setup

- Use the operator console's read-only GitHub App form for research.
- Cookie-only imported research profiles live under the gateway runtime browser directory and are copied capabilities. Never point Crawl4AI at the mutable source profile.
- Provider use requires a vendor name, encrypted connection, exact requested domains, attempt/estimated-spend limits and positive `request_cost_usd`. Installed defaults remain disabled. Estimates are reserved, not reconciled vendor charges; use vendor-side billing controls.
- Auto public crawl can route recognized challenges to Bright Data. Local/managed/sensitive reads and explicit standard/scroll modes are not outsourced; browser cookies/headers are not sent. Human handoff and CapSolver token application remain unfinished.
- Requested-domain checks cannot independently enforce vendor-side redirects/DNS. Native proof uses a fake vendor, not paid acceptance. See [challenge routing evidence](CHALLENGE-ROUTING-EVIDENCE-2026-09-02.md) and the user manual.

## Local document OCR data

`Install-HaloResearch.ps1` invokes `uv run --locked python -m
halo_research_gateway.ocr_data` after environment synchronization. This verifies
and installs English `tessdata_fast` data plus its Apache license into
`.venv/share/tessdata`. Existing verified files are reused without a download;
size/hash mismatch fails setup. A different existing file is left untouched.
The new assets are environment data, not runtime credentials or source files.
They must be restored/verified after rebuilding a virtual environment.

PDF parsing/OCR runs in an owned native child, killed and reaped on timeout or
cancellation. Its 120-second parse deadline excludes the preceding HTTP fetch.
See [manual](USER-MANUAL.md#pdf-text-tables-and-local-ocr) for exact bounds and
[evidence](DOCUMENT-EXTRACTION-EVIDENCE-2026-09-02.md) for tested/unproved surfaces.
Fixture installer wiring is not a clean-machine installation receipt.

## Crawl lifecycle and evidence

Each bounded crawl closes its owned browser, including after cancellation or
timeout. Repeated cancellation must not abandon cleanup. A whole-crawl timeout
retains completed pages with warnings; a failed or empty page is not evidence.
Default collection/page deadlines are 120/45 seconds after admission. They do
not constitute a hard limit on cleanup duration, browser memory or every
subresource. Public navigation shares the direct HTTP origin gate; subresource
and redirect-origin scheduling remain unfinished.

No personal browser is attached or terminated. Gateway-owned imported session
cookies are read for each managed call; session changes are not written back.
Browser/crawl SDK verbose output is disabled. Explicit Chromium response-stage
redirect interception is required in addition to ordinary request guards. See
[manual](USER-MANUAL.md#7-browser-crawling) and [crawl evidence](CRAWL-TRAVERSAL-EVIDENCE-2026-09-02.md).

## Rollback

1. Stop the gateway.
2. Disable/remove only the `Halo Research Gateway` scheduled task.
3. Remove only `halo-research` host entries and skill copies; restore timestamped host config backups where applicable.
4. Preserve database, backups, vault, receipts, and browser profiles unless Scott explicitly authorizes removal.
5. Revert the two scoped DSH integration files; do not alter DSH model or verified-coder configuration.

## Research-only upgrade

See [the current scope](RESEARCH-ONLY-SCOPE.md). Old action settings are ignored. Old plans/receipts and vault entries are preserved, but email, GitHub writes, and general submissions have no executable route. Session-import approval is now under `/operator/api/imports/chrome/{plan_id}/approve`; the old actions endpoint returns 404.
