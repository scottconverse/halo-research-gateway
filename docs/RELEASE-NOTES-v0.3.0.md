# Halo Research Gateway 0.3.0 release notes

Version 0.3.0 is the research-only, Windows-native multi-client release. The
source version is set; the Git tag remains pending Scott's approval.

## What changed

- DSH's complete bounded research workflow is verified across continuation and
  two automatic compactions.
- The reusable DSH client integration and exact upstream repairs are packaged in
  the Gateway repository under `integrations/dsh`.
- The Gateway contract is explicitly client-neutral standard MCP. DSH is the
  first client; Codex Desktop/CLI, Cowork and Claude Desktop/Code, OpenCode
  Desktop and LM Studio Bionic use the same endpoint and fourteen tools.
- CI now runs the DSH adapter tests and lints/builds the landing page on Windows.
- Package metadata, HTTP identity, README, user manual, landing-page source,
  implementation status and changelog are aligned at 0.3.0.

## Scope boundary

This remains a research gateway. It finds and reads evidence; it does not send
email, write GitHub issues/comments, submit general forms, purchase anything or
operate accounts. Optional research login and paid retrieval providers remain
operator-controlled and disabled by default.

## Evidence and limits

See [the DSH workflow evidence](DSH-VERIFIED-WORKFLOW-EVIDENCE-2026-09-03.md),
[host integration matrix](host-integration.md), and
[research-only finish list](RESEARCH-ONLY-SCOPE.md). A registered MCP client is
not called live-proven until its model has selected and completed a Gateway tool.
