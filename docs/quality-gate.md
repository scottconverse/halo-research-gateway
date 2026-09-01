# Quality gate

The canonical deterministic gate is `scripts\Invoke-QualityGate.ps1`. The committed pre-commit hook and Windows GitHub Actions workflow call the same script.

The gate checks the locked dependency graph, formatting, lint, deterministic unit/fixture tests, canonical skill packaging, and stale-spec references. It must make no public request, mutate no host registration, start no model, and touch no protected DSH configuration.

Live and machine-specific acceptance remains explicit:

- `tests\acceptance\mcp_smoke.py`: real tool list, direct fetch, and complete-envelope size;
- `tests\acceptance\mcp_contract.py`: serialized cursor-only schema and signed continuation;
- `tests\acceptance\live_provider_canary.py`: anonymous search/fallback, Reddit RSS, document extraction, and Crawl4AI readiness;
- `tests\acceptance\crawl_canary.py`: real Windows JavaScript crawl;
- DSH session evidence: real local planner selection and call;
- Job Object probe: child process inheritance and kill-on-close behavior.

CI cannot prove host registrations, DPAPI under Scott's profile, installed Chrome behavior, DSH/LM Studio integration, or public upstream availability. Those exclusions are deliberate and must never be reported as CI-proven.
