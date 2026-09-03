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

The service retains the last three SQLite backups before migrations. A migration failure must leave the previous database intact and stop startup. Do not delete `gateway.db` to clear cache because it also owns provider circuits, connections, jobs, plans, and receipts.

If port 8765 is occupied, identify the owning PID and command line; do not kill it blindly. The Windows Job Object contains the gateway and descendants it launches; it does not adopt unrelated Chrome or Chromium processes.

The registered task is `Halo Research Gateway`. The 2026-09-01 recovery drill performed an ownership-checked stop, invoked the task, restored `status=ok`, and recorded task result `0x00000000`. A future recovery claim must repeat the drill against the current source/installer identity rather than relying on that historical receipt.

## Research provider setup

- Use the operator console's read-only GitHub App form for research.
- Cookie-only imported research profiles live under the gateway runtime browser directory and are copied capabilities. Never point Crawl4AI at the mutable source profile.
- CapSolver and Bright Data remain inert until the operator config names the provider (`capsolver` or `brightdata`), encrypted connection ID, exact domains, attempt ceiling, and spend ceiling.

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
