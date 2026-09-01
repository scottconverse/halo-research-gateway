# Host integration matrix — 2026-09-01

| Host/runtime | Registration | Current disposition |
|---|---|---|
| DSH Halo planner | `halo_research` MCP insert in canonical and live web composition; persona routes to `mcp__halo_research__*` | Passed: real Qwen3.6 35B planner called `web_search` and completed `HALO-GATEWAY-DSH-OK` |
| DSH verified worker | Gateway remains available only through DSH's selected worker surface; gateway did not alter the verified-coder boundary | Configured by DSH policy; no separate full sixteen-tool worker claim |
| Claude Code local | User MCP `halo-research` at `http://127.0.0.1:8765/mcp` | Registered and health check reports connected; model-selected call still to be captured |
| OpenCode local | MCP `halo-research` at the same endpoint | Registered and health check reports connected; model-selected call still to be captured |
| Codex Desktop/CLI local | `[mcp_servers.halo_research]` in `C:\Users\scott\.codex\config.toml` | Installed for a new process; this running app cannot dynamically reload it |
| LM Studio Bionic local | `halo-research.url` in `C:\Users\scott\.lmstudio\mcp.json`; canonical skill in `.lmstudio\skills` | Registered without removing its filesystem MCP; Bionic UI/model call still to be captured |
| Cloud-only MCP clients | Cannot reach workstation loopback | Architecturally out of scope; installing the skill alone does not bridge localhost |

The canonical endpoint is `http://127.0.0.1:8765/mcp`. Host naming may normalize the server label; DSH's proven prefix is `mcp__halo_research__`.

DSH remains primary. Gateway integration does not own or change model IDs, 32K contexts, reasoning, slot count, permissions, planner/worker routing, reduced worker tools, protected acceptance inputs, or verifier receipts.
