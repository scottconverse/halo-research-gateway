"""Lazy Crawl4AI adapter. Import failure degrades only browser tools."""

from __future__ import annotations

import asyncio
import re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from ..clock import SystemClock, rfc3339
from ..models import EvidenceItem, LocalTarget, ProviderResult
from ..security import validate_url
from .http_fetch import resolve_public


class CrawlUnavailable(RuntimeError):
    code = "CRAWL_DISABLED"


class Crawl4AIProvider:
    def __init__(self, base_directory: str, clock=None) -> None:
        self.base_directory = base_directory
        self.clock = clock or SystemClock()
        self._crawler = None
        self._active_profile: str | None = None
        self._lock = asyncio.Lock()
        self._active_policy: LocalTarget | None = None

    async def start(self, profile: str | None = None, local_target: LocalTarget | None = None) -> None:
        if self._crawler is not None and self._active_profile == profile and self._active_policy == local_target:
            return
        if self._crawler is not None:
            await self._crawler.close()
            self._crawler = None
            self._active_profile = None
        try:
            from crawl4ai import AsyncWebCrawler, BrowserConfig
        except ImportError as exc:
            raise CrawlUnavailable("Crawl4AI extra is not installed") from exc
        # Playwright's Windows headless-shell build fails its ICU bootstrap on
        # this machine. The installed Chrome channel passes the same isolated
        # profile canary and does not attach to Scott's live Chrome profile.
        browser_values = {
            "headless": True,
            "text_mode": True,
            "browser_type": "chromium",
            "chrome_channel": "chrome",
            "channel": "chrome",
            "accept_downloads": False,
            "extra_args": ["--disable-features=ServiceWorker"],
        }
        if profile is not None:
            browser_values.update(
                use_persistent_context=True,
                user_data_dir=str(self._profile_directory(profile)),
            )
        browser = BrowserConfig(
            **browser_values,
        )
        self._crawler = AsyncWebCrawler(config=browser, base_directory=self.base_directory)

        async def guard_page(_, *, context, **__):
            async def guard_route(route, request):
                try:
                    await self._validate_browser_request(
                        request.url, local_target is None, local_target, request.method
                    )
                    await route.continue_()
                except Exception:
                    await route.abort("blockedbyclient")

            await context.route("**/*", guard_route)

            async def guard_websocket(websocket):
                await self._handle_websocket(websocket, local_target is None, local_target)

            route_websocket = getattr(context, "route_web_socket", None)
            if route_websocket is None:
                raise CrawlUnavailable("Playwright WebSocket routing is required")
            await route_websocket("**/*", guard_websocket)

        self._crawler.crawler_strategy.set_hook("on_page_context_created", guard_page)
        await self._crawler.start()
        self._active_profile = profile
        self._active_policy = local_target

    async def close(self) -> None:
        if self._crawler is not None:
            await self._crawler.close()
            self._crawler = None
            self._active_profile = None
            self._active_policy = None

    async def crawl(
        self,
        url: str,
        *,
        max_pages: int = 1,
        mode: str = "auto",
        wait_for: str | None = None,
        profile: str | None = None,
        public: bool = True,
        local_target: LocalTarget | None = None,
    ) -> ProviderResult:
        await self._validate_browser_request(url, public, local_target)
        async with self._lock:
            selected_profile = profile if mode == "managed_profile" else None
            await self.start(selected_profile, None if public else local_target)
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

    def _profile_directory(self, profile: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", profile) or profile in {".", ".."}:
            raise ValueError("BROWSER_PROFILE_INVALID")
        profile_root = (Path(self.base_directory) / "profiles").resolve()
        candidate = (profile_root / profile).resolve()
        if candidate.parent != profile_root or not candidate.is_dir():
            raise ValueError("BROWSER_PROFILE_NOT_FOUND")
        return candidate

    @staticmethod
    async def _validate_browser_request(
        url: str, public: bool, local_target: LocalTarget | None = None, method: str = "GET"
    ) -> None:
        if not public and local_target is None:
            raise ValueError("LOCAL_TARGET_REQUIRED")
        scheme = urlsplit(url).scheme.lower()
        if scheme in {"data", "blob", "about"}:
            return
        if not public:
            local_target.validate_request(url, method)
            return
        if scheme in {"ws", "wss"}:
            parts = urlsplit(url)
            url = urlunsplit(("https" if scheme == "wss" else "http", parts.netloc, parts.path, parts.query, ""))
        target = validate_url(url)
        await resolve_public(target)

    @classmethod
    async def _handle_websocket(cls, websocket, public: bool, local_target: LocalTarget | None = None) -> None:
        try:
            await cls._validate_browser_request(websocket.url, public, local_target)
            websocket.connect_to_server()
        except Exception:
            await websocket.close(code=1008, reason="Blocked by Halo egress policy")
