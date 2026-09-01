"""Bounded provider admission, pacing, and singleflight deduplication."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TypeVar

from .clock import SystemClock

T = TypeVar("T")


class QueueFullError(RuntimeError):
    code = "QUEUE_FULL"


@dataclass(frozen=True, slots=True)
class QueuePolicy:
    max_pending: int
    per_client_pending: int
    active: int
    min_interval_seconds: float = 0.0


class Coordinator:
    def __init__(self, policies: dict[str, QueuePolicy], clock=None) -> None:
        self.policies = policies
        self.clock = clock or SystemClock()
        self._semaphores = {name: asyncio.Semaphore(policy.active) for name, policy in policies.items()}
        self._pending: dict[str, int] = defaultdict(int)
        self._client_pending: dict[tuple[str, str], int] = defaultdict(int)
        self._last_started: dict[str, float] = defaultdict(lambda: float("-inf"))
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._flights: dict[str, asyncio.Task] = {}
        self.rejections: dict[str, int] = defaultdict(int)

    async def run(
        self,
        provider: str,
        client: str,
        operation_key: str,
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        flight = self._flights.get(operation_key)
        if flight is not None:
            return await asyncio.shield(flight)
        policy = self.policies[provider]
        key = (provider, client)
        if self._pending[provider] >= policy.max_pending or self._client_pending[key] >= policy.per_client_pending:
            self.rejections[provider] += 1
            raise QueueFullError(f"{provider} queue is full")
        self._pending[provider] += 1
        self._client_pending[key] += 1

        async def admitted() -> T:
            try:
                async with self._semaphores[provider]:
                    async with self._locks[provider]:
                        delay = policy.min_interval_seconds - (self.clock.monotonic() - self._last_started[provider])
                        if delay > 0:
                            await self.clock.sleep(delay)
                        self._last_started[provider] = self.clock.monotonic()
                    return await operation()
            finally:
                self._pending[provider] -= 1
                self._client_pending[key] -= 1

        task = asyncio.create_task(admitted())
        self._flights[operation_key] = task
        try:
            return await asyncio.shield(task)
        finally:
            if task.done() and self._flights.get(operation_key) is task:
                self._flights.pop(operation_key, None)

    def stats(self) -> dict[str, dict[str, int]]:
        return {
            name: {
                "pending": self._pending[name],
                "active_limit": policy.active,
                "pending_limit": policy.max_pending,
                "rejections": self.rejections[name],
            }
            for name, policy in self.policies.items()
        }
