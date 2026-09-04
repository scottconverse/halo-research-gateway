# Optional DSH client integration

DSH is the first client for Halo Research Gateway, but the Gateway is not a
DSH service. The Gateway remains a Windows-only, agent/model-neutral MCP server.
Codex Desktop, Cowork/Claude, OpenCode Desktop, LM Studio Bionic, and other
compatible local MCP hosts use the same fourteen research tools directly.

This directory contains the optional DSH client integration needed for long
research turns that cross DSH automatic compaction. It does not change the
Gateway server, schemas, tool surface, model routes, permissions, planner/worker
roles, or verified-coder policy.

## Contents

- `halo-research-state/` reconstructs an authoritative research ledger from
  successful `mcp__halo_research__*` calls and results, emits a canonical
  `VERIFIED_JOB_RECEIPT` from projected DSH job results, enforces explicit
  research budgets, and checks the requested final-answer contract. The job
  receipt keeps every pause/status/resume/terminal snapshot distinct and uses
  one root `continuation_calls_total` counter.
- `halo-orchestrator/agent.cordis.yml` is the minimal client composition fragment
  that loads the verified state immediately after compaction.
- `patches/compaction-request-retention.patch` preserves the active user request
  and recorded tool progress through DSH compaction.
- `patches/invalid-summary-rejection.patch` rejects malformed tool-call summaries
  before they can replace the durable evidence stream.

The patches are exact exports of DSH commits `f709c7b` and `a040de5`. They were
tested together against the DSH `0.1.1-rc.2` source line. Review and apply them
to a clean DSH source checkout before loading the plugin; do not patch a global
package blindly.

## DSH composition

Place `halo-research-state` at a stable absolute path. In the DSH agent preset,
load it immediately after `@deepseek-ai/dsh-compaction-basic`:

```yaml
- id: halo-research-state
  name: 'file:///C:/absolute/path/to/halo-research-state/index.mjs'
```

Use the actual local path; the package intentionally contains no developer- or
machine-specific path. Loading the adapter does not narrow DSH capabilities or
authorize unrelated work.

## Verification

From the Gateway repository root:

```powershell
node --test integrations/dsh/halo-research-state/test/*.test.mjs
node integrations/dsh/halo-research-state/verify-history.mjs <saved-dsh-history.json>
```

The Node tests cover durable-envelope reconstruction, exact cursor/coverage
state, ordered job-operation receipts, checkpoint warnings, counter-
contradiction rejection, compaction injection, explicit call/time budgets,
hostile page markup, bounded answer revision, citations, and honest incomplete-
coverage disclosure.
The saved-history verifier is the release acceptance fixture, not a universal
truth checker; it deliberately returns `manualEvidenceReviewRequired: true`.

## Other clients

Codex Desktop, Cowork/Claude, OpenCode Desktop, and LM Studio Bionic do not need
this DSH adapter. Register `http://127.0.0.1:8765/mcp`, install the canonical
`halo-research` skill when the host supports skills, and restart the client so
it reloads MCP configuration. See `docs/host-integration.md`.
