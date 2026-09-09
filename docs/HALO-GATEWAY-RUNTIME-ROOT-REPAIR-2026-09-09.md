# Halo Research Gateway: runtime-root repair, 2026-09-09

Time: 2026-09-09 13:35 MDT. Author: Claude Fable 5.1 (session code-6c). Authorized by Scott Converse (decision A: the real runtime root is canonical).

## What was wrong

The Sep 8 install and acceptance of Gateway 0.3.0 ran inside the OpenAI Codex MSIX container. Windows redirected that process's `%LOCALAPPDATA%\HaloResearchGateway` writes into
`C:\Users\scott\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HaloResearchGateway`.
The at-logon scheduled task `Halo Research Gateway` runs outside any container. After the 2026-09-08 22:29 MDT reboot it started the Gateway from the real
`C:\Users\scott\AppData\Local\HaloResearchGateway`, which had no `config.toml`. The service fell back to built-in defaults (`__main__.py` passes `None` to `GatewayConfig.load` when the file is absent). Compared with the recorded config, the only missing setting was the `[local_targets.mission_control]` block, so `local_fetch`/`local_crawl` had no allowed local target.

## What was done

1. Copied the recorded config from the records folder,
   `Current Halo Configuration\deployments\20260903-134547\gateway-before\config.toml`,
   to `C:\Users\scott\AppData\Local\HaloResearchGateway\config.toml`.
   SHA-256 before and after: `D3D772F625C6D4A49DEF53A2B8B3E98D52826A8D43F0534E0F28D6ED4BC0E0EA` (same as the Codex-store copy, its Sep 8 backup, and the handoff record). The copy step refused to run if a file already existed; none did.
2. Stopped the running Gateway with `scripts\Stop-HaloResearch.ps1` (ownership-aware: checks pid record, repository, executable, exact start time). Old pid 3952 with listener child 14452 exited; port 8765 was confirmed free before the next step.
3. Started it with `scripts\Start-HaloResearch.ps1`, the same script the logon task runs, under Windows PowerShell 5.1 like the task. New pid 40744; listener child 35636; `run\gateway.json` rewritten (schema 2, started 2026-09-09T19:35:26Z).

Not touched: the Codex-store folder (kept as evidence), the database, vault, browser profiles, the scheduled task, DSH, LM Studio, Windows Sandbox. Nothing was committed to Git.

## Proof

- `/health`: `status ok`, version `0.3.0`, result schema `1.5`, database schema `3`, database `ok`, connections ready 0, jobs complete 5 / cancelled 1, cache entries 41 (same database as before the restart).
- `uv run --locked python tests/acceptance/mcp_smoke.py` -> `{'tools': 14, 'web_fetch': 'ok', 'chars': 1382}`, exit 0.
- Live MCP call `local_fetch target=mission_control path=/api/status` -> `ok=false`, provider `local-http`, error `UPSTREAM_UNAVAILABLE` (Mission Control on 3090 is down). The target is recognized.
- Contrast call `local_fetch target=not_a_configured_target` -> provider `local`, error `LOCAL_TARGET_NOT_ALLOWED`. Before the repair the `mission_control` target would have failed this same way.
- This Claude session's own MCP client reconnected to the restarted service and made both calls.

Limits: the Gateway `logs` folder is still empty (the service logs to its console, which the task discards). Mission Control itself is still down; that is the next item. Real logon behaviour with the config present has not been exercised since this change (the previous logon start, without config, did work).

## Where things are now

| Item | Path |
|---|---|
| Canonical runtime root | `C:\Users\scott\AppData\Local\HaloResearchGateway` |
| Live config | `...\HaloResearchGateway\config.toml` (SHA-256 D3D772F6...) |
| Database | `...\HaloResearchGateway\state\gateway.db` |
| PID record | `...\HaloResearchGateway\run\gateway.json` |
| Recorded config copy (in MANIFEST-SHA256.txt) | `Desktop\Halo Stack Research\Current Halo Configuration\deployments\20260903-134547\gateway-before\config.toml` |
| Historical Codex-store instance (do not use, do not delete) | `C:\Users\scott\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HaloResearchGateway` |

Operating rule going forward: run Gateway installs and lifecycle scripts from a shell that is NOT inside an MSIX app container (Task Scheduler, a plain terminal, or this Claude Code shell, which measured as non-virtualized). Check `AppData\Local\Packages\*\LocalCache\Local\` whenever a runtime file "verified" but cannot be found.

## Verification ledger

VERIFIED: Stop script removes only the recorded pid after ownership checks | C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Stop-HaloResearch.ps1:13
VERIFIED: ownership check compares pid, repository, executable and exact start time | C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\HaloLifecycle.ps1:32
VERIFIED: readiness check walks the listener's parent chain to the launched pid | C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\HaloLifecycle.ps1:97
VERIFIED: Start script refuses to start if the port is owned and writes the pid record | C:\Users\scott\Desktop\Code\halo-research-gateway\scripts\Start-HaloResearch.ps1:25
VERIFIED: missing config.toml means built-in defaults | C:\Users\scott\Desktop\Code\halo-research-gateway\src\halo_research_gateway\__main__.py:17
VERIFIED: local targets are read from the in-memory config, not the database | C:\Users\scott\Desktop\Code\halo-research-gateway\src\halo_research_gateway\service.py:1161
VERIFIED: recorded config defines [local_targets.mission_control] | C:\Users\scott\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HaloResearchGateway\config.toml:72
VERIFIED: new pid record shows pid 40744 started 2026-09-09T19:35:26Z | C:\Users\scott\AppData\Local\HaloResearchGateway\run\gateway.json:3
MEASURED: SHA-256 of source and placed config both D3D772F6... (Get-FileHash in scratchpad gw_repair.ps1)
MEASURED: /health, mcp_smoke output, and the two local_fetch MCP responses quoted above (this session)
UNVERIFIED: logon start with the config present - not checked
UNVERIFIED: Mission Control display behaviour after this change - not checked
