"""Application service implementing the semantic Halo research contracts."""

from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import urllib.parse
import uuid
from pathlib import Path

import httpx

from .actions.store import ActionStore
from .cache import Cache
from .clock import SystemClock, rfc3339
from .config import GatewayConfig
from .connections.chrome_import import ChromeImporter
from .connections.oauth import OAuthManager
from .connections.store import ConnectionStore
from .coordinator import Coordinator, QueuePolicy
from .cursor import CursorCodec, CursorError
from .envelope import build_envelope, error_envelope
from .jobs.manager import JobManager
from .migrations import SCHEMA_VERSION as DATABASE_SCHEMA_VERSION
from .migrations import migrate
from .models import LocalTarget, ProviderResult
from .providers.crawl4ai_provider import Crawl4AIProvider
from .providers.document_extract import DocumentProvider
from .providers.exa import ExaProvider, ExaRateLimited
from .providers.http_fetch import HttpFetchProvider, PinnedTransport, resolve_public
from .providers.optional import OptionalProviderRegistry
from .providers.reddit_rss import parse_atom, search_url, thread_rss_url
from .providers.search import DdgsSearchProvider
from .rate_limit import RateLedger
from .security import UrlPolicyError, validate_url


class HaloService:
    def __init__(self, config: GatewayConfig) -> None:
        self.config = config
        self.clock = SystemClock()
        config.ensure_directories()
        migrate(config.storage.database, config.storage.backup_directory)
        self.cache = Cache(config.storage.database, config.storage.cache_max_bytes, config.storage.entry_max_bytes)
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
        self.crawler = Crawl4AIProvider(config.crawl.base_directory, self.clock)
        self.documents = DocumentProvider(self.http, self.clock)
        self.jobs = JobManager(config.storage.database, self.clock)
        self.actions = ActionStore(config.storage.database, config.actions.approval_ttl_seconds, self.clock)
        self.rate = RateLedger(config.storage.database, self.clock)
        runtime_root = Path(config.storage.database).parent.parent
        self.connections = ConnectionStore(config.storage.database, runtime_root / "vault", self.clock)
        self.optional_providers = OptionalProviderRegistry(
            config.storage.database, self.connections, config.captcha, config.proxy
        )
        self.oauth = OAuthManager(self.connections)
        self.chrome_importer = ChromeImporter(runtime_root / "browser" / "profiles")
        self.cursors = CursorCodec(
            Path(config.storage.database).parent / "cursor-hmac.key", config.output.cursor_ttl_seconds
        )
        self._snapshots: dict[str, ProviderResult] = {}
        self.started_at = rfc3339(self.clock.utcnow())
        self._job_tasks: dict[str, asyncio.Task] = {}
        self._oauth_tasks: dict[str, asyncio.Task] = {}
        self.jobs.recover_expired()

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
        return self.actions.prepare({"action": "chrome_import", "import": preview})

    async def chrome_import_execute(self, plan_id: str, approval_token: str, idempotency_key: str) -> dict:
        async def executor(plan):
            if plan.get("action") != "chrome_import":
                raise ValueError("CHROME_IMPORT_PLAN_REQUIRED")
            return await asyncio.to_thread(self.chrome_importer.execute, plan["import"])

        return await self.actions.execute(plan_id, approval_token, idempotency_key, executor)

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
        items = self._chunk_items([x.as_dict() for x in result.items], budget)
        snapshot_key = result.cache_key or "snapshot:" + uuid.uuid4().hex
        result.cache_key = snapshot_key
        self._snapshots[snapshot_key] = result

        def encode_cursor(page: dict) -> str:
            return self.cursors.encode(
                page | {"tool": tool, "snapshot": snapshot_key, "budget": budget, "schema": "1.5"}
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
            if state.get("tool") != tool or state.get("schema") != "1.5":
                raise CursorError("cursor does not match tool or schema")
            cursor_budget = int(state["budget"])
            if max_chars is not None and self._budget(max_chars) != cursor_budget:
                raise CursorError("cursor does not match output profile")
            snapshot_key = state["snapshot"]
            result = self._snapshots.get(snapshot_key)
            if result is None:
                cached = self.cache.get_with_age(snapshot_key)
                if cached is None:
                    return self._error(tool, "pagination", ValueError("CURSOR_EVICTED"))
                result = self._decode_result(cached[0], snapshot_key, cached[1])
            return self._envelope(tool, result, cursor_budget, state)
        except Exception as exc:
            return self._error(tool, "pagination", exc)

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
        result.cache_key = cache_key
        if cacheable and "SENSITIVE_URL_NOT_CACHED" not in result.warnings:
            self.cache.put(cache_key, self._encode_result(result), ttl_seconds)
        return result

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
            content = item.get("content") or ""
            if len(content) <= chunk_size:
                output.append(item)
                continue
            parts = [content[index : index + chunk_size] for index in range(0, len(content), chunk_size)]
            for number, part in enumerate(parts, 1):
                chunk = dict(item)
                chunk["content"] = part
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
            tool, provider, str(uuid.uuid4()), code, f"{type(exc).__name__}: operation did not complete"
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
        key = (
            "search:"
            + hashlib.sha256(
                json.dumps(
                    [query, max_results, content_type, include_domains, exclude_domains, freshness_days], sort_keys=True
                ).encode()
            ).hexdigest()
        )
        try:

            async def run():
                try:
                    self.rate.admit("exa-anonymous", self.config.exa.daily_soft_limit)
                    result = await self.exa.search(query, max_results)
                    self.rate.success("exa-anonymous")
                    return result
                except ExaRateLimited:
                    self.rate.rate_limited("exa-anonymous", threshold=1, cooldown_seconds=3600)
                    return await self.ddgs.search(
                        query,
                        max_results=max_results,
                        content_type=content_type,
                        include_domains=include_domains,
                        exclude_domains=exclude_domains,
                        freshness_days=freshness_days,
                    )
                except Exception:
                    return await self.ddgs.search(
                        query,
                        max_results=max_results,
                        content_type=content_type,
                        include_domains=include_domains,
                        exclude_domains=exclude_domains,
                        freshness_days=freshness_days,
                    )

            result = await self._cached_run("exa", client, key, 21600, run, max_age_seconds=max_age_seconds)
            return self._envelope("web_search", result, max_chars, requested=max_results)
        except Exception as exc:
            return self._error("web_search", "search", exc)

    async def web_fetch(
        self, url: str | None = None, max_chars=None, cursor=None, client="unidentified", max_age_seconds=None
    ) -> dict:
        if cursor:
            return self._resume("web_fetch", cursor, max_chars)
        if not url:
            return self._error("web_fetch", "policy", ValueError("URL_REQUIRED"))
        key = "fetch:" + hashlib.sha256(url.encode()).hexdigest()
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
        del max_depth, same_site_only, interaction, capture
        key = "crawl:" + hashlib.sha256(json.dumps([url, max_pages, mode, profile, wait_for]).encode()).hexdigest()
        try:
            result = await self._cached_run(
                "crawl",
                client,
                key,
                3600,
                lambda: self.crawler.crawl(url, max_pages=max_pages, mode=mode, wait_for=wait_for, profile=profile),
                max_age_seconds=max_age_seconds,
            )
            return self._envelope("web_crawl", result, max_chars, requested=max_pages)
        except Exception as exc:
            return self._error("web_crawl", "crawl4ai", exc)

    async def _rss(self, url: str, limit: int) -> ProviderResult:
        self.rate.admit("reddit-anonymous")
        target = validate_url(url)
        address = await resolve_public(target)
        async with httpx.AsyncClient(
            transport=PinnedTransport(target, address),
            trust_env=False,
            timeout=30,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) halo-research-gateway/0.1 (+local-personal-research)"
            },
        ) as client:
            response = await client.get(url)
            if response.status_code == 429:
                self.rate.rate_limited(
                    "reddit-anonymous",
                    self.config.reddit.max_consecutive_429,
                    self.config.reddit.circuit_cooldown_seconds,
                )
            response.raise_for_status()
            self.rate.success("reddit-anonymous")
            return parse_atom(response.content, limit=limit, clock=self.clock)

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
    ) -> dict:
        if cursor:
            return self._resume("document_extract", cursor, max_chars)
        if not url:
            return self._error("document_extract", "policy", ValueError("URL_REQUIRED"))
        key = "document:" + hashlib.sha256(json.dumps([url, pages]).encode()).hexdigest()
        try:
            from .security import is_sensitive_url

            result = await self._cached_run(
                "http",
                client,
                key,
                86400,
                lambda: self.documents.extract(url, pages),
                cacheable=not is_sensitive_url(url),
                max_age_seconds=max_age_seconds,
            )
            return self._envelope("document_extract", result, max_chars, requested=len(result.items))
        except Exception as exc:
            return self._error("document_extract", "document", exc)

    async def deep_research(
        self,
        question: str,
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
    ) -> dict:
        if cursor:
            return self._resume("deep_research", cursor, max_chars)
        del max_pages, max_depth
        try:
            search = await self.ddgs.search(
                question,
                max_results=max_sources,
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                freshness_days=freshness_days,
            )
            urls = list(seed_urls or []) + [item.url for item in search.items]
            seen = set()
            items = []
            warnings = list(search.warnings)
            for url in urls:
                if url in seen or len(items) >= max_sources:
                    continue
                seen.add(url)
                try:
                    fetched = await self.http.fetch(url)
                    items.extend(fetched.items)
                    warnings.extend(fetched.warnings)
                except Exception:
                    warnings.append("UPSTREAM_UNAVAILABLE")
            return self._envelope(
                "deep_research",
                ProviderResult("halo-deep", items, sorted(set(warnings)), len(items)),
                max_chars,
                requested=max_sources,
            )
        except Exception as exc:
            return self._error("deep_research", "halo-deep", exc)

    async def local_fetch(
        self, target: str | None = None, path: str | None = None, max_chars=None, cursor=None
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
            url = policy.build_url(path)
            async with httpx.AsyncClient(
                trust_env=False, follow_redirects=False, timeout=self.config.http.total_timeout_seconds
            ) as client:
                response = await client.get(url)
                response.raise_for_status()
                if response.is_redirect:
                    raise ValueError("LOCAL_REDIRECT_DENIED")
                from .models import EvidenceItem

                result = ProviderResult(
                    "local-http",
                    [
                        EvidenceItem(
                            url=url, retrieved_at=rfc3339(self.clock.utcnow()), source=target, content=response.text
                        )
                    ],
                    [],
                    1,
                )
            return self._envelope("local_fetch", result, max_chars, requested=1)
        except Exception as exc:
            return self._error("local_fetch", "local-http", exc)

    async def local_crawl(
        self, target: str | None = None, path: str | None = None, max_pages=1, profile=None, max_chars=None, cursor=None
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
            key = "local-crawl:" + hashlib.sha256(json.dumps([target, path, max_pages, profile]).encode()).hexdigest()
            result = await self._cached_run(
                "crawl",
                "unidentified",
                key,
                300,
                lambda: self.crawler.crawl(
                    url,
                    max_pages=max_pages,
                    mode="managed_profile" if profile else "standard",
                    profile=profile,
                    public=False,
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
        if operation == "create":
            requested_limits = {"profile": profile, **(limits or {})}
            requested_limits["max_sources"] = min(int(requested_limits.get("max_sources", 12)), 50)
            requested_limits["max_pages"] = min(
                int(requested_limits.get("max_pages", 20)), self.config.jobs.absolute_pages
            )
            requested_limits["timeout_seconds"] = min(
                int(requested_limits.get("timeout_seconds", self.config.jobs.default_timeout_seconds)),
                self.config.jobs.absolute_timeout_seconds,
            )
            created = self.jobs.create(owner, question or "", requested_limits)
            task = asyncio.create_task(self._run_job(created["job_id"], owner))
            self._job_tasks[created["job_id"]] = task
            task.add_done_callback(lambda _, key=created["job_id"]: self._job_tasks.pop(key, None))
            return created
        if operation == "status":
            return self.jobs.status(job_id, owner)
        changed = self.jobs.transition(job_id, owner, operation)
        if operation == "resume":
            task = asyncio.create_task(self._run_job(job_id, owner))
            self._job_tasks[job_id] = task
            task.add_done_callback(lambda _, key=job_id: self._job_tasks.pop(key, None))
        elif operation == "cancel" and job_id in self._job_tasks:
            self._job_tasks[job_id].cancel()
        return changed

    async def _run_job(self, job_id: str, owner: str) -> None:
        job = self.jobs.start(job_id, owner, self.config.jobs.lease_seconds)
        if job["state"] != "running":
            return
        limits = job["limits"]
        try:
            result = await asyncio.wait_for(
                self.deep_research(
                    job["request"]["question"],
                    max_sources=limits["max_sources"],
                    max_pages=limits["max_pages"],
                    max_chars=6000,
                    client=owner,
                ),
                timeout=limits["timeout_seconds"],
            )
            current = self.jobs.status(job_id, owner)
            if current["state"] == "running":
                self.jobs.finish(job_id, owner, {"result": result})
        except asyncio.CancelledError:
            return
        except TimeoutError:
            self.jobs.finish(job_id, owner, {}, "JOB_TIMEOUT")
        except Exception:
            self.jobs.finish(job_id, owner, {}, "UPSTREAM_UNAVAILABLE")

    def web_action_prepare(
        self, action: str, target_url: str, intent: str, fields: dict, connection_id=None, profile=None, max_price=None
    ) -> dict:
        if target_url.startswith(("http://", "https://")):
            validate_url(target_url)
        return self.actions.prepare(
            {
                "action": action,
                "target_url": target_url,
                "intent": intent,
                "fields": fields,
                "connection_id": connection_id,
                "profile": profile,
                "max_price": max_price,
            }
        )

    async def web_action_execute(self, plan_id: str, approval_token: str, idempotency_key: str) -> dict:
        async def execute(plan):
            target = urllib.parse.urlsplit(plan["target_url"]).hostname
            if plan["action"] != "form_submit":
                return {
                    "status": "ACTION_ADAPTER_NOT_CONFIGURED",
                    "message": "This action requires a site-specific operator-configured adapter",
                    "target": target,
                }
            try:
                return await self.http.submit_form(plan["target_url"], plan["fields"])
            except Exception:
                return {
                    "status": "ACTION_STATE_AMBIGUOUS",
                    "message": "The submission outcome could not be proven; it was not retried",
                    "target": target,
                }

        return await self.actions.execute(plan_id, approval_token, idempotency_key, execute)

    def health(self) -> dict:
        return {
            "status": "ok",
            "version": "0.1.0",
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
            "actions": "ready" if self.config.actions.enabled else "disabled",
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
