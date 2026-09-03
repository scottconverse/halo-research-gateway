# DSH verified research workflow — 2026-09-03

## Verdict

Pass for the bounded DSH end-to-end research workflow. This is client evidence,
not a claim that every registered MCP host or optional paid provider has passed
live acceptance.

## Bound evidence

- DSH session: `session-e041fd09-6d55-498a-85e5-8733e8ec9e0d`.
- Eight research tool calls produced eight successful Gateway results.
- The run fetched and cited three distinct required sources.
- It used an actually issued continuation rather than reconstructing a cursor.
- Two automatic compactions occurred and the original research request survived.
- The final answer completed in 128,443 ms, below the six-minute ceiling.
- The final answer was 139 words, below the 250-word ceiling.
- The strict history verifier passed every required check.
- Manual source-to-claim review found no unsupported claim.

The answer disclosed two incomplete reads (the URLs task documentation and the
Python packaging guide) instead of representing them as complete evidence.

## Repairs exercised

The passing run includes the request-retention repair and invalid-summary
rejection repair exported under `integrations/dsh/patches`. The reusable DSH
research-state, acceptance and history-verifier code is under
`integrations/dsh/halo-research-state`.

These client-side repairs do not alter Gateway tools, DSH model IDs, context,
reasoning, permissions, planner/worker routing or verified-coder policy.

## Remaining boundaries

- This evidence proves DSH, the first client. It does not claim a model-selected
  live tool call from every other registered client.
- Real account login/app-bound-cookie compatibility remains separate.
- CapSolver and Bright Data real paid calls were not authorized or performed.
- Broader stress, clean-OS and actual-logon acceptance remain separate.
