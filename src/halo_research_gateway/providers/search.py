"""Accountless search provider with explicit provenance."""

from __future__ import annotations

import asyncio
from urllib.parse import urlsplit

from ..clock import SystemClock, rfc3339
from ..models import EvidenceItem, ProviderResult


class DdgsSearchProvider:
    def __init__(self, clock=None) -> None:
        self.clock = clock or SystemClock()

    async def search(
        self,
        query: str,
        *,
        max_results: int = 6,
        content_type: str = "web",
        include_domains: list[str] | None = None,
        exclude_domains: list[str] | None = None,
        freshness_days: int | None = None,
    ) -> ProviderResult:
        def invoke():
            from ddgs import DDGS

            ddgs = DDGS()
            if content_type == "news":
                return list(ddgs.news(query, max_results=max_results * 2))
            if content_type == "images":
                return list(ddgs.images(query, max_results=max_results * 2))
            if content_type == "videos":
                return list(ddgs.videos(query, max_results=max_results * 2))
            timelimit = None
            if freshness_days:
                timelimit = (
                    "d" if freshness_days <= 1 else "w" if freshness_days <= 7 else "m" if freshness_days <= 31 else "y"
                )
            return list(ddgs.text(query, timelimit=timelimit, max_results=max_results * 2))

        raw = await asyncio.to_thread(invoke)
        items: list[EvidenceItem] = []
        includes = {d.lower() for d in include_domains or []}
        excludes = {d.lower() for d in exclude_domains or []}
        now = rfc3339(self.clock.utcnow())
        for entry in raw:
            url = entry.get("href") or entry.get("url") or entry.get("image")
            if not url:
                continue
            host = (urlsplit(url).hostname or "").lower()
            if includes and not any(host == d or host.endswith("." + d) for d in includes):
                continue
            if any(host == d or host.endswith("." + d) for d in excludes):
                continue
            items.append(
                EvidenceItem(
                    title=entry.get("title"),
                    url=url,
                    published_at=entry.get("date"),
                    retrieved_at=now,
                    source=host,
                    snippet=entry.get("body") or entry.get("description"),
                    metadata={
                        k: v for k, v in entry.items() if k in {"duration", "publisher", "thumbnail", "width", "height"}
                    },
                )
            )
            if len(items) >= max_results:
                break
        return ProviderResult("ddgs-accountless", items, ["PROVIDER_FALLBACK_USED"], len(items))
