"""Optional retrieval must not bypass its operator's attempt/spend limits."""

import asyncio

import pytest
from test_optional_providers import make_registry

from halo_research_gateway.config import OptionalProviderConfig
from halo_research_gateway.providers.optional import OptionalProviderError


@pytest.mark.parametrize("cost", [-1, 0, float("nan"), float("inf"), -float("inf"), True])
async def test_invalid_estimated_cost_never_reaches_adapter_or_ledger(tmp_path, cost):
    registry, _ = make_registry(tmp_path)
    calls = []
    registry.register("captcha", "fixture", lambda **values: calls.append(values))
    error = None
    try:
        await registry.execute("captcha", "example.com", cost)
    except Exception as exc:
        error = exc
    assert isinstance(error, OptionalProviderError) and str(error) == "OPTIONAL_PROVIDER_COST_REQUIRED"
    assert not calls
    assert registry.status()["captcha"]["attempts_today"] == 0


async def test_tiny_positive_cost_reserves_at_least_one_microdollar(tmp_path):
    registry, _ = make_registry(tmp_path)
    registry.register("captcha", "fixture", lambda **values: {"ok": True})
    result = await registry.execute("captcha", "example.com", 0.00000001)
    assert result["estimated_cost_usd"] == 0.000001, "Sub-micro estimates are rounded down to free"


async def test_default_cost_comes_from_operator_policy_not_zero(tmp_path):
    registry, _ = make_registry(tmp_path)
    registry.configs["captcha"] = registry.configs["captcha"].model_copy(update={"request_cost_usd": 0.02})
    registry.register("captcha", "fixture", lambda **values: {"ok": True})
    result = await registry.execute("captcha", "example.com")
    assert result["estimated_cost_usd"] == 0.02
    assert registry.status()["captcha"]["spend_is_estimated"] is True


def test_operator_request_estimate_is_real_validated_configuration():
    config, error = None, None
    try:
        config = OptionalProviderConfig(request_cost_usd=0.02)
    except Exception as exc:
        error = exc
    assert error is None, f"Request estimate rejected as an unknown configuration field: {error}"
    assert config.request_cost_usd == 0.02


async def test_failed_or_cancelled_provider_keeps_reserved_budget(tmp_path):
    registry, _ = make_registry(tmp_path, attempts=1, spend=0.02)
    entered = asyncio.Event()

    async def pending(**values):
        entered.set()
        await asyncio.Event().wait()

    registry.register("captcha", "fixture", pending)
    task = asyncio.create_task(registry.execute("captcha", "example.com", 0.02))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    with pytest.raises(OptionalProviderError, match="ATTEMPT_BUDGET_EXHAUSTED"):
        await registry.execute("captcha", "example.com", 0.02)
    assert registry.status()["captcha"]["spend_usd_today"] == 0.02
