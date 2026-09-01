"""Explicit live Crawl4AI canary; not part of deterministic pre-commit."""

import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


async def main():
    crawler = AsyncWebCrawler(
        config=BrowserConfig(
            headless=True,
            chrome_channel="chrome",
            channel="chrome",
            text_mode=True,
            accept_downloads=False,
        )
    )
    await crawler.start()
    try:
        result = await crawler.arun(
            url="https://example.com",
            config=CrawlerRunConfig(page_timeout=20_000),
        )
        print({"success": result.success, "status": result.status_code, "chars": len(str(result.markdown))})
        if not result.success or result.status_code != 200:
            raise SystemExit(1)
    finally:
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())
