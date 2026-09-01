"""Disabled-by-default CapSolver and Bright Data adapters."""

from __future__ import annotations

import urllib.parse
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from ..clock import SystemClock
from ..security import validate_url
from .http_fetch import PinnedTransport, resolve_public

JsonRequester = Callable[[str, str, dict[str, str], dict[str, Any]], Awaitable[dict[str, Any]]]


def _exact_target(url: str, domain: str) -> None:
    target = validate_url(url)
    if target.host.rstrip(".").casefold() != domain.rstrip(".").casefold():
        raise ValueError("OPTIONAL_PROVIDER_TARGET_MISMATCH")


class _FixedApi:
    def __init__(self, base_url: str, requester: JsonRequester | None = None) -> None:
        self.base_url = base_url
        self._requester = requester or self._request_json

    async def _request_json(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> dict[str, Any]:
        url = self.base_url + path
        target = validate_url(url)
        address = await resolve_public(target)
        async with httpx.AsyncClient(
            transport=PinnedTransport(target, address), trust_env=False, timeout=45, follow_redirects=False
        ) as client:
            response = await client.request(method, url, headers=headers, json=body)
            response.raise_for_status()
            if len(response.content) > 20_971_520:
                raise ValueError("OPTIONAL_PROVIDER_RESPONSE_TOO_LARGE")
            return response.json()


class CapSolverAdapter(_FixedApi):
    """Create one bounded task and poll for no more than 120 seconds."""

    def __init__(self, clock=None, requester: JsonRequester | None = None) -> None:
        super().__init__("https://api.capsolver.com", requester)
        self.clock = clock or SystemClock()

    async def __call__(self, *, domain: str, secret: dict[str, str], task: dict[str, Any]) -> dict[str, Any]:
        client_key = secret.get("clientKey") or secret.get("client_key") or secret.get("api_key")
        if not client_key:
            raise PermissionError("CAPSOLVER_API_KEY_REQUIRED")
        website_url = str(task.get("websiteURL") or "")
        _exact_target(website_url, domain)
        if "callbackUrl" in task:
            raise ValueError("CAPSOLVER_CALLBACK_NOT_ALLOWED")
        created = await self._requester(
            "POST",
            "/createTask",
            {"Accept": "application/json"},
            {"clientKey": client_key, "task": task},
        )
        if created.get("errorId"):
            raise RuntimeError("CAPSOLVER_CREATE_FAILED")
        if created.get("status") == "ready":
            return {"status": "ready", "solution": created.get("solution", {})}
        task_id = str(created.get("taskId") or "")
        if not task_id:
            raise RuntimeError("CAPSOLVER_TASK_ID_MISSING")
        started = self.clock.monotonic()
        polls = 0
        while polls < 40 and self.clock.monotonic() - started < 120:
            await self.clock.sleep(3)
            polls += 1
            result = await self._requester(
                "POST",
                "/getTaskResult",
                {"Accept": "application/json"},
                {"clientKey": client_key, "taskId": task_id},
            )
            if result.get("errorId"):
                raise RuntimeError("CAPSOLVER_RESULT_FAILED")
            if result.get("status") == "ready":
                return {"status": "ready", "task_id": task_id, "solution": result.get("solution", {})}
        raise TimeoutError("CAPSOLVER_RESULT_TIMEOUT")


class BrightDataUnlockerAdapter(_FixedApi):
    """Make one synchronous, exact-target Unlocker API request."""

    def __init__(self, requester: JsonRequester | None = None) -> None:
        super().__init__("https://api.brightdata.com", requester)

    async def __call__(
        self,
        *,
        domain: str,
        secret: dict[str, str],
        url: str,
        output_format: str = "raw",
        country: str | None = None,
    ) -> dict[str, Any]:
        _exact_target(url, domain)
        api_key = secret.get("api_key") or secret.get("token")
        zone = secret.get("zone")
        if not api_key or not zone:
            raise PermissionError("BRIGHTDATA_API_KEY_AND_ZONE_REQUIRED")
        if output_format not in {"raw", "json"}:
            raise ValueError("BRIGHTDATA_FORMAT_INVALID")
        body: dict[str, Any] = {"zone": zone, "url": url, "format": output_format, "method": "GET"}
        if country:
            if len(country) != 2 or not country.isalpha():
                raise ValueError("BRIGHTDATA_COUNTRY_INVALID")
            body["country"] = country.lower()
        result = await self._requester(
            "POST",
            "/request",
            {"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            body,
        )
        return {
            "status": "complete",
            "target": urllib.parse.urlunsplit(urllib.parse.urlsplit(url)._replace(fragment="")),
            "status_code": result.get("status_code"),
            "headers": result.get("headers", {}),
            "body": result.get("body"),
        }
