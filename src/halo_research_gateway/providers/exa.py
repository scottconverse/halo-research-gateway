"""Anonymous Exa MCP adapter with explicit provider identity."""

from __future__ import annotations

import json
import re
from urllib.parse import urlsplit

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from ..clock import SystemClock, rfc3339
from ..models import EvidenceItem, ProviderResult

URL_RE = re.compile(r"https?://[^\s<>\]\)\"']+")


class ExaRateLimited(RuntimeError):
    code = "RATE_LIMITED"


class ExaProvider:
    def __init__(self, url: str, clock=None) -> None:
        self.url = url
        self.clock = clock or SystemClock()

    async def search(self, query: str, max_results: int = 6) -> ProviderResult:
        async with httpx.AsyncClient(trust_env=False, timeout=30) as http:
            async with streamable_http_client(self.url, http_client=http) as streams:
                async with ClientSession(streams[0], streams[1]) as session:
                    await session.initialize()
                    result = await session.call_tool("web_search_exa", {"query": query, "numResults": max_results})
        structured = getattr(result, "structuredContent", None)
        text = "\n".join(getattr(block, "text", "") for block in getattr(result, "content", []))
        raw = structured if structured is not None else _maybe_json(text)
        if _is_rate_limited(text, raw):
            raise ExaRateLimited("anonymous Exa quota is exhausted")
        items = _normalize(raw, text, max_results, rfc3339(self.clock.utcnow()))
        return ProviderResult("exa-anonymous", items, [], len(items))


def _maybe_json(text: str):
    try:
        return json.loads(text)
    except (ValueError, TypeError):
        return None


def _is_rate_limited(text: str, raw) -> bool:
    combined = (text + " " + json.dumps(raw, ensure_ascii=False, default=str)).lower()
    return any(
        marker in combined
        for marker in (
            "hit exa's free mcp rate limit",
            "hit exa’s free mcp rate limit",
            "rate limit exceeded",
            "too many requests",
        )
    )


def _normalize(raw, text: str, limit: int, now: str) -> list[EvidenceItem]:
    candidates = []
    if isinstance(raw, dict):
        candidates = raw.get("results") or raw.get("items") or raw.get("data") or []
    elif isinstance(raw, list):
        candidates = raw
    items: list[EvidenceItem] = []
    for value in candidates:
        if not isinstance(value, dict):
            continue
        url = value.get("url") or value.get("id")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            continue
        items.append(
            EvidenceItem(
                title=value.get("title"),
                url=url,
                published_at=value.get("publishedDate") or value.get("date"),
                retrieved_at=now,
                source=urlsplit(url).hostname,
                snippet=value.get("text") or value.get("summary") or value.get("snippet"),
            )
        )
        if len(items) >= limit:
            return items
    if not items:
        for url in dict.fromkeys(URL_RE.findall(text)):
            items.append(
                EvidenceItem(url=url.rstrip(".,"), retrieved_at=now, source=urlsplit(url).hostname, snippet=text[:800])
            )
            if len(items) >= limit:
                break
    return items
