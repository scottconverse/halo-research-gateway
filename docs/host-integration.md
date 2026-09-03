# Host integration matrix — 2026-09-03

Halo Research Gateway is Windows-only and agent/model-neutral. Every client uses
the standard Streamable HTTP MCP endpoint at `http://127.0.0.1:8765/mcp` and the
same fourteen research tools. DSH is the first client, not a core dependency.

| Client/runtime | Registration | Current evidence |
|---|---|---|
| DSH Halo planner | `halo_research` MCP insert in the canonical/live web composition; DSH maps the server to `mcp__halo_research__*` | Full bounded workflow passed: eight successful calls, three distinct required sources, continuation, two automatic compactions and a supported final answer |
| DSH verified worker | Gateway remains available according to DSH's selected worker surface | Optional integration does not alter the verified-coder boundary; no broader worker-tool claim |
| Cowork / Claude Desktop or Code | User MCP `halo-research` at the canonical endpoint | Registered/connected where configured; a fresh model-selected live call remains separate acceptance |
| Codex Desktop/CLI | `[mcp_servers.halo_research]` at the canonical endpoint | Installed for a new process; a running client must reload before use, and a fresh model-selected live call remains separate acceptance |
| OpenCode Desktop | MCP `halo-research` at the canonical endpoint | Registered/connected where configured; a fresh model-selected live call remains separate acceptance |
| LM Studio Bionic | `halo-research.url` in LM Studio MCP configuration; canonical skill may also be installed | Registered without removing the filesystem MCP; Bionic UI/model selection remains separate acceptance |
| Other local MCP clients | Standard Streamable HTTP MCP | Compatible when they can reach workstation loopback and support the protocol |
| Cloud-only clients | Cannot reach workstation loopback | Out of scope unless the operator separately supplies a secure transport; installing a skill does not bridge loopback |

The optional DSH package under `integrations/dsh` contains DSH state/acceptance
logic and two reproducible upstream patches. It is not required by Codex,
Cowork/Claude, OpenCode, Bionic or another MCP client.

Gateway integration does not own or change client model IDs, context windows,
reasoning, slot count, permissions, planner/worker routing, sandboxes or verifier
policy. See [DSH workflow evidence](DSH-VERIFIED-WORKFLOW-EVIDENCE-2026-09-03.md).
