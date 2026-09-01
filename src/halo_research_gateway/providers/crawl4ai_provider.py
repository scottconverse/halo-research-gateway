"""Lazy Crawl4AI adapter. Import failure degrades only browser tools."""

from __future__ import annotations

import asyncio
from urllib.parse import urlsplit

from ..clock import SystemClock, rfc3339
from ..models import EvidenceItem, ProviderResult
from ..security import validate_url


class CrawlUnavailable(RuntimeError):
    code = "CRAWL_DISABLED"


class Crawl4AIProvider:
    def __init__(self, base_directory: str, clock=None) -> None:
        self.base_directory = base_directory
        self.clock = clock or SystemClock()
        self._crawler = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._crawler is not None:
            return
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig
        except ImportError as exc:
            raise CrawlUnavailable("Crawl4AI extra is not installed") from exc
        # Playwright's Windows headless-shell build fails its ICU bootstrap on
        # this machine. The installed Chrome channel passes the same isolated
        # profile canary and does not attach to Scott's live Chrome profile.
        browser = BrowserConfig(
            headless=True,
            text_mode=True,
            browser_type="chromium",
            chrome_channel="chrome",
            channel="chrome",
            accept_downloads=False,
        )
        self._crawler = AsyncWebCrawler(config=browser, base_directory=self.base_directory)
        await self._crawler.start()

    async def close(self) -> None:
        if self._crawler is not None:
            await self._crawler.close()
            self._crawler = None

    async def crawl(
        self,
        url: str,
        *,
        max_pages: int = 1,
        mode: str = "auto",
        wait_for: str | None = None,
        profile: str | None = None,
        public: bool = True,
    ) -> ProviderResult:
        if public:
            validate_url(url)
        async with self._lock:
            await self.start()
            from crawl4ai import CacheMode, CrawlerRunConfig

            config = CrawlerRunConfig(
                cache_mode=CacheMode.BYPASS,
                wait_for=(f"css:{wait_for}" if wait_for else None),
                page_timeout=45_000,
                remove_overlay_elements=True,
                exclude_external_links=True,
                scan_full_page=max_pages > 1,
            )
            result = await self._crawler.arun(url=url, config=config)
            if not result.success:
                raise RuntimeError(result.error_message or "browser crawl failed")
            markdown = (
                result.markdown.raw_markdown if hasattr(result.markdown, "raw_markdown") else str(result.markdown)
            )
            item = EvidenceItem(
                title=(getattr(result, "metadata", {}) or {}).get("title"),
                url=getattr(result, "url", url),
                retrieved_at=rfc3339(self.clock.utcnow()),
                source=urlsplit(url).hostname,
                content=markdown,
                metadata={"mode": mode, "profile": profile, "status_code": getattr(result, "status_code", None)},
            )
            return ProviderResult("crawl4ai", [item], [], 1)
