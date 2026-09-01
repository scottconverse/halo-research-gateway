"""Injectable time boundary used by queues, jobs, cursors, and approvals."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime


class SystemClock:
    def utcnow(self) -> datetime:
        return datetime.now(UTC)

    def monotonic(self) -> float:
        return time.monotonic()

    async def sleep(self, seconds: float) -> None:
        await asyncio.sleep(seconds)


def rfc3339(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
