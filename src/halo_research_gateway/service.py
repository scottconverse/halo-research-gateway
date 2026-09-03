"""Application service implementing the semantic Halo research contracts."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import uuid
from collections import OrderedDict
from pathlib import Path

import httpx

from . import __version__
from .cache import Cache
from .cache_errors import EntryTooLargeError
from .clock import SystemClock, rfc3339
from .config import GatewayConfig
from .connections.chrome_import import ChromeImporter
from .connections.import_reviews import ImportReviewStore
from .connections.oauth import OAuthManager
from .connections.store import ConnectionStore
from .coordinator import Coordinator, QueuePolicy
from .cursor import CursorCodec, CursorError
from .envelope import build_envelope, error_envelope
from .jobs.manager import JobManager
from .migrations import SCHEMA_VERSION as DATABASE_SCHEMA_VERSION
from .migrations import migrate
from .models import EvidenceItem, LocalTarget, ProviderResult
from .providers.community import CommunityProvider, community_source_for_url
from .providers.crawl4ai_provider import Crawl4AIProvider
from .providers.deep import BodyDeduplicator, canonical_url, domain_allowed, url_host
from .providers.document_extract import DocumentProvider
from .providers.exa import ExaProvider, ExaRateLimited
from .providers.github import GitHubProvider
from .providers.http_fetch import HttpFetchProvider
from .providers.optional import OptionalProviderRegistry
from .providers.paid import BrightDataUnlockerAdapter, CapSolverAdapter
from .providers.reddit_rss import parse_atom, search_url, thread_rss_url
from .providers.search import DdgsSearchProvider
from .providers.transcripts import TranscriptProvider
from .rate_limit import ProviderRateLimited, RateLedger
from .security import ParsedTarget, UrlPolicyError, is_sensitive_url, redact_url


class HaloService:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self.clock = SystemClock()
        config.ensure_directories()
        migrate(config.storage.database, config.storage.backup_directory)
        self.cache = Cache(
            config.storage.database, config.storage.cache_max_bytes, config.storage.entry_max_bytes, enforce_limits=True
        )
        self.coordinator = Coordinator(
            {
                "exa": QueuePolicy(
                    config.queues.exa_max_pending,
                    config.queues.default_per_client_pending,
                    1,
                    config.exa.min_interval_seconds,
                ),
                "http": QueuePolicy(config.queues.http_max_pending, 8, config.http.global_concurrency, 0),
                "reddit": QueuePolicy(config.queues.reddit_max_pending, 2, 1, config.reddit.min_interval_seconds),
                "crawl": QueuePolicy(config.queues.crawl_max_pending, 1, config.crawl.concurrency, 2),
                "deep": QueuePolicy(4, 1, 1, 0),
            },
            self.clock,
        )
        self.http = HttpFetchProvider(
            timeout=config.http.total_timeout_seconds,
            max_redirects=config.http.max_redirects,
            max_bytes=config.http.max_decompressed_bytes,
            per_origin_concurrency=config.http.per_origin_concurrency,
            per_origin_interval_seconds=config.http.per_origin_interval_seconds,
            clock=self.clock,
        )
        self.exa = ExaProvider(config.exa.url, self.clock)
        self.ddgs = DdgsSearchProvider(self.clock)
        self.crawler = Crawl4AIProvider(
            config.crawl.base_directory, self.clock, limits=config.crawl, origin_gate=self.http._origin_gate
        )
        self.documents = DocumentProvider(self.http, self.clock)
        self.jobs = JobManager(config.storage.database, self.clock)
        self.import_reviews = ImportReviewStore(
            config.storage.database, config.imports.approval_ttl_seconds, self.clock
        )
        self.rate = RateLedger(config.storage.database, self.clock)
        runtime_root = Path(config.storage.database).parent.parent
        self.connections = ConnectionStore(config.storage.database, runtime_root / "vault", self.clock)
        self.github = GitHubProvider(
            self.connections,
            self.clock,
            max_response_bytes=config.http.max_decompressed_bytes,
            timeout_seconds=config.http.total_timeout_seconds,
        )
        self.transcripts = TranscriptProvider(self.http, self.clock)
        self.community = CommunityProvider(self.http, self.github, self.ddgs, self.clock)
        self.optional_providers = OptionalProviderRegistry(
            config.storage.database, self.connections, config.captcha, config.proxy
        )
        self.optional_providers.register("captcha", "capsolver", CapSolverAdapter(self.clock))
        self.optional_providers.register("proxy", "brightdata", BrightDataUnlockerAdapter())
        self.crawler.optional_providers = self.optional_providers
        self.oauth = OAuthManager(self.connections)
        self.chrome_importer = ChromeImporter(runtime_root / "browser" / "profiles")
        self.cursors = CursorCodec(
            Path(config.storage.database).parent / "cursor-hmac.key", config.output.cursor_ttl_seconds
        )
        self._snapshots: OrderedDict[str, tuple[bytes, float]] = OrderedDict()
        self._snapshot_bytes = 0
        self.started_at = rfc3339(self.clock.utcnow())
        self._job_tasks: dict[str, asyncio.Task] = {}
        self._job_lock = asyncio.Lock()
        self._oauth_tasks: dict[str, asyncio.Task] = {}
        self.jobs.recover_expired(recover_queued=True)

    async def close(self) -> None:
        for task in self._job_tasks.values():
            task.cancel()
        for task in self._oauth_tasks.values():
            task.cancel()
        if self._job_tasks:
            await asyncio.gather(*self._job_tasks.values(), return_exceptions=True)
        if self._oauth_tasks:
            await asyncio.gather(*self._oauth_tasks.values(), return_exceptions=True)
        await self.crawler.close()
        self._snapshots.clear()
        self._snapshot_bytes = 0

    async def oauth_begin(self, **values) -> dict:
        begun = await self.oauth.begin(**values)
        self._oauth_tasks[begun["flow_id"]] = asyncio.create_task(self.oauth.complete(begun["flow_id"]))
        return begun

    def oauth_status(self, flow_id: str) -> dict:
        task = self._oauth_tasks.get(flow_id)
        if task is None:
            return {"flow_id": flow_id, "state": "unavailable"}
        if not task.done():
            return {"flow_id": flow_id, "state": "waiting_for_operator"}
        self._oauth_tasks.pop(flow_id, None)
        try:
            return {"flow_id": flow_id, "state": "complete", "connection": task.result()}
        except Exception as exc:
            return {"flow_id": flow_id, "state": "failed", "error": str(exc).split("/", 1)[0]}

    def chrome_import_preview(self, **values) -> dict:
        preview = self.chrome_importer.preview(**values)
        return self.import_reviews.prepare({"action": "chrome_import", "import": preview})

    async def chrome_import_execute(self, plan_id: str, approval_token: str, idempotency_key: str) -> dict:
        async def executor(plan):
            if plan.get("action") != "chrome_import":
                raise ValueError("CHROME_IMPORT_PLAN_REQUIRED")
            return await asyncio.to_thread(self.chrome_importer.execute, plan["import"])

        return await self.import_reviews.execute(plan_id, approval_token, idempotency_key, executor)

    def _budget(self, max_chars: int | None) -> int:
        return min(
            max_chars or self.config.output.unidentified_default_chars,
            self.config.output.unidentified_ceiling_chars,
            30000,
        )

    def _envelope(
        self,
        tool: str,
        result: ProviderResult,
        max_chars: int | None,
        cursor_state: dict | None = None,
        requested: int | None = None,
    ) -> dict:
        now = rfc3339(self.clock.utcnow())
        budget = self._budget(max_chars)
        payload = self._encode_result(result)
        digest = hashlib.sha256(payload).hexdigest()
        snapshot_key = digest
        self._snapshot_put(snapshot_key, payload)
        items = self._chunk_items([x.as_dict() for x in result.items], budget)

        def encode_cursor(page: dict) -> str:
            return self.cursors.encode(
                page
                | {
                    "t": tool,
                    "s": snapshot_key,
                    "k": result.cache_key,
                    "b": budget,
                    "v": 3,
                }
            )

        return build_envelope(
            tool,
            result.provider,
            str(uuid.uuid4()),
            now,
            now,
            items,
            requested or len(result.items),
            result.available if result.available is not None else len(result.items),
            budget,
            cache_hit=result.cache_hit,
            cache_age_seconds=result.cache_age_seconds,
            cache_key=result.cache_key,
            cursor_state=cursor_state,
            encode_cursor=encode_cursor,
            warnings=result.warnings,
        )

    def _resume(self, tool: str, cursor: str, max_chars: int | None) -> dict:
        try:
            state = self.cursors.decode(cursor)
            if state.get("v") != 3:
                return self._error(tool, "pagination", ValueError("CURSOR_EVICTED"))
            if state.get("t") != tool:
                raise CursorError("cursor does not match tool or schema")
            cursor_budget = int(state["b"])
            if max_chars is not None and self._budget(max_chars) != cursor_budget:
                raise CursorError("cursor does not match output profile")
            snapshot_key = state["s"]
            cache_key = state.get("k", "")
            payload = self._snapshot_get(snapshot_key)
            age = 0
            if payload is None:
                cached = self.cache.get_with_age(cache_key) if cache_key else None
                if cached is None or hashlib.sha256(cached[0]).hexdigest() != snapshot_key:
                    return self._error(tool, "pagination", ValueError("CURSOR_EVICTED"))
                payload, age = cached
            result = self._decode_result(payload, cache_key, age)
            return self._envelope(tool, result, cursor_budget, state)
        except Exception as exc:
            return self._error(tool, "pagination", exc)

    def _prune_snapshots(self) -> None:
        now = self.clock.monotonic()
        for key, (payload, expires) in list(self._snapshots.items()):
            if expires <= now:
                del self._snapshots[key]
                self._snapshot_bytes -= len(payload)

    def _snapshot_put(self, key: str, payload: bytes) -> None:
        self._prune_snapshots()
        limits = self.config.output
        if len(payload) > limits.snapshot_max_bytes:
            raise ValueError("SNAPSHOT_TOO_LARGE")
        prior = self._snapshots.pop(key, None)
        if prior is not None:
            self._snapshot_bytes -= len(prior[0])
        while self._snapshots and (
            len(self._snapshots) >= limits.snapshot_max_entries
            or self._snapshot_bytes + len(payload) > limits.snapshot_max_bytes
        ):
            _, (removed, _) = self._snapshots.popitem(last=False)
            self._snapshot_bytes -= len(removed)
        self._snapshots[key] = (payload, self.clock.monotonic() + limits.cursor_ttl_seconds)
        self._snapshot_bytes += len(payload)

    def _snapshot_get(self, key: str) -> bytes | None:
        self._prune_snapshots()
        entry = self._snapshots.get(key)
        if entry is None:
            return None
        self._snapshots.move_to_end(key)
        return entry[0]

    def _snapshot_stats(self) -> dict:
        self._prune_snapshots()
        return {
            "entries": len(self._snapshots),
            "payload_bytes": self._snapshot_bytes,
            "max_entries": self.config.output.snapshot_max_entries,
            "max_payload_bytes": self.config.output.snapshot_max_bytes,
        }

    @staticmethod
    def _encode_result(result: ProviderResult) -> bytes:
        return json.dumps(
            {
                "provider": result.provider,
                "items": [item.as_dict() for item in result.items],
                "warnings": result.warnings,
                "available": result.available,
            },
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode()

    @staticmethod
    def _decode_result(payload: bytes, cache_key: str, age_seconds: int) -> ProviderResult:
        from .models import EvidenceItem

        value = json.loads(payload)
        return ProviderResult(
            value["provider"],
            [EvidenceItem(**raw) for raw in value["items"]],
            value.get("warnings", []),
            value.get("available"),
            cache_hit=True,
            cache_age_seconds=age_seconds,
            cache_key=cache_key,
        )

    async def _cached_run(
        self,
        queue: str,
        client: str,
        cache_key: str,
        ttl_seconds: int,
        operation,
        *,
        max_age_seconds: int | None = None,
        cacheable: bool = True,
    ) -> ProviderResult:
        if cacheable:
            cached = self.cache.get_with_age(cache_key, max_age_seconds)
            if cached is not None:
                return self._decode_result(cached[0], cache_key, cached[1])
        result = await self.coordinator.run(queue, client, cache_key, operation)
        persist = cacheable and "SENSITIVE_URL_NOT_CACHED" not in result.warnings
        result.cache_key = cache_key if persist else ""
        if persist:
            self._cache_result(result, cache_key, ttl_seconds)
        return result

    def _cache_result(self, result: ProviderResult, key: str, ttl: int, encoded: bytes | None = None) -> None:
        """Cache capacity must not turn already-collected evidence into a failure."""
        result.cache_key = ""
        try:
            self.cache.put(key, encoded if encoded is not None else self._encode_result(result), ttl)
        except EntryTooLargeError:
            if "RESULT_NOT_CACHED_TOO_LARGE" not in result.warnings:
                result.warnings.append("RESULT_NOT_CACHED_TOO_LARGE")
        else:
            result.cache_key = key

    @staticmethod
    def _chunk_items(items: list[dict], budget: int) -> list[dict]:
        """Split long evidence bodies before envelope pagination.

        This preserves the citation on every chunk and prevents the formatter's
        forward-progress rule from emitting a single page above the host limit.
        """
        chunk_size = max(64, budget - 1750)
        output: list[dict] = []
        for original in items:
            item = dict(original)
            metadata = dict(item.get("metadata") or {})
            if "links" in metadata:
                metadata["links"] = metadata["links"][:10]
            item["metadata"] = metadata
            if metadata.get("segments"):
                # The envelope pages caption text and timing metadata together.
                # Pre-chunking prose would repeat the entire segment array.
                output.append(item)
                continue
            content = item.get("content") or ""
            if len(content) <= chunk_size:
                output.append(item)
                continue
            parts = [content[index : index + chunk_size] for index in range(0, len(content), chunk_size)]
            for number, part in enumerate(parts, 1):
                chunk = dict(item)
                chunk["content"] = part
                if number > 1:
                    chunk["snippet"] = None
                chunk["metadata"] = {key: value for key, value in metadata.items() if key != "links"} | {
                    "content_part": number,
                    "content_parts": len(parts),
                }
                output.append(chunk)
        return output

    def _error(self, tool: str, provider: str, exc: Exception) -> dict:
        code = getattr(exc, "code", None) or (str(exc) if str(exc).isupper() else "UPSTREAM_UNAVAILABLE")
        if isinstance(exc, UrlPolicyError):
            code = "UNSAFE_URL"
        return error_envelope(
            tool,
            provider,
            str(uuid.uuid4()),
            code,
            f"{type(exc).__name__}: operation did not complete",
            retry_after_seconds=getattr(exc, "retry_after_seconds", None),
        )

    async def web_search(
        self,
        query: str | None = None,
        max_results: int = 6,
        content_type: str = "web",
        include_domains=None,
        exclude_domains=None,
        freshness_days=None,
        max_chars=None,
        cursor=None,
        client="unidentified",
        max_age_seconds=None,
    ) -> dict:
        if cursor:
            return self._resume("web_search", cursor, max_chars)
        if not query:
            return self._error("web_search", "policy", ValueError("QUERY_REQUIRED"))
        if "reddit.com" in (include_domains or []):
            return self._error("web_search", "policy", ValueError("REDDIT_USE_REDDIT_SEARCH"))
        try:
            result = await self._search_result(
                query,
                max_results,
                content_type,
                include_domains,
                exclude_domains,
                freshness_days,
                client,
                max_age_seconds,
            )
            return self._envelope("web_search", result, max_chars, requested=max_results)
        except Exception as exc:
            return self._error("web_search", "search", exc)

    async def _search_result(
        self,
        query,
        max_results,
        content_type,
        include_domains,
        exclude_domains,
        freshness_days,
        client,
        max_age_seconds,
    ) -> ProviderResult:
        key = (
            "search:"
            + hashlib.sha256(
                json.dumps(
                    [query, max_results, content_type, include_domains, exclude_domains, freshness_days], sort_keys=True
                ).encode()
            ).hexdigest()
        )

        async def run():
            # This anonymous Exa tool accepts only query/result count here.
            # Route controls it cannot express to the accountless provider.
            if content_type == "web" and freshness_days is None:
                try:
                    self.rate.admit("exa-anonymous", self.config.exa.daily_soft_limit)
                    count = min(30, max_results * 2) if include_domains or exclude_domains else max_results
                    result = await self.exa.search(query, count)
                    self.rate.success("exa-anonymous")
                    result.items = [
                        item for item in result.items if domain_allowed(item.url, include_domains, exclude_domains)
                    ][:max_results]
                    result.available = len(result.items)
                    if result.items:
                        return result
                except ExaRateLimited:
                    self.rate.rate_limited("exa-anonymous", threshold=1, cooldown_seconds=3600)
                except Exception:
                    pass
            return await self.ddgs.search(
                query,
                max_results=max_results,
                content_type=content_type,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                freshness_days=freshness_days,
            )

        return await self._cached_run("exa", client, key, 21600, run, max_age_seconds=max_age_seconds)

    async def web_fetch(
        self, url: str | None = None, max_chars=None, cursor=None, client="unidentified", max_age_seconds=None
    ) -> dict:
        if cursor:
            return self._resume("web_fetch", cursor, max_chars)
        if not url:
            return self._error("web_fetch", "policy", ValueError("URL_REQUIRED"))
        key = "fetch:v2:" + hashlib.sha256(url.encode()).hexdigest()
        try:
            from .security import is_sensitive_url

            result = await self._cached_run(
                "http",
                client,
                key,
                3600,
                lambda: self.http.fetch(url),
                cacheable=not is_sensitive_url(url),
                max_age_seconds=max_age_seconds,
            )
            return self._envelope("web_fetch", result, max_chars, requested=1)
        except Exception as exc:
            return self._error("web_fetch", "direct-http", exc)

    async def web_crawl(
        self,
        url: str | None = None,
        max_pages=1,
        max_depth=0,
        same_site_only=True,
        mode="auto",
        profile=None,
        interaction="none",
        capture="none",
        wait_for=None,
        max_chars=None,
        cursor=None,
        client="unidentified",
        max_age_seconds=None,
    ) -> dict:
        if cursor:
            return self._resume("web_crawl", cursor, max_chars)
        if not url:
            return self._error("web_crawl", "policy", ValueError("URL_REQUIRED"))
        key = (
            "crawl:v3:"
            + hashlib.sha256(
                json.dumps(
                    [url, max_pages, max_depth, same_site_only, mode, profile, interaction, capture, wait_for]
                ).encode()
            ).hexdigest()
        )
        try:
            result = await self._cached_run(
                "crawl",
                client,
                key,
                3600,
                lambda: self.crawler.crawl(
                    url,
                    max_pages=max_pages,
                    max_depth=max_depth,
                    same_site_only=same_site_only,
                    mode=mode,
                    wait_for=wait_for,
                    profile=profile,
                    interaction=interaction,
                    capture=capture,
                ),
                max_age_seconds=max_age_seconds,
                cacheable=mode != "managed_profile" and not is_sensitive_url(url),
            )
            return self._envelope("web_crawl", result, max_chars, requested=max_pages)
        except Exception as exc:
            return self._error("web_crawl", "crawl4ai", exc)

    async def _rss(self, url: str, limit: int) -> ProviderResult:
        self.rate.admit("reddit-anonymous")
        try:
            _, _, _, body = await self.http.download(url, accept="application/atom+xml,application/rss+xml")
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                requested_delay = exc.response.headers.get("Retry-After", "")
                delay = max(
                    self.config.reddit.rate_limit_backoff_seconds,
                    int(requested_delay) if requested_delay.isdecimal() else 0,
                )
                delay = min(delay, 86400)
                self.rate.rate_limited(
                    "reddit-anonymous",
                    self.config.reddit.max_consecutive_429,
                    self.config.reddit.circuit_cooldown_seconds,
                    backoff_seconds=delay,
                )
                raise ProviderRateLimited(delay) from exc
            raise
        self.rate.success("reddit-anonymous")
        return parse_atom(body, limit=limit, clock=self.clock)

    async def reddit_search(
        self,
        query: str | None = None,
        subreddit=None,
        sort="relevance",
        time="all",
        max_results=10,
        max_chars=None,
        cursor=None,
        client="unidentified",
        max_age_seconds=None,
    ) -> dict:
        if cursor:
            return self._resume("reddit_search", cursor, max_chars)
        if not query:
            return self._error("reddit_search", "policy", ValueError("QUERY_REQUIRED"))
        url = search_url(query, subreddit, sort, time)
        try:
            key = "reddit:" + hashlib.sha256(url.encode()).hexdigest()
            result = await self._cached_run(
                "reddit",
                client,
                key,
                900,
                lambda: self._rss(url, max_results),
                max_age_seconds=max_age_seconds,
            )
            return self._envelope("reddit_search", result, max_chars, requested=max_results)
        except Exception as exc:
            return self._error("reddit_search", "reddit-rss", exc)

    async def reddit_thread(
        self,
        url: str | None = None,
        max_comments=30,
        max_chars=None,
        cursor=None,
        client="unidentified",
        max_age_seconds=None,
    ) -> dict:
        if cursor:
            return self._resume("reddit_thread", cursor, max_chars)
        if not url:
            return self._error("reddit_thread", "policy", ValueError("URL_REQUIRED"))
        try:
            rss_url = thread_rss_url(url)
            key = "reddit:" + hashlib.sha256(rss_url.encode()).hexdigest()
            result = await self._cached_run(
                "reddit",
                client,
                key,
                1800,
                lambda: self._rss(rss_url, max_comments + 1),
                max_age_seconds=max_age_seconds,
            )
            return self._envelope("reddit_thread", result, max_chars, requested=max_comments + 1)
        except Exception as exc:
            return self._error("reddit_thread", "reddit-rss", exc)

    async def document_extract(
        self,
        url: str | None = None,
        pages=None,
        max_chars=None,
        cursor=None,
        client="unidentified",
        max_age_seconds=None,
        *,
        include_tables=True,
        ocr="auto",
    ) -> dict:
        if cursor:
            return self._resume("document_extract", cursor, max_chars)
        if not url:
            return self._error("document_extract", "policy", ValueError("URL_REQUIRED"))
        key = "document:v3:" + hashlib.sha256(json.dumps([url, pages, include_tables, ocr]).encode()).hexdigest()
        try:
            from .security import is_sensitive_url

            result = await self._cached_run(
                "http",
                client,
                key,
                86400,
                lambda: self.documents.extract(url, pages, include_tables=include_tables, ocr=ocr),
                cacheable=not is_sensitive_url(url),
                max_age_seconds=max_age_seconds,
            )
            return self._envelope("document_extract", result, max_chars, requested=len(result.items))
        except Exception as exc:
            return self._error("document_extract", "document", exc)

    async def deep_research(
        self,
        question: str | None = None,
        seed_urls=None,
        include_domains=None,
        exclude_domains=None,
        max_sources=12,
        max_pages=20,
        max_depth=2,
        freshness_days=None,
        max_chars=None,
        cursor=None,
        client="unidentified",
        _checkpoint=None,
        _checkpoint_save=None,
    ) -> dict:
        if cursor:
            return self._resume("deep_research", cursor, max_chars)
        if (
            not question
            or not question.strip()
            or not 1 <= max_sources <= 50
            or not 1 <= max_pages <= 250
            or not 0 <= max_depth <= 3
        ):
            return self._error("deep_research", "policy", ValueError("INVALID_DEEP_RESEARCH_LIMITS"))
        seed_urls = list(seed_urls or [])
        key = (
            "deep:"
            + hashlib.sha256(
                json.dumps(
                    [
                        question,
                        seed_urls,
                        include_domains,
                        exclude_domains,
                        max_sources,
                        max_pages,
                        max_depth,
                        freshness_days,
                    ],
                    sort_keys=True,
                ).encode()
            ).hexdigest()
        )
        try:

            async def collect() -> ProviderResult:
                state = _checkpoint if _checkpoint is not None else {}
                warnings: list[str] = list(state.get("warnings", []))
                frontier: list[tuple[str, int, str]] = [tuple(entry) for entry in state.get("frontier", [])]
                enqueued: set[str] = {entry[0] for entry in frontier}
                items = [EvidenceItem(**item) for item in state.get("items", [])]
                position = state.get("position", 0)
                attempted = state.get("attempted", 0)

                def checkpoint():
                    if _checkpoint_save is not None:
                        state.update(
                            version=1,
                            search_complete=True,
                            frontier=frontier,
                            position=position,
                            attempted=attempted,
                            items=[item.as_dict() for item in items],
                            warnings=sorted(set(warnings)),
                        )
                        _checkpoint_save(state)

                def enqueue(
                    raw_url: str, depth: int, root_host: str | None = None, base_url: str | None = None
                ) -> None:
                    normalized = canonical_url(raw_url, base_url)
                    if normalized is None:
                        warnings.append("SOURCE_URL_SKIPPED")
                        return
                    if _checkpoint_save is not None and is_sensitive_url(normalized):
                        warnings.append("SENSITIVE_SOURCE_NOT_PERSISTED")
                        return
                    host = url_host(normalized)
                    root = root_host or host
                    if root_host is not None and host != root:
                        warnings.append("CROSS_SITE_LINK_SKIPPED")
                        return
                    if not domain_allowed(normalized, include_domains, exclude_domains):
                        warnings.append("SOURCE_FILTERED")
                        return
                    if normalized in enqueued:
                        warnings.append("DUPLICATE_URL_SKIPPED")
                        return
                    if len(enqueued) >= max_pages:
                        warnings.append("PAGE_LIMIT_REACHED")
                        return
                    enqueued.add(normalized)
                    frontier.append((normalized, depth, root))

                if not state.get("search_complete"):
                    try:
                        search = await self.ddgs.search(
                            question,
                            max_results=max_sources,
                            include_domains=include_domains,
                            exclude_domains=exclude_domains,
                            freshness_days=freshness_days,
                        )
                        warnings.extend(search.warnings)
                    except Exception:
                        search = ProviderResult("search-unavailable", [], ["SEARCH_UNAVAILABLE"], 0)
                        warnings.extend(search.warnings)
                    for url in seed_urls:
                        enqueue(url, 0)
                        if len(enqueued) >= max_pages:
                            break
                    for item in search.items:
                        enqueue(item.url, 0)
                        if len(enqueued) >= max_pages:
                            break
                    checkpoint()

                deduplicator = BodyDeduplicator()
                for item in items:
                    deduplicator.duplicate(item.content or item.snippet or "")
                while position < len(frontier) and attempted < max_pages and len(items) < max_sources:
                    url, depth, root_host = frontier[position]
                    attempted += 1
                    checkpoint()  # Charge before dispatch; interrupted reads consume their attempt.
                    fetch_key = "fetch:" + hashlib.sha256(url.encode()).hexdigest()
                    try:
                        fetched = await self._cached_run(
                            "http", client, fetch_key, 3600, lambda current=url: self.http.fetch(current)
                        )
                    except Exception:
                        warnings.append("UPSTREAM_UNAVAILABLE")
                        position += 1
                        checkpoint()
                        continue
                    warnings.extend(fetched.warnings)
                    for item in fetched.items:
                        result_url = canonical_url(item.url)
                        if result_url is None or not domain_allowed(result_url, include_domains, exclude_domains):
                            warnings.append("SOURCE_FILTERED")
                            continue
                        if _checkpoint_save is not None and is_sensitive_url(result_url):
                            warnings.append("SENSITIVE_SOURCE_NOT_PERSISTED")
                            continue
                        if url_host(result_url) != root_host:
                            warnings.append("CROSS_SITE_LINK_SKIPPED")
                            continue
                        item.url = result_url
                        if _checkpoint_save is not None:
                            metadata = dict(item.metadata or {})
                            safe_links = []
                            for link in metadata.get("links") or []:
                                href = link.get("url") if isinstance(link, dict) else link[1] if len(link) > 1 else None
                                normalized_link = canonical_url(str(href), result_url) if href else None
                                if normalized_link and is_sensitive_url(normalized_link):
                                    warnings.append("SENSITIVE_SOURCE_NOT_PERSISTED")
                                else:
                                    safe_links.append(link)
                            metadata["links"] = safe_links
                            item = EvidenceItem(**{**item.as_dict(), "metadata": metadata})
                        body = item.content or item.snippet or ""
                        if deduplicator.duplicate(body):
                            warnings.append("DUPLICATE_CONTENT_SKIPPED")
                        elif len(items) < max_sources:
                            items.append(item)

                        links = (item.metadata or {}).get("links") or []
                        if depth >= max_depth:
                            if links:
                                warnings.append("DEPTH_LIMIT_REACHED")
                            continue
                        for link in links:
                            href = link.get("url") if isinstance(link, dict) else link[1] if len(link) > 1 else None
                            if href:
                                enqueue(str(href), depth + 1, root_host, item.url)
                    position += 1
                    checkpoint()

                if position < len(frontier) and attempted >= max_pages:
                    warnings.append("PAGE_LIMIT_REACHED")
                if len(items) >= max_sources and position < len(frontier):
                    warnings.append("SOURCE_LIMIT_REACHED")
                checkpoint()
                return ProviderResult("halo-deep", items, sorted(set(warnings)), len(items))

            if _checkpoint is None:
                result = await self._cached_run("deep", client, key, 1800, collect)
            else:
                # Job-local checkpoints cannot be shared with a different job's frontier.
                result = await self.coordinator.run("deep", client, "job:" + _checkpoint["job_id"], collect)
            return self._envelope(
                "deep_research",
                result,
                max_chars,
                requested=max_sources,
            )
        except Exception as exc:
            return self._error("deep_research", "halo-deep", exc)

    async def github_research(
        self,
        query: str | None = None,
        repository: str | None = None,
        kinds: list[str] | None = None,
        ref: str | None = None,
        max_results: int = 10,
        max_chars=None,
        cursor=None,
        client="unidentified",
    ) -> dict:
        if cursor:
            return self._resume("github_research", cursor, max_chars)
        if not query or not query.strip() or not 1 <= max_results <= 30:
            return self._error("github_research", "github-api", ValueError("INVALID_GITHUB_QUERY"))
        key = (
            "github:"
            + hashlib.sha256(
                json.dumps([query, repository, kinds, ref, max_results], sort_keys=True).encode()
            ).hexdigest()
        )
        try:
            result = await self.coordinator.run(
                "http",
                client,
                key,
                lambda: self.github.research(query, repository, kinds, ref, max_results),
            )
            if result.items or "GITHUB_AUTH_NOT_CONFIGURED" not in result.warnings:
                return self._envelope("github_research", result, max_chars, requested=max_results)

            # Anonymous public discovery remains useful, but is explicitly not
            # represented as structured/authenticated GitHub API coverage.
            public_query = f"site:github.com/{repository} {query}" if repository else f"site:github.com {query}"
            search_result = await self._search_result(
                public_query, max_results, "web", ["github.com"], None, None, client, None
            )
            # Repage complete normalized evidence, never an already rendered page
            # or a mutable/evictable side effect of another tool's envelope.
            fallback = ProviderResult(
                "github-public-discovery",
                search_result.items,
                sorted(set(search_result.warnings + result.warnings)),
                search_result.available,
                cache_hit=search_result.cache_hit,
                cache_age_seconds=search_result.cache_age_seconds,
            )
            return self._envelope("github_research", fallback, max_chars, requested=max_results)
        except Exception as exc:
            return self._error("github_research", "github-api", exc)

    async def transcript_fetch(
        self,
        url: str | None = None,
        language: str | None = None,
        prefer_human: bool = True,
        max_chars=None,
        cursor=None,
        client="unidentified",
    ) -> dict:
        if cursor:
            return self._resume("transcript_fetch", cursor, max_chars)
        if not url:
            return self._error("transcript_fetch", "policy", ValueError("URL_REQUIRED"))
        if language is not None and (not language.strip() or len(language) > 64):
            return self._error("transcript_fetch", "policy", ValueError("INVALID_TRANSCRIPT_LANGUAGE"))
        from .security import is_sensitive_url

        if is_sensitive_url(url):
            return self._error("transcript_fetch", "policy", ValueError("SENSITIVE_URL_NOT_ALLOWED"))
        key = (
            "transcript:"
            + hashlib.sha256(json.dumps([url, language, prefer_human], sort_keys=True).encode()).hexdigest()
        )
        try:
            result = await self._cached_run(
                "http",
                client,
                key,
                3600,
                lambda: self.transcripts.fetch(url, language, prefer_human),
                cacheable=not is_sensitive_url(url),
            )
            return self._envelope("transcript_fetch", result, max_chars, requested=1)
        except Exception as exc:
            return self._error("transcript_fetch", "public-transcript", exc)

    async def community_search(
        self,
        query: str | None = None,
        sources: list[str] | None = None,
        max_results: int = 10,
        freshness_days: int | None = None,
        max_chars=None,
        cursor=None,
        client="unidentified",
    ) -> dict:
        if cursor:
            return self._resume("community_search", cursor, max_chars)
        if not query or not query.strip() or len(query) > 500 or not 1 <= max_results <= 25:
            return self._error("community_search", "policy", ValueError("INVALID_COMMUNITY_QUERY"))
        if freshness_days is not None and freshness_days < 0:
            return self._error("community_search", "policy", ValueError("INVALID_FRESHNESS"))
        key = (
            "community-search:"
            + hashlib.sha256(
                json.dumps([query, sources, max_results, freshness_days], sort_keys=True).encode()
            ).hexdigest()
        )
        selected = {str(source).casefold() for source in (sources or ["all"])}
        cacheable = not ({"all", "github_discussions"} & selected)
        try:
            result = await self._cached_run(
                "http",
                client,
                key,
                900,
                lambda: self.community.search(query, sources, max_results, freshness_days),
                cacheable=cacheable,
            )
            return self._envelope("community_search", result, max_chars, requested=max_results)
        except Exception as exc:
            return self._error("community_search", "community-public", exc)

    async def community_thread(
        self,
        url: str | None = None,
        max_replies: int = 40,
        sort: str = "source_default",
        max_chars=None,
        cursor=None,
        client="unidentified",
    ) -> dict:
        if cursor:
            return self._resume("community_thread", cursor, max_chars)
        if not url:
            return self._error("community_thread", "policy", ValueError("URL_REQUIRED"))
        if not 1 <= max_replies <= 150 or sort not in {"source_default", "top", "oldest", "newest"}:
            return self._error("community_thread", "policy", ValueError("INVALID_COMMUNITY_THREAD_LIMITS"))
        try:
            source = community_source_for_url(url)
            key = (
                "community-thread:"
                + hashlib.sha256(json.dumps([url, max_replies, sort], sort_keys=True).encode()).hexdigest()
            )
            if source == "reddit":
                rss_url = thread_rss_url(url)
                result = await self._cached_run(
                    "reddit", client, key, 1800, lambda: self._rss(rss_url, max_replies + 1)
                )
            elif source == "forums":
                result = await self._cached_run(
                    "crawl",
                    client,
                    "forum-challenge:v1:" + key,
                    1800,
                    lambda: self.crawler.crawl(url, max_pages=1, mode="standard"),
                )
                result.provider = "community-forum-crawl"
                result.warnings = sorted(set([*result.warnings, "FORUM_THREAD_UNSTRUCTURED"]))
                for item in result.items:
                    item.metadata = dict(item.metadata or {}) | {"community_source": "forums"}
            else:
                result = await self._cached_run(
                    "http",
                    client,
                    key,
                    1800,
                    lambda: self.community.thread(url, max_replies, sort),
                    cacheable=source != "github_discussions",
                )
            return self._envelope("community_thread", result, max_chars, requested=max_replies + 1)
        except Exception as exc:
            return self._error("community_thread", "community-public", exc)

    async def local_fetch(
        self,
        target: str | None = None,
        path: str | None = None,
        max_chars=None,
        cursor=None,
        client="unidentified",
    ) -> dict:
        if cursor:
            return self._resume("local_fetch", cursor, max_chars)
        if not target or path is None:
            return self._error("local_fetch", "policy", ValueError("TARGET_AND_PATH_REQUIRED"))
        configured = self.config.local_targets.get(target)
        if configured is None:
            return self._error("local_fetch", "local", ValueError("LOCAL_TARGET_NOT_ALLOWED"))
        policy = LocalTarget(
            target,
            configured.scheme,
            configured.host,
            configured.port,
            tuple(configured.path_prefixes),
            tuple(configured.methods),
            configured.browser_allowed,
            configured.cache_authenticated,
        )
        try:
            if "GET" not in policy.methods:
                raise ValueError("LOCAL_METHOD_NOT_ALLOWED")
            url = policy.build_url(path)
            # Hash the exact named target and URL: queue diagnostics must not
            # expose private source paths, and different local policies cannot join.
            key = "local-http:" + hashlib.sha256(json.dumps([target, url]).encode()).hexdigest()
            result = await self.coordinator.run("http", client, key, lambda: self._local_fetch_result(url, policy))
            return self._envelope("local_fetch", result, max_chars, requested=1)
        except Exception as exc:
            return self._error("local_fetch", "local-http", exc)

    async def _local_fetch_result(self, url: str, policy: LocalTarget) -> ProviderResult:
        origin = ParsedTarget(policy.scheme, policy.host, policy.port, "")
        try:
            async with (
                asyncio.timeout(self.config.http.total_timeout_seconds),
                self.http._origin_gate(origin),
            ):
                async with httpx.AsyncClient(
                    trust_env=False, follow_redirects=False, timeout=self.config.http.total_timeout_seconds
                ) as client:
                    async with client.stream("GET", url) as response:
                        if response.is_redirect:
                            raise ValueError("LOCAL_REDIRECT_DENIED")
                        response.raise_for_status()
                        payload = bytearray()
                        async for chunk in response.aiter_bytes():
                            if len(payload) + len(chunk) > self.config.http.max_decompressed_bytes:
                                raise ValueError("LOCAL_RESPONSE_TOO_LARGE")
                            payload.extend(chunk)
                        text = payload.decode(response.encoding or "utf-8", errors="replace")
        except (TimeoutError, httpx.TimeoutException):
            raise TimeoutError("LOCAL_REQUEST_TIMEOUT") from None
        sensitive = is_sensitive_url(url)
        return ProviderResult(
            "local-http",
            [
                EvidenceItem(
                    url=redact_url(url) if sensitive else url,
                    retrieved_at=rfc3339(self.clock.utcnow()),
                    source=policy.target_id,
                    content=text,
                )
            ],
            ["SENSITIVE_URL_NOT_CACHED"] if sensitive else [],
            1,
        )

    async def local_crawl(
        self,
        target: str | None = None,
        path: str | None = None,
        max_pages=1,
        profile=None,
        max_chars=None,
        cursor=None,
        client="unidentified",
        *,
        max_depth=0,
        interaction="none",
    ) -> dict:
        if cursor:
            return self._resume("local_crawl", cursor, max_chars)
        if not target or path is None:
            return self._error("local_crawl", "policy", ValueError("TARGET_AND_PATH_REQUIRED"))
        configured = self.config.local_targets.get(target)
        if configured is None or not configured.browser_allowed:
            return self._error("local_crawl", "local", ValueError("LOCAL_TARGET_NOT_ALLOWED"))
        policy = LocalTarget(
            target,
            configured.scheme,
            configured.host,
            configured.port,
            tuple(configured.path_prefixes),
            tuple(configured.methods),
            configured.browser_allowed,
            configured.cache_authenticated,
        )
        try:
            url = policy.build_url(path)
            cacheable = configured.cache_authenticated
            key = (
                "local-crawl:v3:"
                + hashlib.sha256(
                    json.dumps([target, path, max_pages, max_depth, profile, interaction]).encode()
                ).hexdigest()
            )
            result = await self._cached_run(
                "crawl",
                client,
                key,
                300,
                lambda: self.crawler.crawl(
                    url,
                    max_pages=max_pages,
                    max_depth=max_depth,
                    interaction=interaction,
                    mode="managed_profile" if profile else "standard",
                    profile=profile,
                    public=False,
                    local_target=policy,
                ),
                cacheable=cacheable,
            )
            result.provider = "local-crawl4ai"
            for item in result.items:
                item.source = target
            return self._envelope("local_crawl", result, max_chars, requested=max_pages)
        except Exception as exc:
            return self._error("local_crawl", "local-crawl4ai", exc)

    async def research_job(
        self, operation: str, owner: str, job_id=None, question=None, profile="standard", limits=None
    ) -> dict:
        async with self._job_lock:
            status = await self._control_job(operation, owner, job_id, question, profile, limits)
            return self._job_status_view(status)

    def _job_status_view(self, status: dict) -> dict:
        """Return counts and a citable page, not the entire durable evidence packet."""
        progress = dict(status["progress"])
        checkpoint = progress.get("checkpoint")
        if checkpoint is not None:
            items = [EvidenceItem(**item) for item in checkpoint.get("items", [])]
            progress["checkpoint"] = {
                "attempted": checkpoint.get("attempted", 0),
                "completed_sources": len(items),
                "remaining_sources": max(0, len(checkpoint.get("frontier", [])) - checkpoint.get("position", 0)),
                "elapsed_seconds": checkpoint.get("elapsed_seconds", 0),
                "search_complete": checkpoint.get("search_complete", False),
            }
            if items:
                warnings = list(checkpoint.get("warnings", []))
                if status.get("error_code"):
                    warnings.append(status["error_code"])
                result = ProviderResult("halo-deep", items, sorted(set(warnings)), len(items))
                encoded = self._encode_result(result)
                key = "job-evidence:" + hashlib.sha256(encoded).hexdigest()
                self._cache_result(result, key, self.config.output.cursor_ttl_seconds, encoded)
                progress["result"] = self._envelope("deep_research", result, 4000)
                progress["partial"] = bool(
                    warnings or progress["result"]["page"]["next_cursor"] or status["state"] != "complete"
                )
        return {**status, "progress": progress}

    async def _control_job(self, operation, owner, job_id, question, profile, limits) -> dict:
        self.jobs.recover_expired()
        if operation == "create":
            requested_limits = {"profile": profile, **(limits or {})}
            bounds = {
                "max_sources": (12, 50),
                "max_pages": (20, min(250, self.config.jobs.absolute_pages)),
                "timeout_seconds": (
                    self.config.jobs.default_timeout_seconds,
                    self.config.jobs.absolute_timeout_seconds,
                ),
            }
            for name, (default, maximum) in bounds.items():
                value = requested_limits.get(name, default)
                if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                    raise ValueError("INVALID_JOB_LIMITS")
                requested_limits[name] = min(value, maximum)
            self._check_job_capacity()
            created = self.jobs.create(owner, question or "", requested_limits)
            self._schedule_job(created["job_id"], owner)
            return created
        if operation == "status":
            return self.jobs.status(job_id, owner)
        if operation == "resume":
            current = self.jobs.status(job_id, owner)
            if current["state"] not in {"paused", "paused_recoverable"}:
                raise ValueError("JOB_STATE_CONFLICT")
            prior = self._job_tasks.get(job_id)
            if prior is not None:
                prior.cancel()
                await asyncio.gather(prior, return_exceptions=True)
            self._check_job_capacity()
        changed = self.jobs.transition(job_id, owner, operation)
        if operation == "resume":
            self._schedule_job(job_id, owner)
        elif operation in {"pause", "cancel"} and job_id in self._job_tasks:
            task = self._job_tasks[job_id]
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        return changed

    def _check_job_capacity(self) -> None:
        counts = self._job_counts()
        if counts["queued"] + counts["running"] >= self.config.jobs.max_active:
            raise ValueError("JOB_CAPACITY_REACHED")

    def _schedule_job(self, job_id: str, owner: str) -> None:
        task = asyncio.create_task(self._run_job(job_id, owner))
        self._job_tasks[job_id] = task

        def done(completed):
            if self._job_tasks.get(job_id) is completed:
                self._job_tasks.pop(job_id, None)
            if completed.cancelled():
                self.jobs.interrupt(job_id, owner)

        task.add_done_callback(done)

    async def _run_job(self, job_id: str, owner: str) -> None:
        job = self.jobs.start(job_id, owner, self.config.jobs.lease_seconds)
        if job["state"] != "running":
            return
        limits = job["limits"]
        checkpoint = job["progress"].get("checkpoint", {})
        checkpoint["job_id"] = job_id
        elapsed_before = checkpoint.get("elapsed_seconds", 0)
        started = self.clock.monotonic()

        def elapsed():
            return elapsed_before + max(0, self.clock.monotonic() - started)

        def heartbeat():
            self.jobs.heartbeat(
                job_id,
                owner,
                elapsed(),
                min(self.config.jobs.lease_seconds, max(0, limits["timeout_seconds"] - elapsed())),
            )

        def save(state):
            state["elapsed_seconds"] = elapsed()
            self.jobs.checkpoint(job_id, owner, state, self.config.storage.entry_max_bytes)

        async def renew():
            while True:
                await self.clock.sleep(max(0.05, self.config.jobs.lease_seconds / 3))
                heartbeat()

        renewal = None
        try:
            remaining = limits["timeout_seconds"] - elapsed_before
            if remaining <= 0:
                raise TimeoutError
            heartbeat()
            renewal = asyncio.create_task(renew())
            result = await asyncio.wait_for(
                self.deep_research(
                    job["request"]["question"],
                    max_sources=limits["max_sources"],
                    max_pages=limits["max_pages"],
                    max_chars=6000,
                    client=owner,
                    _checkpoint=checkpoint,
                    _checkpoint_save=save,
                ),
                timeout=remaining,
            )
            current = self.jobs.status(job_id, owner)
            if current["state"] == "running":
                error = None if result.get("ok") else (result.get("error") or {}).get("code", "RESEARCH_FAILED")
                if not error and not result.get("items"):
                    error = "NO_RESEARCH_EVIDENCE"
                partial = bool(result.get("warnings") or (result.get("page") or {}).get("next_cursor"))
                self.jobs.finish(job_id, owner, {"result": result, "partial": partial}, error)
        except asyncio.CancelledError:
            self.jobs.interrupt(job_id, owner)
            return
        except TimeoutError:
            self.jobs.finish(job_id, owner, {}, "JOB_TIMEOUT")
        except Exception:
            self.jobs.finish(job_id, owner, {}, "UPSTREAM_UNAVAILABLE")
        finally:
            if renewal is not None:
                renewal.cancel()
                await asyncio.gather(renewal, return_exceptions=True)
            heartbeat()

    def health(self) -> dict:
        return {
            "status": "ok",
            "version": __version__,
            "result_schema_version": "1.5",
            "database_schema_version": DATABASE_SCHEMA_VERSION,
            "database": "ok",
            "exa": "unknown",
            "search_fallback": "ready",
            "http": "ready",
            "crawl": "lazy",
            "reddit": "ready",
            "vault": "ready",
            "connections": {
                "ready": sum(item["status"] == "ready" for item in self.connections.list()),
                "revoked": sum(item["status"] == "revoked" for item in self.connections.list()),
            },
            "jobs": self._job_counts(),
            "optional_providers": self.optional_providers.status(),
            "cache_entries": self.cache.stats()["entries"],
            "started_at": self.started_at,
        }

    def stats(self) -> dict:
        return {
            "started_at": self.started_at,
            "queues": self.coordinator.stats(),
            "cache": self.cache.stats(),
            "snapshots": self._snapshot_stats(),
            "jobs": self._job_counts(),
            "profiles": {
                "unidentified": {
                    "default": self.config.output.unidentified_default_chars,
                    "ceiling": self.config.output.unidentified_ceiling_chars,
                }
            },
            "providers": self.rate.status(),
            "optional_providers": self.optional_providers.status(),
        }

    def _job_counts(self) -> dict:
        with sqlite3.connect(self.config.storage.database) as db:
            rows = db.execute("SELECT state,COUNT(*) FROM jobs GROUP BY state").fetchall()
        result = {"queued": 0, "running": 0, "paused": 0}
        result.update(dict(rows))
        return result
