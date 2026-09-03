"""Disabled-by-default CAPTCHA/proxy provider seams with durable budgets."""

from __future__ import annotations

import inspect
import math
import sqlite3
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal
from typing import Any

from ..config import OptionalProviderConfig
from ..connections.store import ConnectionStore

Adapter = Callable[..., dict[str, Any] | Awaitable[dict[str, Any]]]


class OptionalProviderError(RuntimeError):
    pass


class OptionalProviderRegistry:
    """Own adapters and enforce exact-domain, attempt, and spend policy."""

    def __init__(self, db_path: str, connections: ConnectionStore, captcha, proxy) -> None:
        self.db_path = db_path
        self.connections = connections
        self.configs: dict[str, OptionalProviderConfig] = {"captcha": captcha, "proxy": proxy}
        self.adapters: dict[tuple[str, str], Adapter] = {}

    def register(self, kind: str, provider: str, adapter: Adapter) -> None:
        if kind not in self.configs or not provider.strip():
            raise ValueError("INVALID_OPTIONAL_PROVIDER")
        self.adapters[(kind, provider)] = adapter

    def status(self) -> dict[str, dict[str, Any]]:
        return {kind: self._status_one(kind, policy) for kind, policy in self.configs.items()}

    def _status_one(self, kind: str, policy: OptionalProviderConfig) -> dict[str, Any]:
        today = datetime.now(UTC).date().isoformat()
        attempts = spend = 0
        if policy.provider:
            with sqlite3.connect(self.db_path) as db:
                row = db.execute(
                    "SELECT attempts,spend_microusd FROM provider_spend "
                    "WHERE provider_kind=? AND provider_name=? AND usage_day=?",
                    (kind, policy.provider, today),
                ).fetchone()
            if row:
                attempts, spend = row
        return {
            "enabled": policy.enabled,
            "provider": policy.provider,
            "adapter_ready": bool(policy.provider and (kind, policy.provider) in self.adapters),
            "allowed_domain_count": len(policy.allowed_domains),
            "attempts_today": attempts,
            "attempt_limit": policy.daily_attempt_limit,
            "spend_usd_today": spend / 1_000_000,
            "spend_limit_usd": policy.daily_spend_limit_usd,
            "request_cost_usd": policy.request_cost_usd,
            "spend_is_estimated": True,
        }

    async def execute(
        self, kind: str, domain: str, estimated_cost_usd: float | None = None, **values
    ) -> dict[str, Any]:
        policy = self.configs.get(kind)
        if policy is None:
            raise OptionalProviderError("OPTIONAL_PROVIDER_KIND_UNKNOWN")
        if not policy.enabled:
            raise OptionalProviderError("OPTIONAL_PROVIDER_DISABLED")
        assert policy.provider and policy.connection_id
        adapter = self.adapters.get((kind, policy.provider))
        if adapter is None:
            raise OptionalProviderError("OPTIONAL_PROVIDER_ADAPTER_NOT_CONFIGURED")
        normalized = domain.rstrip(".").lower()
        allowed = {item.rstrip(".").lower() for item in policy.allowed_domains}
        if normalized not in allowed:
            raise OptionalProviderError("OPTIONAL_PROVIDER_DOMAIN_NOT_ALLOWED")
        cost = policy.request_cost_usd if estimated_cost_usd is None else estimated_cost_usd
        if type(cost) not in {int, float} or not math.isfinite(cost) or not 0 < cost <= 10000:
            raise OptionalProviderError("OPTIONAL_PROVIDER_COST_REQUIRED")
        estimated_microusd = int((Decimal(str(cost)) * 1_000_000).to_integral_value(rounding=ROUND_CEILING))
        self._admit(kind, policy, estimated_microusd)
        secret = self.connections.secret(policy.connection_id)
        result = adapter(domain=normalized, secret=secret, **values)
        if inspect.isawaitable(result):
            result = await result
        return {
            "provider_kind": kind,
            "provider": policy.provider,
            "domain": normalized,
            "estimated_cost_usd": estimated_microusd / 1_000_000,
            "result": result,
        }

    def _admit(self, kind: str, policy: OptionalProviderConfig, estimated_microusd: int) -> None:
        today = datetime.now(UTC).date().isoformat()
        limit_microusd = int(
            (Decimal(str(policy.daily_spend_limit_usd)) * 1_000_000).to_integral_value(rounding=ROUND_FLOOR)
        )
        with sqlite3.connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT attempts,spend_microusd FROM provider_spend "
                "WHERE provider_kind=? AND provider_name=? AND usage_day=?",
                (kind, policy.provider, today),
            ).fetchone()
            attempts, spend = row or (0, 0)
            if attempts >= policy.daily_attempt_limit:
                raise OptionalProviderError("OPTIONAL_PROVIDER_ATTEMPT_BUDGET_EXHAUSTED")
            if spend + estimated_microusd > limit_microusd:
                raise OptionalProviderError("OPTIONAL_PROVIDER_SPEND_BUDGET_EXHAUSTED")
            db.execute(
                "INSERT INTO provider_spend(provider_kind,provider_name,usage_day,attempts,spend_microusd,updated_at) "
                "VALUES(?,?,?,?,?,?) ON CONFLICT(provider_kind,provider_name,usage_day) DO UPDATE SET "
                "attempts=excluded.attempts,spend_microusd=excluded.spend_microusd,updated_at=excluded.updated_at",
                (
                    kind,
                    policy.provider,
                    today,
                    attempts + 1,
                    spend + estimated_microusd,
                    datetime.now(UTC).isoformat(),
                ),
            )
