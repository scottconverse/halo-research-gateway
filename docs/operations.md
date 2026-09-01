# Operations

## Runtime locations

- Repository: `C:\Users\scott\Desktop\Code\halo-research-gateway`
- Runtime root: `C:\Users\scott\AppData\Local\HaloResearchGateway`
- Operator config: `C:\Users\scott\AppData\Local\HaloResearchGateway\config.toml`
- Database: `C:\Users\scott\AppData\Local\HaloResearchGateway\state\gateway.db`
- Backups: `C:\Users\scott\AppData\Local\HaloResearchGateway\state\backups`
- Vault: `C:\Users\scott\AppData\Local\HaloResearchGateway\vault`
- Browser data: `C:\Users\scott\AppData\Local\HaloResearchGateway\browser`
- PID identity: `C:\Users\scott\AppData\Local\HaloResearchGateway\run\gateway.json`

Start and stop only with the repository scripts. The stop script verifies executable and command-line identity before stopping the recorded PID. Do not stop another Python, browser, LM Studio, DSH, or Ollama process by name.

## Recovery

The service retains the last three SQLite backups before migrations. A migration failure must leave the previous database intact and stop startup. Do not delete `gateway.db` to clear cache because it also owns provider circuits, connections, jobs, plans, and receipts.

If port 8765 is occupied, identify the owning PID and command line; do not kill it blindly. The Windows Job Object contains the gateway and descendants it launches; it does not adopt unrelated Chrome or Chromium processes.

## Rollback

1. Stop the gateway.
2. Disable/remove only the `Halo Research Gateway` scheduled task.
3. Remove only `halo-research` host entries and skill copies; restore timestamped host config backups where applicable.
4. Preserve database, backups, vault, receipts, and browser profiles unless Scott explicitly authorizes removal.
5. Revert the two scoped DSH integration files; do not alter DSH model or verified-coder configuration.
