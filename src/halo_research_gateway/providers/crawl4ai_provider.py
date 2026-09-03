"""Lazy Crawl4AI adapter. Import failure degrades only browser tools."""

from __future__ import annotations

import asyncio
import contextlib
import copy
import json
import re
from collections import deque
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urljoin, urlsplit, urlunsplit

from ..clock import SystemClock, rfc3339
from ..config import CrawlConfig
from ..models import EvidenceItem, LocalTarget, ProviderResult
from ..security import is_sensitive_url, redact_url, validate_url
from .challenge_tokens import ChallengeTokenError, solve_widget
from .deep import canonical_url
from .html import extract_html
from .http_fetch import resolve_public
from .optional import OptionalProviderError


class CrawlUnavailable(RuntimeError):
    code = "CRAWL_DISABLED"


class CrawlSourceError(RuntimeError):
    """An actionable, non-secret retrieval failure, retained for partial crawls."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


async def _settle_driver_task(task):
    cancelled = False
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            cancelled = True
    return task.result(), cancelled


@contextlib.asynccontextmanager
async def _playwright_session():
    """Pair driver startup with shutdown even when opening is cancelled."""
    from playwright.async_api import async_playwright

    manager = async_playwright()
    driver, cancelled = await _settle_driver_task(asyncio.create_task(manager.__aenter__()))
    try:
        if cancelled:
            raise asyncio.CancelledError
        yield driver
    finally:
        _, stopped_cancelled = await _settle_driver_task(asyncio.create_task(manager.__aexit__(None, None, None)))
        if stopped_cancelled:
            raise asyncio.CancelledError


def is_challenge_page(html: str, headers=None) -> bool:
    """Recognize strong gate-page signals, not articles mentioning CAPTCHAs."""
    if any(
        str(key).lower() == "cf-mitigated" and str(value).lower() == "challenge"
        for key, value in (headers or {}).items()
    ):
        return True
    if not html:
        return False
    from selectolax.parser import HTMLParser

    tree = HTMLParser(html[:1_000_000])
    title = tree.css_first("title")
    title = " ".join(title.text().lower().split()) if title else ""
    gate_title = title in {
        "just a moment...",
        "just a moment",
        "verify you are human",
        "robot check",
        "security verification",
        "attention required! | cloudflare",
    }
    marker = tree.css_first(
        'script[src*="/cdn-cgi/challenge-platform/"], form#challenge-form, #cf-challenge-running, '
        '#challenge-running, iframe[src*="challenges.cloudflare.com"], .g-recaptcha, .h-captcha, .cf-turnstile'
    )
    return gate_title and marker is not None


class Crawl4AIProvider:
    def __init__(self, base_directory: str, clock=None, *, limits: CrawlConfig | None = None, origin_gate=None) -> None:
        self.base_directory = base_directory
        self.clock = clock or SystemClock()
        self.limits = limits or CrawlConfig()
        self.origin_gate = origin_gate
        self._crawler = None
        self._active_profile: str | None = None
        self._lock = asyncio.Lock()
        self._active_policy: LocalTarget | None = None
        self._navigation_host: str | None = None
        self.optional_providers = None
        self._human_cookies: tuple[str, list[dict]] | None = None

    async def start(
        self, profile: str | None = None, local_target: LocalTarget | None = None, *, navigation_host: str | None = None
    ) -> None:
        if (
            self._crawler is not None
            and self._active_profile == profile
            and self._active_policy == local_target
            and self._navigation_host == navigation_host
        ):
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
            "verbose": False,
            "extra_args": ["--disable-features=ServiceWorker"],
        }
        if profile is not None:
            # Crawl4AI 0.9.3's persistent path ignores chrome_channel and starts
            # bundled Chromium. Let installed Chrome read its own encrypted
            # cookie copy, then seed the isolated research context in memory.
            browser_values["cookies"] = await self._profile_cookies(profile)
        browser = BrowserConfig(
            **browser_values,
        )
        self._crawler = AsyncWebCrawler(config=browser, base_directory=self.base_directory)

        async def guard_page(page, *, context, **__):
            await self._guard_page(page, context, local_target, navigation_host)

        self._crawler.crawler_strategy.set_hook("on_page_context_created", guard_page)
        await self._crawler.start()
        self._active_profile = profile
        self._active_policy = local_target
        self._navigation_host = navigation_host

    async def _guard_page(self, page, context, local_target=None, navigation_host=None, *, single_page=False) -> None:
        async def guard_route(route, request):
            try:
                if single_page and request.frame.page != page:
                    raise ValueError("RESEARCH_SESSION_SINGLE_PAGE")
                if (
                    navigation_host is not None
                    and request.is_navigation_request()
                    and request.frame == page.main_frame
                    and urlsplit(request.url).hostname != navigation_host
                ):
                    raise ValueError("CRAWL_NAVIGATION_SCOPE")
                await self._validate_browser_request(request.url, local_target is None, local_target, request.method)
                await route.continue_()
            except Exception:
                await route.abort("blockedbyclient")

        await context.route("**/*", guard_route)
        # Playwright route handlers do not see every HTTP redirect hop.
        # Pause redirect responses before Chromium follows their Location.
        cdp = await context.new_cdp_session(page)
        main_frame = (await cdp.send("Page.getFrameTree"))["frameTree"]["frame"]["id"]

        async def guard_response(event):
            request_id = event["requestId"]
            try:
                if event.get("responseStatusCode") in {301, 302, 303, 307, 308}:
                    headers = {value["name"].lower(): value["value"] for value in event.get("responseHeaders", [])}
                    if headers.get("location"):
                        destination = urljoin(event["request"]["url"], headers["location"])
                        if (
                            navigation_host is not None
                            and event.get("frameId") == main_frame
                            and event.get("resourceType") == "Document"
                            and urlsplit(destination).hostname != navigation_host
                        ):
                            raise ValueError("CRAWL_NAVIGATION_SCOPE")
                        async with asyncio.timeout(5):
                            await self._validate_browser_request(
                                destination,
                                local_target is None,
                                local_target,
                                event["request"].get("method", "GET"),
                            )
                await cdp.send("Fetch.continueRequest", {"requestId": request_id})
            except Exception:
                with contextlib.suppress(Exception):
                    await cdp.send("Fetch.failRequest", {"requestId": request_id, "errorReason": "BlockedByClient"})

        cdp.on("Fetch.requestPaused", guard_response)
        await cdp.send("Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Response"}]})

        async def guard_websocket(websocket):
            await self._handle_websocket(websocket, local_target is None, local_target)

        route_websocket = getattr(context, "route_web_socket", None)
        if route_websocket is None:
            raise CrawlUnavailable("Playwright WebSocket routing is required")
        await route_websocket("**/*", guard_websocket)

    async def close(self) -> None:
        async with self._lock:
            await self._settle_close()
            self._human_cookies = None

    async def human_handoff(self, url: str, profile: str, done: asyncio.Event, ready) -> None:
        """Let the operator handle one public login; retain only temporary cookies.

        Does not claim that a challenge was solved. Callers must retry the read.
        No browser interaction primitives or cookies are returned to a model.
        """
        validate_url(url)
        self._profile_directory(profile)
        cookies = None
        async with asyncio.timeout(min(120, self.limits.job_timeout_seconds)):
            async with self._lock:
                await self._validate_browser_request(url, True)
                seed = await self._profile_cookies(profile)
                async with _playwright_session() as playwright:
                    browser = await playwright.chromium.launch(
                        channel="chrome",
                        headless=False,
                        args=["--disable-background-networking", "--disable-sync", "--no-first-run"],
                    )
                    try:
                        context = await browser.new_context(accept_downloads=False, service_workers="block")
                        await context.add_cookies(seed)
                        page = await context.new_page()
                        await self._guard_page(page, context, single_page=True)
                        closed = False

                        def page_closed(*_):
                            nonlocal closed
                            closed = True
                            done.set()

                        async def close_popup(popup):
                            if popup != page:
                                await popup.close()

                        context.on("page", close_popup)
                        page.on("close", page_closed)
                        await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                        ready()
                        await done.wait()
                        if closed:
                            raise ValueError("RESEARCH_SESSION_WINDOW_CLOSED")
                        cookies = await context.cookies()
                        if len(cookies) > 5000 or len(json.dumps(cookies).encode()) > 2_097_152:
                            raise ValueError("RESEARCH_SESSION_TOO_LARGE")
                    finally:
                        await browser.close()
                # Replace the one retained in-memory session only after successful cleanup.
                self._human_cookies = (profile, copy.deepcopy(cookies))

    async def _settle_close(self) -> None:
        task = asyncio.create_task(self._close_browser())
        cancelled = False
        while not task.done():
            try:
                await asyncio.shield(task)
            except asyncio.CancelledError:
                cancelled = True
        task.result()
        if cancelled:
            raise asyncio.CancelledError

    async def _close_browser(self) -> None:
        if self._crawler is not None:
            await self._crawler.close()
            self._crawler = None
            self._active_profile = None
            self._active_policy = None
            self._navigation_host = None

    async def crawl(
        self,
        url: str,
        *,
        max_pages: int = 1,
        max_depth: int = 0,
        same_site_only: bool = True,
        mode: str = "auto",
        wait_for: str | None = None,
        profile: str | None = None,
        public: bool = True,
        local_target: LocalTarget | None = None,
        interaction: str = "none",
        capture: str = "none",
    ) -> ProviderResult:
        if (
            type(max_pages) is not int
            or not 1 <= max_pages <= min(self.limits.max_pages, 25)
            or type(max_depth) is not int
            or not 0 <= max_depth <= min(self.limits.max_depth, 3)
        ):
            raise ValueError("CRAWL_LIMIT_INVALID")
        if mode not in {"auto", "standard", "managed_profile"}:
            raise ValueError("CRAWL_MODE_UNAVAILABLE")
        if interaction not in {"none", "scroll"}:
            raise ValueError("CRAWL_INTERACTION_UNAVAILABLE")
        if capture != "none":
            raise ValueError("CRAWL_CAPTURE_UNAVAILABLE")
        if mode == "managed_profile" and not profile:
            raise ValueError("BROWSER_PROFILE_REQUIRED")
        if profile is not None and mode != "managed_profile":
            raise ValueError("BROWSER_PROFILE_REQUIRES_MANAGED_MODE")
        if wait_for is not None:
            try:
                import soupsieve

                if not isinstance(wait_for, str) or not 1 <= len(wait_for) <= 1024:
                    raise ValueError("invalid selector length")
                soupsieve.compile(wait_for)
            except Exception:
                raise ValueError("CRAWL_SELECTOR_INVALID") from None
        root = canonical_url(url)
        if root is None:
            raise ValueError("CRAWL_URL_INVALID")
        items, warnings = [], []
        async with self._lock:
            try:
                async with asyncio.timeout(self.limits.job_timeout_seconds):
                    await self._validate_browser_request(root, public, local_target)
                    await self.start(
                        profile if mode == "managed_profile" else None,
                        None if public else local_target,
                        navigation_host=urlsplit(root).hostname if same_site_only else None,
                    )
                    await self._collect_pages(
                        root,
                        max_pages,
                        max_depth,
                        same_site_only,
                        mode,
                        wait_for,
                        profile,
                        public,
                        local_target,
                        interaction,
                        items,
                        warnings,
                    )
            except TimeoutError:
                if not items:
                    raise RuntimeError("CRAWL_TIMEOUT") from None
                warnings.append("CRAWL_TIMEOUT")
            finally:
                await self._settle_close()
        if not items:
            precise = next(
                (
                    value
                    for value in reversed(warnings)
                    if value.startswith(("CRAWL_CHALLENGE", "OPTIONAL_PROVIDER_", "PROXY_"))
                ),
                None,
            )
            raise RuntimeError(precise or "CRAWL_NO_EVIDENCE")
        return ProviderResult("crawl4ai", items, list(dict.fromkeys(warnings)), len(items))

    async def _collect_pages(
        self,
        root,
        max_pages,
        max_depth,
        same_site_only,
        mode,
        wait_for,
        profile,
        public,
        local_target,
        interaction,
        items,
        warnings,
    ):
        from crawl4ai import CacheMode, CrawlerRunConfig

        frontier, seen, visited = deque([(root, 0)]), {root}, set()
        attempts, remaining_chars = 0, 400_000
        while frontier and attempts < max_pages:
            current, depth = frontier.popleft()
            if current in visited:
                continue
            attempts += 1
            for item in items:
                item.metadata.update({"attempted_pages": attempts, "returned_pages": len(items)})
            try:
                await self._validate_browser_request(current, public, local_target)
                captcha = {}
                registry = self.optional_providers
                if registry is not None and registry.configs["captcha"].enabled:
                    self._crawler.crawler_strategy.set_hook("after_goto", None)
                if (
                    registry is not None
                    and registry.configs["captcha"].enabled
                    and public
                    and mode == "auto"
                    and profile is None
                    and interaction == "none"
                    and not any(is_sensitive_url(value) for value in (root, current))
                ):

                    async def validate_solver_url(value):
                        if is_sensitive_url(value):
                            raise ChallengeTokenError("CRAWL_CHALLENGE_REQUIRED")
                        await self._validate_browser_request(value, True)
                        if same_site_only and urlsplit(value).hostname != urlsplit(root).hostname:
                            raise ChallengeTokenError("CRAWL_CHALLENGE_CHANGED")
                        return validate_url(value)

                    async def solver_hook(page, *, response=None, registry=registry, captcha=captcha, **_):
                        try:
                            captcha.update(
                                await solve_widget(
                                    page, registry, validate_solver_url, is_challenge_page, response, wait_for
                                )
                            )
                        except (ChallengeTokenError, OptionalProviderError) as exc:
                            captcha["error"] = str(exc)
                        except asyncio.CancelledError:
                            raise
                        except TimeoutError:
                            raise
                        except Exception:
                            captcha["error"] = "CRAWL_CHALLENGE_SOLVER_FAILED"
                        return page

                    self._crawler.crawler_strategy.set_hook("after_goto", solver_hook)
                config = CrawlerRunConfig(
                    verbose=False,
                    cache_mode=CacheMode.BYPASS,
                    wait_for=(f"css:{wait_for}" if wait_for else None),
                    page_timeout=int(self.limits.page_timeout_seconds * 1000),
                    remove_overlay_elements=True,
                    exclude_external_links=same_site_only,
                    scan_full_page=interaction == "scroll",
                    max_scroll_steps=5,
                    scroll_delay=0.2,
                )
                async with asyncio.timeout(self.limits.page_timeout_seconds):
                    gate = (
                        self.origin_gate(validate_url(current))
                        if public and self.origin_gate
                        else contextlib.nullcontext()
                    )
                    async with gate:
                        result = await self._crawler.arun(url=current, config=config)
                        if captcha.get("error"):
                            raise CrawlSourceError(captcha["error"])
                        if captcha.get("applied"):
                            title, content, links = extract_html(captcha["html"])
                            result = SimpleNamespace(
                                success=200 <= captcha["status"] < 300,
                                status_code=captcha["status"],
                                url=captcha["url"],
                                html=captcha["html"],
                                markdown=content,
                                metadata={"title": title},
                                links={
                                    "internal": [{"href": urljoin(captcha["url"], href)} for _, href in links[:250]],
                                    "external": [],
                                },
                            )
                            warnings.append("CAPTCHA_RETRIEVAL_USED")
                        result_url = (
                            canonical_url(getattr(result, "redirected_url", None) or getattr(result, "url", current))
                            or current
                        )
                        await self._validate_browser_request(result_url, public, local_target)
                        if is_challenge_page(
                            getattr(result, "html", "") or "",
                            None if captcha.get("applied") else getattr(result, "response_headers", None),
                        ):
                            if (
                                not public
                                or mode != "auto"
                                or profile is not None
                                or interaction != "none"
                                or any(is_sensitive_url(value) for value in (root, current, result_url))
                            ):
                                raise CrawlSourceError("CRAWL_CHALLENGE_REQUIRED")
                            result = await self._proxy_page(result_url, wait_for)
                            warnings.extend(result.retrieval_warnings)
                if not result.success or (getattr(result, "status_code", None) or 200) >= 400:
                    raise RuntimeError("CRAWL_PAGE_FAILED")
                result_url = (
                    canonical_url(getattr(result, "redirected_url", None) or getattr(result, "url", current)) or current
                )
                await self._validate_browser_request(result_url, public, local_target)
            except TimeoutError:
                warnings.append("CRAWL_PAGE_TIMEOUT")
                continue
            except CrawlSourceError as exc:
                warnings.append(exc.code)
                continue
            except Exception:
                warnings.append("CRAWL_PAGE_FAILED")
                continue
            if result_url in visited:
                continue
            visited.update((current, result_url))
            markdown = (
                result.markdown.raw_markdown if hasattr(result.markdown, "raw_markdown") else str(result.markdown or "")
            )
            token = captcha.get("token")
            if token:
                markdown = markdown.replace(token, "[redacted challenge token]")
                if token in result_url:
                    warnings.append("CRAWL_CHALLENGE_TOKEN_IN_URL")
                    continue
            bounded = markdown[: min(50_000, remaining_chars)]
            if len(bounded) < len(markdown):
                warnings.append("CRAWL_CONTENT_TRUNCATED")
            remaining_chars -= len(bounded)
            sensitive = is_sensitive_url(root) or is_sensitive_url(current) or is_sensitive_url(result_url)
            if sensitive:
                warnings.append("SENSITIVE_URL_NOT_CACHED")
            if bounded.strip():
                items.append(
                    EvidenceItem(
                        title=str((getattr(result, "metadata", {}) or {}).get("title") or "").replace(
                            token, "[redacted challenge token]"
                        )[:1000]
                        if token
                        else str((getattr(result, "metadata", {}) or {}).get("title") or "")[:1000],
                        url=redact_url(result_url) if sensitive else result_url,
                        retrieved_at=rfc3339(self.clock.utcnow()),
                        source=urlsplit(result_url).hostname,
                        content=bounded,
                        metadata={
                            "mode": "managed_profile" if mode == "managed_profile" else "standard",
                            "requested_mode": mode,
                            "authenticated_source": mode == "managed_profile",
                            "interaction": interaction,
                            "depth": depth,
                            "status_code": getattr(result, "status_code", None),
                            **getattr(result, "retrieval_metadata", {}),
                            **(
                                {"mode": "captcha", "retrieval_provider": "capsolver"} if captcha.get("applied") else {}
                            ),
                        },
                    )
                )
            else:
                warnings.append("CRAWL_EMPTY_PAGE")
            if depth < max_depth:
                links = getattr(result, "links", {}) or {}
                candidates = [*links.get("internal", [])[:250], *links.get("external", [])[:250]]
                if len(links.get("internal", [])) + len(links.get("external", [])) > 250:
                    warnings.append("CRAWL_LINK_LIMIT_REACHED")
                for link in candidates[:250]:
                    if token and token in str(link.get("href", "")):
                        warnings.append("CRAWL_CHALLENGE_TOKEN_IN_URL")
                        continue
                    candidate = canonical_url(link.get("href", ""), result_url)
                    if not candidate or candidate in seen:
                        continue
                    if same_site_only and urlsplit(candidate).hostname != urlsplit(root).hostname:
                        continue
                    try:
                        await self._validate_browser_request(candidate, public, local_target)
                    except Exception:
                        warnings.append("CRAWL_LINK_BLOCKED")
                        continue
                    if len(seen) >= 250:
                        warnings.append("CRAWL_LINK_LIMIT_REACHED")
                        break
                    seen.add(candidate)
                    frontier.append((candidate, depth + 1))
            if remaining_chars == 0:
                warnings.append("CRAWL_CONTENT_TRUNCATED")
                break
        if frontier:
            warnings.append("CRAWL_PAGE_LIMIT_REACHED")
        for item in items:
            item.metadata.update({"attempted_pages": attempts, "returned_pages": len(items)})

    async def _proxy_page(self, url: str, wait_for: str | None):
        registry = self.optional_providers
        if registry is None or not registry.configs["proxy"].enabled:
            raise CrawlSourceError("CRAWL_CHALLENGE_REQUIRED")
        if registry.configs["proxy"].provider != "brightdata":
            raise CrawlSourceError("OPTIONAL_PROVIDER_ADAPTER_NOT_CONFIGURED")
        target = validate_url(url)
        try:
            response = await registry.execute("proxy", target.host, url=url)
        except OptionalProviderError as exc:
            raise CrawlSourceError(str(exc)) from None
        except TimeoutError:
            raise
        except Exception:
            raise CrawlSourceError("PROXY_RETRIEVAL_FAILED") from None
        result = response["result"]
        if not isinstance(result, dict):
            raise CrawlSourceError("PROXY_RESPONSE_INVALID")
        if type(result.get("status_code")) is not int or not 200 <= result["status_code"] < 300:
            raise CrawlSourceError("PROXY_SOURCE_HTTP_ERROR")
        html = result.get("body")
        if not isinstance(html, str) or not html.strip():
            raise CrawlSourceError("PROXY_EMPTY_EVIDENCE")
        if len(html.encode("utf-8")) > 20_971_520:
            raise CrawlSourceError("PROXY_CONTENT_TOO_LARGE")
        if is_challenge_page(html, result.get("headers")):
            raise CrawlSourceError("CRAWL_CHALLENGE_REQUIRED")
        if wait_for:
            from selectolax.parser import HTMLParser

            if HTMLParser(html).css_first(wait_for) is None:
                raise CrawlSourceError("PROXY_SELECTOR_NOT_FOUND")
        title, text, links = extract_html(html)
        if not text.strip():
            raise CrawlSourceError("PROXY_EMPTY_EVIDENCE")
        # The documented Unlocker response does not attest a final URL. Keep the
        # requested citation explicit; never guess a redirect base for relative links.
        absolute = [{"href": href} for _, href in links[:250] if urlsplit(href).scheme in {"http", "https"}]
        warnings = ["PROXY_RETRIEVAL_USED", "PROXY_FINAL_URL_UNVERIFIED"]
        if len(absolute) < len(links):
            warnings.append("PROXY_RELATIVE_LINKS_SKIPPED")
        return SimpleNamespace(
            success=True,
            url=url,
            html=html,
            markdown=text,
            status_code=result["status_code"],
            metadata={"title": title},
            links={"internal": absolute, "external": []},
            retrieval_warnings=warnings,
            retrieval_metadata={
                "mode": "proxy",
                "retrieval_provider": "brightdata",
                "final_url_verified": False,
                "citation_url_kind": "requested",
            },
        )

    def _profile_directory(self, profile: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", profile) or profile in {".", ".."}:
            raise ValueError("BROWSER_PROFILE_INVALID")
        profile_root = (Path(self.base_directory) / "profiles").resolve()
        candidate = (profile_root / profile).resolve()
        if candidate.parent != profile_root or not candidate.is_dir():
            raise ValueError("BROWSER_PROFILE_NOT_FOUND")
        return candidate

    async def _profile_cookies(self, profile: str) -> list[dict]:
        directory = self._profile_directory(profile)
        if self._human_cookies is not None and self._human_cookies[0] == profile:
            return copy.deepcopy(self._human_cookies[1])
        args = ["--disable-background-networking", "--disable-sync", "--no-first-run"]
        if (directory / "Profile").is_dir():
            args.append("--profile-directory=Profile")
        async with _playwright_session() as playwright:
            context = await playwright.chromium.launch_persistent_context(
                str(directory),
                channel="chrome",
                headless=True,
                args=args,
                accept_downloads=False,
                service_workers="block",
            )
            try:
                await context.route("**/*", lambda route: route.abort())
                return await context.cookies()
            finally:
                await context.close()

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
