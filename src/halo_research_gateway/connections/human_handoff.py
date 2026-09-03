"""One explicitly operator-started research login, never a model action tool."""

from __future__ import annotations

import asyncio
import uuid

from ..security import validate_url


class HumanHandoff:
    def __init__(self, crawler):
        self.crawler = crawler
        self._task: asyncio.Task | None = None
        self._done = asyncio.Event()
        self._state = {"state": "idle"}

    def status(self) -> dict:
        return dict(self._state)

    def invalidate(self, profile: str) -> None:
        if self._state.get("profile") == profile and (self._task is None or self._task.done()):
            self._state = {"state": "idle"}

    async def begin(self, url: str, profile: str) -> dict:
        if self._task is not None and not self._task.done():
            raise RuntimeError("RESEARCH_SESSION_BUSY")
        if not self.crawler.limits.enabled:
            raise ValueError("CRAWL_DISABLED")
        target = validate_url(url)
        self.crawler._profile_directory(profile)
        self._done = asyncio.Event()
        self._state = {
            "session_id": str(uuid.uuid4()),
            "state": "opening",
            "origin": target.origin,
            "profile": profile,
            "timeout_seconds": 120,
        }
        # No await between the single-session check and reservation.
        self._task = asyncio.create_task(self._run(url, profile))
        return self.status()

    async def _run(self, url, profile):
        def ready():
            self._state["state"] = "waiting_for_operator"

        try:
            await self.crawler.human_handoff(url, profile, self._done, ready)
            self._state["state"] = "ready_to_retry"
        except asyncio.CancelledError:
            self._state["state"] = "cancelled"
        except TimeoutError:
            self._state.update(state="timed_out", error="RESEARCH_SESSION_TIMEOUT")
        except Exception:
            # Browser exception strings can contain URLs and authentication data.
            self._state.update(state="failed", error="RESEARCH_SESSION_FAILED")

    async def finish(self, session_id: str, *, cancel: bool = False) -> dict:
        if session_id != self._state.get("session_id") or self._task is None or self._task.done():
            raise RuntimeError("RESEARCH_SESSION_STALE")
        if cancel:
            self._task.cancel()
        else:
            if self._state["state"] != "waiting_for_operator":
                raise RuntimeError("RESEARCH_SESSION_NOT_READY")
            self._done.set()
        await asyncio.gather(self._task, return_exceptions=True)
        # A task cancelled before its first instruction cannot update its state.
        if self._task.cancelled():
            self._state["state"] = "cancelled"
        return self.status()

    async def close(self) -> None:
        if self._task is not None and not self._task.done():
            await self.finish(self._state["session_id"], cancel=True)
