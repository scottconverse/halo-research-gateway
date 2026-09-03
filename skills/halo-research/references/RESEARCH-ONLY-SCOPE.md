# Halo Research Gateway: research-only contract

Effective 2026-09-02, by Scott's explicit direction. This supersedes conflicting
scope and acceptance requirements in the original v1.5 design, release notes,
handoffs, skill copies, and earlier plans. Historical evidence is not deleted.

## Purpose

Give DSH full, useful search and research: find sources, read their contents,
collect evidence, and return usable citations. The Gateway is not a general
personal assistant or an account-operation system. It does not change DSH's
native permissions, models, or development workflow.

## Keep

- Search and fallback discovery; ordinary and JavaScript-rendered page reading.
- Reddit, technical communities, documents, captions, and read-only GitHub research.
- Bounded multi-step research, jobs, cache, shared queues, pagination, and citations.
- Explicit local research targets and research authentication/managed sessions.
- Cookie-only session import into Gateway-owned profiles, with operator review.
- Optional challenge/proxy adapters used only to retrieve research sources, with
  explicit provider/domain/budget setup. They are disabled by default.

The MCP surface contains fourteen tools: `web_search`, `web_fetch`, `web_crawl`,
`reddit_search`, `reddit_thread`, `document_extract`, `deep_research`,
`github_research`, `transcript_fetch`, `community_search`, `community_thread`,
`local_fetch`, `local_crawl`, and `research_job`.

## Remove; not a future backlog

- Gmail composition, drafts, sending, and the compose OAuth preset.
- GitHub issue/comment creation, editing, and state changes; the write-App form.
- General form submission, posting, messaging, purchasing, account changes, and
  deletion plans/execution. Neither action MCP tool remains.
- General-purpose action approval/execution plumbing and its console interface.
- Whole Chrome-profile import, saved passwords, autofill, payment metadata,
  extensions, settings, browsing history, and bookmarks.

Research login-session import is not a general action API. It accepts only
cookie files and their necessary encryption metadata. It is **not site-filtered**;
use a dedicated research source profile. Existing personal data, vault records,
database tables, and historical receipts are preserved, not erased or revoked.
Legacy non-research plans cannot be approved or executed by the remaining flow.
Old `[actions]` configuration is ignored for upgrade compatibility; new import
review configuration is `[imports]`. It cannot restore removed functionality.

## Needs to be done to finish

This is the remaining research-only acceptance list, not a new feature plan.

The removal, recorded GitHub/browser/WebSocket fixes, Exa source attribution and
filter fixes, and cookie-only fixture repair are committed. Pushed checkpoint
`135cdd8` passed CI. Live MCP returned ordinary/JS pages, PDF text, captions,
Reddit search/thread and Hacker News discussion evidence. Authenticated GitHub
was proven at adapter level. These do not complete the following work:

1. **Repair the DSH integration, then prove the whole workflow.** The local
   model selected the correct Gateway search tool but DSH failed before dispatch:
   `Cannot read properties of undefined (reading 'prepare')`. Its host and agent
   loop resolve different tools-package instances and scheduler symbols.
   Approval is requested for a scoped DSH package-resolution repair/restart,
   preserving all model choices, permissions, presets and conversations. Then
   rerun discovery, pagination, multi-source reading and cited synthesis.
2. **Finish durable research jobs.** Pause/cancel, admission/argument bounds,
   state protection and honest empty/partial outcomes now pass isolated tests.
   Source checkpoints, cumulative budgets, lease renewal and bounded status now
   have regression coverage and a native process-crash/restart fixture passes.
   A live Gateway MCP job now passes pause/frozen-state/resume, cumulative
   budget checks and retained evidence pagination. DSH job use, long-running
   stress and provider cancellation still need proof;
   an already-running synchronous DDGS request cannot be forcibly cancelled.
3. **Finish research login/challenge access.** A real Chrome v10 cookie fixture
   passes; app-bound cookies and an operator-chosen real login are unproven.
   Complete visible human challenge handling and actual optional-provider crawl
   routing. Use fixtures for paid adapters unless paid use is separately approved.
4. **Finish reliability acceptance.** Verify shared concurrent clients, active
   cancellation, browser/process cleanup, startup/PID identity, restart recovery,
   response/time bounds and installation. Unit tests alone are not host acceptance.
   Three coordinator cancellation races are now fixed with regressions and a
   real loopback HTTPX disconnect/restart fixture. This does not complete broad
   provider cancellation, shutdown or installation acceptance.
   Background startup now verifies exact process identity, serializes operations,
   honors configured port/health, and cleans failed launches. Disposable native
   duplicate-start/stop/restart passes in both PowerShell versions; foreground,
   logon, browser-tree and clean-install acceptance are not covered by that test.
5. **Close source-provider coverage gaps.** Prove the actual DDGS fallback path,
   connected Gateway/DSH authenticated GitHub, larger/nested discussions, and
   honest source/coverage limits. Keep intermittent upstream throttling visible.
6. **Finish delivery.** The corrected owner-only landing page is published.
   Keep operator copies aligned, finish metadata/documentation and verify CI
   for the final revision after the remaining functional acceptance work.
   Product version remains `0.2.0`; no new release tag or package is claimed.

Optional fallback-host integrations do not justify expanding the core product.
No Gmail, publishing, shopping, account management, broad personal-data migration,
new dashboard, or general automation platform belongs in the finish list.

Recorded implementation gaps still included in that list:

- Public/local crawl depth and page limits now drive real bounded traversal;
  site scope, partial evidence, explicit scrolling, response-stage redirects,
  option-specific cache keys, profile cache policy and cleanup have regression/
  native Chrome evidence. See CRAWL-TRAVERSAL-EVIDENCE-2026-09-02.md.
- Consent/load-more/pagination-button/site-search interactions, capture artifacts,
  stealth/undetected modes and automatic anti-bot escalation remain unfinished.
  Their absent behavior is now explicit, not silently claimed successful.
- Browser subresource/redirect-origin scheduling, response-byte/peak-memory bounds,
  Chromium DNS pinning and cross-origin out-of-process iframe coverage remain open.
- `document_extract` table/OCR forwarding, page-cited native tables, isolated
  cancellation/deadline, and local English OCR are fixed and fixture-tested.
  Arbitrary scanned layouts, hard native-parser RAM bounds, DSH use and complete
  clean-install acceptance are not proved. See DOCUMENT-EXTRACTION-EVIDENCE-2026-09-02.md.
- Recognized sensitive final HTTP/non-PDF/PDF/browser citation URLs are redacted
  and not disk-cached; intermediate-hop and embedded/prose URL handling remain open.
- Snapshot retention is bounded by count, serialized bytes and idle age. Cursors
  bind immutable evidence; full collected prose survives bounded pages, and
  unavailable/oversized results fail explicitly. Native two-client MCP/exact-local
  HTTP eviction/restart and existing job recovery pass. See RESULT-RETENTION-EVIDENCE-2026-09-02.md.
- Total process/native peak memory, regular disk-cache eviction on ordinary reads,
  local/GitHub response/shared limits and arbitrary job-field bounds remain open.
- Background creation-time/duplicate-owner safeguards are fixed and native-tested;
  foreground ownership, strict wall-clock startup bounds, logon, long-running
  and clean-install acceptance remain.
- Two HTTP User-Agent strings still say `0.1`; package description/dependency
  metadata, contributing guidance and a licensing decision remain unfinished.

## Change rule

Before proposing a feature, explain what it does in plain English and how it
helps DSH find/read/cite sources. If it does not directly serve that purpose,
do not add it. New scope requires Scott's explicit decision, not an inference
from available permissions, a third-party SDK, or an old specification.
