# DSH summary diagnostics — September 3, 2026

## Outcome

The complete DSH research workflow remains **failed/unaccepted**. Four isolated
local-model summary calls (baseline plus three proposed variants) did not produce
a trustworthy evidence checkpoint. None of the prompt/composition variants was
installed or committed as product code. A completed model request is not proof
that its summary or a final research answer is correct.

These diagnostics follow the earlier [package-identity repair](DSH-RESOLUTION-EVIDENCE-2026-09-03.md).
The separate DSH source repair at `a040de5b778c6a7efdb866fd383fce63c555a27f`
rejects auxiliary tool-call output before checkpoint replacement. That candidate
is not installed and does not check the factual accuracy of text-only summaries.
Installed DSH still uses the earlier active-request-retention patch.

## Choices and decision

Choices were to install a proposed summary change, continue similar prompt
trials, or preserve the negative results without deploying the variants. The
recommendation and action were to preserve them without deployment: unsupported
facts and progress claims survived all three variants. Do not change DSH models,
contexts, permissions, presets or ordinary tools to conceal this failed gate.

## What was actually tested

The disposable probe used DSH's actual LLM adapter and source summarizer with the
unchanged `lmstudio / halo/qwen3.6-35b-a3b` route. It supplied the selected
historical messages for compaction event 370 from the owned research session
`session-0a8ca74f-b125-4e85-a723-8f0e1a987f0e`. Each call had a 150-second abort
bound. This was replay of captured public evidence, not another full research run.
The history contains older summaries as well as direct source results; these
trials do not establish which unsupported claims first arose in which generation.

| Diagnostic | Observed model completion | Why it was rejected |
| --- | --- | --- |
| Original summary request | 22,301 ms; stop | Reported failed search and nonexistent multi-page exceptions progress. |
| Explicit evidence/findings prompt | 23,088 ms; stop | Reported unsupported earlier-page contents and three exceptions pages. |
| Extractive-evidence prompt | 27,164 ms; stop | Added nonexistent exception class names and unsupported empty-fetch/page claims; misassociated cursors. |
| Dedicated auxiliary summarizer | 41,443 ms; stop | Retained useful cancellation qualifications, but asserted six exceptions parts and continued unnecessary reading. |

The first three dispatched requests retained the 52 tool schemas from the
captured header. The dedicated request used a summary-specific system message
and omitted schemas **only inside this disposable auxiliary probe**. It did not
remove tools from DSH or modify the installed summarizer. No tool execution,
session creation/prompt/cancel, provider configuration, paid call or personal
account access occurred. Settings hashes before/after every diagnostic matched.

The captured actual research history contains 14 successful Gateway envelopes,
zero failed envelopes. The exceptions source was returned as one complete page
with `next_cursor: null`, 2,664 content characters and 4,962 serialized characters,
not the multi-page structures claimed by these summaries. The raw cursor strings
in the extractive summary existed in its input; the defect was unsupported
source/page association, not evidence of newly fabricated token bytes. Exact
substring checks also flagged altered/abridged quotations; a mismatch alone is
not proof of a false factual claim. Manual source comparison remains necessary.

## Fixture failures are separate

An initial profile guard rejected the local dummy-key configuration before any
model call. The corrected baseline reached model completion and saved its result,
then the probe exited 1 because its cleanup called nonexistent `ctx.stop`.
Cleanup was corrected to dispose the two plugin handles. A first candidate also
exited 1 before dispatch because it attempted to mutate a read-only message.
Creating a new message/options object corrected that fixture error. The three
subsequent variants exited 0 but **failed the semantic review** above. The
predispatch failure has no model-quality verdict. No failure is counted as green.

These scripts are exploratory spikes, not production changes or TDD evidence.
Their current source is not the exact prompt for every earlier attempt; each
attempt's saved `request.json` is the authoritative input for that attempt.

## Reproduction records

Working directory for model probes:
`C:\Users\scott\Desktop\Code\dsh-halo-research\_upstream\deepseek-harness`.
Commands, in order (the first two dispatched modes also had setup failures above):

```text
pnpm exec tsx 'C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/probe-dsh-summary-evidence.mjs' baseline 370
pnpm exec tsx 'C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/probe-dsh-summary-evidence.mjs' evidence 370
pnpm exec tsx 'C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/probe-dsh-summary-evidence.mjs' evidence 370 v2
pnpm exec tsx 'C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/probe-dsh-summary-evidence.mjs' evidence 370 extractive
pnpm exec tsx 'C:/Users/scott/Documents/Codex/2026-09-01/is-this-tool-plugin-real-https/outputs/probe-dsh-summary-evidence.mjs' dedicated 370
```

Do not rerun blindly: each output directory is guarded against replacement.
Raw requests, streamed chunks, model outputs, usage, settings hashes, review and
terminal records remain under the workspace `outputs\dsh-summary-evidence\`.
`tool-records.json` retains exact commands, exit codes and recorded errors;
original captured histories remain in `outputs\dsh-request-retained\`.
These machine-local artifacts are not bundled into the public repository.

## Crawl finding corrected

The current Gateway already forwards `max_depth` and `same_site_only` to its
crawler and performs bounded traversal. Inspection and the existing suite
disproved the suspected missing-forwarding defect. No crawl code was changed.

```text
uv run --locked python -m pytest -q tests/unit/test_crawl_options.py
31 passed in 12.35s
```

Advanced consent/load-more/pagination-button/site-search interactions, captures
and stealth/undetected modes remain distinct documented gaps; they must not be
confused with already-working linked-page traversal.

## Installed state and release boundary

At `2026-09-03T14:35:29Z`, Gateway health was `ok`, version `0.2.0`, start
`2026-09-03T10:29:12.730843Z`, no active jobs, five complete/one cancelled,
zero connections and idle research handoff. Both optional paid providers were
disabled with zero attempts/spend. DSH listed 131 sessions, zero running.
Installed compaction SHA256 remained
`C817D6B2B86905630A53DF1530C699D9E8F038446995FFFB162F86D94BC628EA`.
This health observation does not prove Exa availability, research quality or a
new deployment. No Gateway or DSH process was restarted.

The Gateway code checkpoint before this documentation update was
`5b558a26ec8742d872645dea12b5e794f019fce6`; its last loaded-source receipt remains
`4df0ccc4f686a872a040e3464a4783c87ca45a08`. Source and loaded runtime are separate.
No push, merge, site publication, version bump or `0.3.0` tag is justified by
these diagnostics. The [full research-only finish list](RESEARCH-ONLY-SCOPE.md)
remains active; this report closes no whole-workflow acceptance gate.
