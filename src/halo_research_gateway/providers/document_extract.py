"""Bounded PDF extraction with page-level citation metadata."""

from __future__ import annotations

import asyncio

from ..clock import SystemClock, rfc3339
from ..models import EvidenceItem, ProviderResult


class DocumentProvider:
    def __init__(self, fetcher, clock=None) -> None:
        self.fetcher = fetcher
        self.clock = clock or SystemClock()

    async def extract(self, url: str, pages: str | None = None) -> ProviderResult:
        current_url, target, headers, payload = await self.fetcher.download(
            url, "application/pdf,application/octet-stream;q=0.8"
        )
        media = headers.get("content-type", "").split(";", 1)[0].lower()
        if media != "application/pdf" and not url.lower().endswith(".pdf"):
            return await self.fetcher.fetch(url)

        def parse():
            try:
                import fitz
            except ImportError as exc:
                raise RuntimeError("OCR_UNAVAILABLE: install the documents extra") from exc
            doc = fitz.open(stream=payload, filetype="pdf")
            selected = _page_selection(pages, len(doc))
            return [(number + 1, doc[number].get_text("text")) for number in selected]

        parsed = await asyncio.to_thread(parse)
        now = rfc3339(self.clock.utcnow())
        items = [
            EvidenceItem(
                url=f"{current_url}#page={number}",
                retrieved_at=now,
                source=target.host,
                title=f"Page {number}",
                content=text,
                metadata={"page": number},
            )
            for number, text in parsed
        ]
        return ProviderResult("pymupdf", items, [], len(items))


def _page_selection(spec: str | None, count: int) -> list[int]:
    if not spec:
        return list(range(min(count, 300)))
    result: set[int] = set()
    for part in spec.split(","):
        if "-" in part:
            start, end = (int(x) for x in part.split("-", 1))
            result.update(range(start - 1, min(end, count)))
        else:
            result.add(int(part) - 1)
    selected = sorted(x for x in result if 0 <= x < count)
    if len(selected) > 300:
        raise ValueError("CONTENT_TOO_LARGE")
    return selected
