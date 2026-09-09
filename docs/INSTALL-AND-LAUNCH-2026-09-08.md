# Halo Research Gateway — installation and launch, 2026-09-08

## Result

Installed and launched the latest origin/main and v0.3.0 tag:
`562a64a48ca063f34ec42dfd4a32eb11ac578081`. Git fetch confirmed the local clean
checkout was already current. GitHub quality-gate runs for this exact SHA were
completed/successful. No source upgrade or source repair was necessary.

Repository: `C:\Users\scott\Desktop\Code\halo-research-gateway`.
Runtime/configuration: `C:\Users\scott\AppData\Local\HaloResearchGateway`.
Operator: http://127.0.0.1:8765/operator
MCP: http://127.0.0.1:8765/mcp
Health: http://127.0.0.1:8765/health

Ran the shipped installer with `-RegisterTask -Start` (not `-RegisterHosts`).
Locked dependencies and verified OCR files were already current. The installer
refreshed the canonical research skill copies and registered the existing
`Halo Research Gateway` at-login task. Gateway PID was 3804 at acceptance.
The task was observed Ready; an actual subsequent login/reboot was not tested.

## Fresh evidence

- Lock/format/lint/skill validation: PASS.
- Unit/fixture tests: 597 passed in 111.19 seconds.
- Optional DSH integration tests: 12 passed.
- Health: `ok`, service 0.3.0, result schema 1.5, database schema 3.
- Operator HTTP: 200.
- MCP smoke: exactly 14 tools; real web_fetch succeeded, 1,382-character envelope.
- Live search: exa-anonymous, 3 items.
- Live browser crawl: Crawl4AI, 1 item.
- Live PDF extraction: PyMuPDF, 1 item.
- Live Reddit search: reddit-rss, successful, 2 items.

Commands used: `scripts/Install-HaloResearch.ps1 -RegisterTask -Start`,
`uv run --locked python tests/acceptance/mcp_smoke.py`, and
`uv run --locked python tests/acceptance/live_provider_canary.py`.
These are direct MCP checks, not new model-selected DSH acceptance.

## Preservation and limits

Existing config backed up to
`C:\Users\scott\AppData\Local\HaloResearchGateway\backups\2026-09-08-install\config.toml`.
Before/after config SHA-256 was identical:
`D3D772F625C6D4A49DEF53A2B8B3E98D52826A8D43F0534E0F28D6ED4BC0E0EA`.
Vault, jobs, cache, accounts and existing configuration were retained.
Paid CAPTCHA/proxy adapters remain disabled; no account grants were added.
No DSH model/router configuration, Ollama, Sandbox or other project was changed.
DSH's previously disabled Gateway MCP entry was not re-enabled by this service
installation. Other existing MCP clients can use the endpoint immediately.

Stop only this service with `scripts/Stop-HaloResearch.ps1`; start it again with
`scripts/Start-HaloResearch.ps1`. Use the shipped ownership-aware scripts, not
blanket Python/Node process termination. This installation did not change the
source version or operator config, so no version/config rollback is needed.

## Correction, 2026-09-09

This installation ran inside the OpenAI Codex MSIX container. Windows redirected
its `%LOCALAPPDATA%\HaloResearchGateway` writes, so the config, the
`backups\2026-09-08-install\config.toml` copy and the database named above live
under `C:\Users\scott\AppData\Local\Packages\OpenAI.Codex_2p2nqsd0c76g0\LocalCache\Local\HaloResearchGateway`,
not in the real runtime root. The at-login task ran after the 2026-09-08 22:29 MDT
reboot (result 0) and started the Gateway from the real root without a config.
On 2026-09-09 the recorded config was placed in the real root and the service
was restarted. See `HALO-GATEWAY-RUNTIME-ROOT-REPAIR-2026-09-09.md`. The "login
not tested" statement above is superseded by that reboot.
