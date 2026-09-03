"""DNS-pinned direct HTTP provider with redirect revalidation."""

from __future__ import annotations

import asyncio
import hashlib
import urllib.parse
from collections import defaultdict
from contextlib import asynccontextmanager

import httpx

from .. import __version__
from ..clock import SystemClock, rfc3339
from ..models import EvidenceItem, ProviderResult
from ..security import ParsedTarget, is_sensitive_url, redact_url, validate_redirect, validate_resolved, validate_url
from .html import extract_html

USER_AGENT = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) halo-research-gateway/{__version__} (+local-personal-research)"


class PinnedTransport(httpx.AsyncBaseTransport):
    """Connect to one validated IP while preserving HTTP Host and TLS SNI."""

    def __init__(self, target: ParsedTarget, address: str) -> None:
        self.target = target
        self.address = address
        self._transport = httpx.AsyncHTTPTransport(retries=0, trust_env=False)

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        host = self.target.host
        default = 443 if self.target.scheme == "https" else 80
        host_header = host if self.target.port == default else f"{host}:{self.target.port}"
        headers = [(k, v) for k, v in request.headers.raw if k.lower() != b"host"]
        headers.append((b"host", host_header.encode("ascii")))
        url = request.url.copy_with(host=self.address)
        extensions = dict(request.extensions)
        extensions["sni_hostname"] = host
        # Rebuild the request with async-compatible content; passing the source
        # stream object through constructs a sync ByteStream in HTTPX 0.28.
        pinned = httpx.Request(
            request.method,
            url,
            headers=headers,
            content=await request.aread(),
            extensions=extensions,
        )
        response = await self._transport.handle_async_request(pinned)
        return httpx.Response(
            response.status_code,
            headers=response.headers,
            stream=response.stream,
            extensions=response.extensions,
            request=request,
        )

    async def aclose(self) -> None:
        await self._transport.aclose()


async def resolve_public(target: ParsedTarget) -> str:
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(target.host, target.port, type=1)
    addresses = list(dict.fromkeys(info[4][0] for info in infos))
    return validate_resolved(target, addresses)


class HttpFetchProvider:
    def __init__(
        self,
        *,
        timeout: float = 30,
        max_redirects: int = 5,
        max_bytes: int = 20_971_520,
        per_origin_concurrency: int = 1,
        per_origin_interval_seconds: float = 1.0,
        clock=None,
    ) -> None:
        self.timeout = timeout
        self.max_redirects = max_redirects
        self.max_bytes = max_bytes
        self.clock = clock or SystemClock()
        self.per_origin_concurrency = per_origin_concurrency
        self.per_origin_interval_seconds = per_origin_interval_seconds
        self._origin_semaphores: dict[str, asyncio.Semaphore] = {}
        self._origin_pacing_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._origin_last_started: dict[str, float] = defaultdict(lambda: float("-inf"))

    @asynccontextmanager
    async def _origin_gate(self, target: ParsedTarget):
        origin = f"{target.scheme}://{target.host}:{target.port}"
        semaphore = self._origin_semaphores.setdefault(origin, asyncio.Semaphore(self.per_origin_concurrency))
        async with semaphore:
            async with self._origin_pacing_locks[origin]:
                delay = self.per_origin_interval_seconds - (self.clock.monotonic() - self._origin_last_started[origin])
                if delay > 0:
                    await self.clock.sleep(delay)
                self._origin_last_started[origin] = self.clock.monotonic()
            yield

    async def download(self, url: str, accept: str | None = None) -> tuple[str, ParsedTarget, dict[str, str], bytes]:
        target = validate_url(url)
        current_url = url
        for _ in range(self.max_redirects + 1):
            address = await resolve_public(target)
            transport = PinnedTransport(target, address)
            async with self._origin_gate(target):
                async with httpx.AsyncClient(
                    transport=transport,
                    trust_env=False,
                    timeout=self.timeout,
                    follow_redirects=False,
                    headers={
                        "User-Agent": USER_AGENT,
                        "Accept": accept or "text/html,application/json,text/plain,application/xml;q=0.9,*/*;q=0.2",
                    },
                ) as client:
                    async with client.stream("GET", current_url) as response:
                        if response.status_code in {301, 302, 303, 307, 308}:
                            location = response.headers.get("location")
                            if not location:
                                response.raise_for_status()
                            target = validate_redirect(target, location)
                            current_url = urllib.parse.urljoin(current_url, location)
                            continue
                        response.raise_for_status()
                        body = bytearray()
                        async for chunk in response.aiter_bytes():
                            body.extend(chunk)
                            if len(body) > self.max_bytes:
                                raise ValueError("CONTENT_TOO_LARGE")
                        return current_url, target, dict(response.headers), bytes(body)
        raise ValueError("too many redirects")

    async def fetch(self, url: str) -> ProviderResult:
        current_url, target, headers, body = await self.download(url)
        sensitive = is_sensitive_url(url) or is_sensitive_url(current_url)
        content_type = headers.get("content-type", "").split(";", 1)[0].lower()
        encoding = "utf-8"
        if "charset=" in headers.get("content-type", ""):
            encoding = headers["content-type"].split("charset=", 1)[1].split(";", 1)[0].strip()
        text = body.decode(encoding, errors="replace")
        title = None
        links: list[tuple[str, str]] = []
        if content_type in {"text/html", "application/xhtml+xml"} or "<html" in text[:500].lower():
            title, text, links = extract_html(text)
        warnings = ["SENSITIVE_URL_NOT_CACHED"] if sensitive else []
        if len(text.strip()) < 80 and content_type.startswith("text/html"):
            warnings.append("TRY_WEB_CRAWL")
        item = EvidenceItem(
            title=title,
            url=redact_url(current_url) if sensitive else current_url,
            retrieved_at=rfc3339(self.clock.utcnow()),
            source=target.host,
            content=text,
            metadata={"content_type": content_type, "links": links[:100], "sha256": hashlib.sha256(body).hexdigest()},
        )
        return ProviderResult("direct-http", [item], warnings, 1)
