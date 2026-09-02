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

1. **Complete and verify this removal.** Check source, MCP discovery, console,
   installed skill/docs, and the landing page. Commit scoped work; distinguish
   local tests/runtime from pushed/merged code and published documentation.
2. **Fix remaining retrieval defects.** GitHub cursor/snapshot identity; local
   browser request validation and awaited WebSocket rejection; truthful partial
   results and supported GitHub discussion/ref behavior. Add regression tests.
3. **Prove the source tools.** Search/fallback, page reading/crawling, PDFs,
   transcripts, Reddit/community, and authenticated read-only GitHub. Record
   actual responses/citations, not just that each tool appears in a list.
4. **Prove authenticated and challenged-page reading.** Validate cookie-only
   managed-session crawling with a selected research profile, profile layout and
   encryption compatibility, and visible operator challenge handling. Either
   prove optional solver/proxy routing under an explicit budget or accurately
   describe the adapters as unwired/unproven. No paid calls without authorization.
5. **Prove a complete workflow through DSH.** Discover, read multiple sources,
   follow a continuation, compare evidence, and produce a supported cited answer;
   also prove bounded deep-research/job pause/resume/recovery and honest failures.
6. **Finish reliability and delivery.** Verify concurrent clients, shared limits,
   cancellation, browser cleanup, restart/recovery, and the corrected installation.
   Align README, manual, skill, and landing page with what actually passed; record
   exact version/commit/CI/release identity and any remaining failures.

Optional fallback-host integrations do not justify expanding the core product.
No Gmail, publishing, shopping, account management, broad personal-data migration,
new dashboard, or general automation platform belongs in the finish list.

## Change rule

Before proposing a feature, explain what it does in plain English and how it
helps DSH find/read/cite sources. If it does not directly serve that purpose,
do not add it. New scope requires Scott's explicit decision, not an inference
from available permissions, a third-party SDK, or an old specification.
