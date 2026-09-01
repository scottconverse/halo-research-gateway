# Host tool mapping

The canonical MCP server name is `halo_research`; hosts may normalize hyphens/underscores differently.

| Host | Expected tool naming | Status/evidence requirement |
|---|---|---|
| DSH Halo planner | `mcp__halo_research__<tool>` | Primary route; must list and call tools through the live DSH composition |
| Codex Desktop/CLI on this workstation | MCP server `halo_research` | Requires a new process after config change |
| Claude Code on this workstation | MCP server `halo-research` | Verify `connected` and a real call |
| OpenCode on this workstation | MCP server `halo-research` | Verify `connected` and a real call |
| LM Studio Bionic | Host-specific MCP plus skill registration | Must be recorded as passed, blocked, or runtime unavailable |
| Cloud-only Codex/Cowork/Claude runtime | Not reachable | Architecturally out of scope without a separately designed remote bridge |

The gateway is model-independent. DSH owns planner/worker routing, contexts, reasoning, model selection, permissions, and its verified-coder gate. Gateway integration must not change those settings.

When adding or updating a host, capture the exact tool list/schema as serialized by that host, actual normalized tool names, a real call, result retention, cache behavior, and the precise client/model/context/reasoning/tool-mode profile.
