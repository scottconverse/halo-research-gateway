"""Bounded provider admission, pacing, and singleflight deduplication."""

from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, TypeVar

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


@dataclass(slots=True)
class _QueuedOperation:
    provider: str
    client: str
    operation_key: str
    operation: Callable[[], Awaitable[Any]]
    future: asyncio.Future
    waiters: int = 1
    state: str = "queued"
    task: asyncio.Task | None = None


class Coordinator:
    def __init__(self, policies: dict[str, QueuePolicy], clock=None) -> None:
        self.policies = policies
        self.clock = clock or SystemClock()
        self._pending: dict[str, int] = defaultdict(int)
        self._client_pending: dict[tuple[str, str], int] = defaultdict(int)
        self._active: dict[str, int] = defaultdict(int)
        self._queues: dict[str, dict[str, deque[_QueuedOperation]]] = defaultdict(dict)
        self._client_order: dict[str, deque[str]] = defaultdict(deque)
        self._last_served: dict[str, str] = {}
        self._last_started: dict[str, float] = defaultdict(lambda: float("-inf"))
        self._pacing_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._state_lock = asyncio.Lock()
        self._flights: dict[tuple[str, str], _QueuedOperation] = {}
        self.rejections: dict[str, int] = defaultdict(int)

    async def run(
        self,
        provider: str,
        client: str,
        operation_key: str,
        operation: Callable[[], Awaitable[T]],
    ) -> T:
        flight_key = (provider, operation_key)
        async with self._state_lock:
            item = self._flights.get(flight_key)
            if item is not None:
                item.waiters += 1
            else:
                policy = self.policies[provider]
                client_key = (provider, client)
                if (
                    self._pending[provider] >= policy.max_pending
                    or self._client_pending[client_key] >= policy.per_client_pending
                ):
                    self.rejections[provider] += 1
                    raise QueueFullError(f"{provider} queue is full")
                future = asyncio.get_running_loop().create_future()
                future.add_done_callback(lambda done: None if done.cancelled() else done.exception())
                item = _QueuedOperation(provider, client, operation_key, operation, future)
                self._flights[flight_key] = item
                self._pending[provider] += 1
                self._client_pending[client_key] += 1
                client_queue = self._queues[provider].get(client)
                if client_queue is None:
                    client_queue = deque()
                    self._queues[provider][client] = client_queue
                    self._client_order[provider].append(client)
                client_queue.append(item)
                self._dispatch_locked(provider)
        try:
            return await asyncio.shield(item.future)
        finally:
            await self._detach_waiter(item)

    async def _detach_waiter(self, item: _QueuedOperation) -> None:
        async with self._state_lock:
            item.waiters -= 1
            if item.waiters:
                return
            if item.state == "active":
                if item.task is not None:
                    item.task.cancel()
                return
            if item.state != "queued":
                return
            client_queue = self._queues[item.provider].get(item.client)
            if client_queue is not None:
                client_queue.remove(item)
                if not client_queue:
                    self._queues[item.provider].pop(item.client, None)
                    try:
                        self._client_order[item.provider].remove(item.client)
                    except ValueError:  # pragma: no cover - guarded by the state lock
                        pass
            item.state = "cancelled"
            self._pending[item.provider] -= 1
            self._client_pending[(item.provider, item.client)] -= 1
            self._flights.pop((item.provider, item.operation_key), None)
            item.future.cancel()
            self._dispatch_locked(item.provider)

    def _dispatch_locked(self, provider: str) -> None:
        policy = self.policies[provider]
        order = self._client_order[provider]
        while self._active[provider] < policy.active and order:
            if len(order) > 1 and order[0] == self._last_served.get(provider):
                order.rotate(-1)
            client = order.popleft()
            client_queue = self._queues[provider][client]
            item = client_queue.popleft()
            if client_queue:
                order.append(client)
            else:
                self._queues[provider].pop(client)
            item.state = "active"
            self._last_served[provider] = client
            self._active[provider] += 1
            item.task = asyncio.create_task(self._execute(item))

    async def _execute(self, item: _QueuedOperation) -> None:
        result = exception = None
        try:
            policy = self.policies[item.provider]
            async with self._pacing_locks[item.provider]:
                delay = policy.min_interval_seconds - (self.clock.monotonic() - self._last_started[item.provider])
                if delay > 0:
                    await self.clock.sleep(delay)
                self._last_started[item.provider] = self.clock.monotonic()
            result = await item.operation()
        except BaseException as exc:  # the shared future must settle for every operation outcome
            exception = exc
        async with self._state_lock:
            item.state = "done"
            self._active[item.provider] -= 1
            self._pending[item.provider] -= 1
            self._client_pending[(item.provider, item.client)] -= 1
            self._flights.pop((item.provider, item.operation_key), None)
            self._dispatch_locked(item.provider)
        if item.future.done():
            return
        if isinstance(exception, asyncio.CancelledError):
            item.future.cancel()
        elif exception is not None:
            item.future.set_exception(exception)
        else:
            item.future.set_result(result)

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
