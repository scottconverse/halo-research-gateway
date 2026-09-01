import sqlite3

import pytest

from halo_research_gateway.config import OptionalProviderConfig
from halo_research_gateway.connections.store import ConnectionStore
from halo_research_gateway.migrations import migrate
from halo_research_gateway.providers.optional import OptionalProviderError, OptionalProviderRegistry


def make_registry(tmp_path, enabled=True, attempts=2, spend=1.0):
    tmp_path.mkdir(parents=True, exist_ok=True)
    db = tmp_path / "gateway.db"
    migrate(str(db), str(tmp_path / "backups"))
    connections = ConnectionStore(str(db), tmp_path / "vault")
    connection = connections.create("fixture", "fixture", "api_key", {"token": "secret"})
    captcha = OptionalProviderConfig(
        enabled=enabled,
        provider="fixture",
        connection_id=connection["connection_id"],
        allowed_domains=["example.com"],
        daily_attempt_limit=attempts,
        daily_spend_limit_usd=spend,
    )
    return OptionalProviderRegistry(str(db), connections, captcha, OptionalProviderConfig()), db


@pytest.mark.asyncio
async def test_optional_provider_requires_adapter_before_spending_budget(tmp_path):
    registry, db = make_registry(tmp_path)
    with pytest.raises(OptionalProviderError, match="ADAPTER_NOT_CONFIGURED"):
        await registry.execute("captcha", "example.com", 0.10)
    with sqlite3.connect(db) as connection:
        assert connection.execute("SELECT COUNT(*) FROM provider_spend").fetchone()[0] == 0


@pytest.mark.asyncio
async def test_optional_provider_exact_domain_and_durable_budgets(tmp_path):
    registry, _ = make_registry(tmp_path, attempts=1, spend=0.25)
    registry.register("captcha", "fixture", lambda **values: {"ok": values["secret"]["token"] == "secret"})
    with pytest.raises(OptionalProviderError, match="DOMAIN_NOT_ALLOWED"):
        await registry.execute("captcha", "sub.example.com", 0.10)
    result = await registry.execute("captcha", "example.com", 0.20)
    assert result["result"] == {"ok": True}
    assert result["estimated_cost_usd"] == 0.2
    with pytest.raises(OptionalProviderError, match="ATTEMPT_BUDGET_EXHAUSTED"):
        await registry.execute("captcha", "example.com", 0.01)


def test_enabled_optional_provider_requires_complete_policy():
    with pytest.raises(ValueError, match="requires provider"):
        OptionalProviderConfig(enabled=True)
