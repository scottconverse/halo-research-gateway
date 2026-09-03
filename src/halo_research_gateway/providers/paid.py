"""Disabled-by-default CapSolver and Bright Data adapters."""

from __future__ import annotations

import asyncio
import json
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
    max_response_bytes = 20_971_520
    timeout_seconds = 45

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
        async with asyncio.timeout(self.timeout_seconds):
            address = await resolve_public(target)
            async with httpx.AsyncClient(
                transport=PinnedTransport(target, address),
                trust_env=False,
                timeout=self.timeout_seconds,
                follow_redirects=False,
            ) as client:
                async with client.stream(method, url, headers=headers, json=body) as response:
                    response.raise_for_status()
                    payload = bytearray()
                    async for chunk in response.aiter_bytes():
                        if len(payload) + len(chunk) > self.max_response_bytes:
                            raise ValueError("OPTIONAL_PROVIDER_RESPONSE_TOO_LARGE")
                        payload.extend(chunk)
        if body.get("format") == "raw":
            return {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "body": payload.decode(response.encoding or "utf-8", errors="replace"),
            }
        try:
            result = json.loads(payload)
        except (ValueError, UnicodeError):
            raise ValueError("OPTIONAL_PROVIDER_RESPONSE_INVALID") from None
        if not isinstance(result, dict):
            raise ValueError("OPTIONAL_PROVIDER_RESPONSE_INVALID")
        return result


class CapSolverAdapter(_FixedApi):
    """Create one bounded task and poll for no more than 120 seconds."""

    solve_timeout_seconds = 120

    def __init__(self, clock=None, requester: JsonRequester | None = None) -> None:
        super().__init__("https://api.capsolver.com", requester)
        self.clock = clock or SystemClock()

    async def __call__(self, *, domain: str, secret: dict[str, str], task: dict[str, Any]) -> dict[str, Any]:
        async with asyncio.timeout(self.solve_timeout_seconds):
            return await self._solve(domain=domain, secret=secret, task=task)

    async def _solve(self, *, domain: str, secret: dict[str, str], task: dict[str, Any]) -> dict[str, Any]:
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
        output_format: str = "json",
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
