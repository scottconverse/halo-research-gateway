"""Structured bounded adapters for public technical discussion sources."""

from __future__ import annotations

import html
import json
import re
import urllib.parse
from datetime import UTC, datetime, timedelta
from typing import Any

from ..clock import rfc3339
from ..models import EvidenceItem, ProviderResult
from ..security import validate_url

SUPPORTED_SOURCES = {"stackoverflow", "stackexchange", "hackernews", "github_discussions", "forums"}
STACK_HOSTS = {
    "stackoverflow.com": "stackoverflow",
    "superuser.com": "superuser",
    "serverfault.com": "serverfault",
    "askubuntu.com": "askubuntu",
    "stackapps.com": "stackapps",
    "mathoverflow.net": "mathoverflow",
}


def _plain_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = re.sub(r"<[^>]+>", " ", value)
    text = re.sub(r"\s+", " ", html.unescape(text)).strip()
    return text or None


def _unix_time(value: object) -> str | None:
    try:
        return rfc3339(datetime.fromtimestamp(int(value), UTC))
    except (TypeError, ValueError, OverflowError):
        return None


def _stack_site(host: str) -> str | None:
    if host in STACK_HOSTS:
        return STACK_HOSTS[host]
    if host.endswith(".stackexchange.com"):
        return host.removesuffix(".stackexchange.com")
    return None


def community_source_for_url(url: str) -> str:
    target = validate_url(url)
    host = target.host.removeprefix("www.")
    if host in {"reddit.com", "old.reddit.com"}:
        return "reddit"
    if _stack_site(host):
        return "stackexchange"
    if host == "news.ycombinator.com":
        return "hackernews"
    path = target.path_query.split("?", 1)[0]
    if host == "github.com" and re.fullmatch(r"/[^/]+/[^/]+/discussions/\d+/?", path):
        return "github_discussions"
    return "forums"


class CommunityProvider:
    def __init__(self, http, github, search, clock) -> None:
        self.http = http
        self.github = github
        self.search_provider = search
        self.clock = clock

    async def _json(self, url: str) -> dict[str, Any]:
        _, _, headers, body = await self.http.download(url, accept="application/json")
        content_type = headers.get("content-type", "")
        match = re.search(r"charset=([^;\s]+)", content_type, flags=re.IGNORECASE)
        text = body.decode(match.group(1).strip("\"'") if match else "utf-8", errors="replace")
        value = json.loads(text)
        if not isinstance(value, dict):
            raise ValueError("COMMUNITY_RESPONSE_INVALID")
        return value

    @staticmethod
    def _selected_sources(sources: list[str] | None) -> list[str]:
        values = [str(value).casefold() for value in (sources or ["all"])]
        if "all" in values:
            values = ["stackoverflow", "hackernews", "github_discussions", "forums"]
        unknown = set(values) - SUPPORTED_SOURCES
        if unknown:
            raise ValueError("INVALID_COMMUNITY_SOURCE")
        return list(dict.fromkeys(values))

    async def search(
        self, query: str, sources: list[str] | None, max_results: int, freshness_days: int | None
    ) -> ProviderResult:
        selected = self._selected_sources(sources)
        buckets: list[list[EvidenceItem]] = []
        warnings = ["COMMUNITY_EVIDENCE_NOT_FACT"]
        available = 0
        for source in selected:
            try:
                if source in {"stackoverflow", "stackexchange"}:
                    bucket, count, source_warnings = await self._stack_search(
                        query, source, max_results, freshness_days
                    )
                elif source == "hackernews":
                    bucket, count, source_warnings = await self._hn_search(query, max_results, freshness_days)
                elif source == "github_discussions":
                    github = await self.github.research(query, None, ["discussions"], None, max_results)
                    bucket = github.items
                    for item in bucket:
                        item.metadata = dict(item.metadata or {}) | {
                            "community_source": "github_discussions",
                            "authenticated_source": github.provider == "github-api",
                        }
                    count = github.available if github.available is not None else len(bucket)
                    source_warnings = list(github.warnings)
                    if freshness_days is not None:
                        source_warnings.append("GITHUB_DISCUSSIONS_FRESHNESS_FILTER_PARTIAL")
                    if not bucket:
                        source_warnings.append("GITHUB_DISCUSSIONS_UNAVAILABLE")
                else:
                    discovered = await self.search_provider.search(
                        query, max_results=max_results, freshness_days=freshness_days
                    )
                    bucket = discovered.items
                    for item in bucket:
                        item.metadata = dict(item.metadata or {}) | {"community_source": "forums"}
                    count = discovered.available if discovered.available is not None else len(bucket)
                    source_warnings = [*discovered.warnings, "FORUM_DISCOVERY_UNSTRUCTURED"]
                buckets.append(bucket)
                available += count
                warnings.extend(source_warnings)
            except Exception:
                warnings.append(source.upper() + "_UNAVAILABLE")

        items: list[EvidenceItem] = []
        for index in range(max((len(bucket) for bucket in buckets), default=0)):
            for bucket in buckets:
                if index < len(bucket):
                    items.append(bucket[index])
                    if len(items) >= max_results:
                        break
            if len(items) >= max_results:
                break
        return ProviderResult("community-public", items, sorted(set(warnings)), available)

    async def _stack_search(
        self, query: str, source: str, max_results: int, freshness_days: int | None
    ) -> tuple[list[EvidenceItem], int, list[str]]:
        params: dict[str, str | int] = {
            "order": "desc",
            "sort": "activity",
            "q": query,
            "site": "stackoverflow",
            "filter": "withbody",
            "pagesize": max_results,
        }
        warnings = []
        if source == "stackexchange":
            warnings.append("STACKEXCHANGE_SEARCH_DEFAULTED_TO_STACKOVERFLOW")
        if freshness_days is not None:
            cutoff = self.clock.utcnow() - timedelta(days=freshness_days)
            params["fromdate"] = int(cutoff.timestamp())
        url = "https://api.stackexchange.com/2.3/search/advanced?" + urllib.parse.urlencode(params)
        payload = await self._json(url)
        items = [self._stack_question(raw, source) for raw in payload.get("items", [])[:max_results]]
        if payload.get("has_more"):
            warnings.append("STACKEXCHANGE_RESULTS_TRUNCATED")
        if payload.get("quota_remaining") is not None and int(payload["quota_remaining"]) < 10:
            warnings.append("STACKEXCHANGE_QUOTA_LOW")
        return items, int(payload.get("total", len(items))), warnings

    def _stack_question(self, raw: dict[str, Any], source: str, depth: int = 0) -> EvidenceItem:
        question_id = raw.get("question_id")
        metadata = {
            "community_source": source,
            "question_id": question_id,
            "author": (raw.get("owner") or {}).get("display_name"),
            "score": raw.get("score"),
            "answer_count": raw.get("answer_count"),
            "is_answered": raw.get("is_answered"),
            "accepted_answer_id": raw.get("accepted_answer_id"),
            "last_activity_at": _unix_time(raw.get("last_activity_date")),
        }
        if depth:
            metadata["depth"] = depth
        link = str(raw.get("link") or f"https://stackoverflow.com/questions/{question_id}")
        return EvidenceItem(
            title=_plain_text(raw.get("title")),
            url=link,
            published_at=_unix_time(raw.get("creation_date")),
            retrieved_at=rfc3339(self.clock.utcnow()),
            source=urllib.parse.urlsplit(link).hostname,
            content=_plain_text(raw.get("body")),
            metadata={key: value for key, value in metadata.items() if value is not None},
        )

    async def _hn_search(
        self, query: str, max_results: int, freshness_days: int | None
    ) -> tuple[list[EvidenceItem], int, list[str]]:
        params: dict[str, str | int] = {"query": query, "tags": "story", "hitsPerPage": max_results}
        if freshness_days is not None:
            cutoff = int((self.clock.utcnow() - timedelta(days=freshness_days)).timestamp())
            params["numericFilters"] = f"created_at_i>{cutoff}"
        url = "https://hn.algolia.com/api/v1/search?" + urllib.parse.urlencode(params)
        payload = await self._json(url)
        items = [self._hn_story(raw) for raw in payload.get("hits", [])[:max_results]]
        warnings = ["HACKERNEWS_SEARCH_USES_PUBLIC_ALGOLIA_INDEX"]
        return items, int(payload.get("nbHits", len(items))), warnings

    def _hn_story(self, raw: dict[str, Any]) -> EvidenceItem:
        item_id = raw.get("objectID") or raw.get("story_id") or raw.get("id")
        metadata = {
            "community_source": "hackernews",
            "item_id": int(item_id) if str(item_id).isdigit() else item_id,
            "author": raw.get("author"),
            "score": raw.get("points"),
            "reply_count": raw.get("num_comments"),
            "external_url": raw.get("url"),
        }
        return EvidenceItem(
            title=_plain_text(raw.get("title") or raw.get("story_title")),
            url=f"https://news.ycombinator.com/item?id={item_id}",
            published_at=raw.get("created_at") or _unix_time(raw.get("created_at_i")),
            retrieved_at=rfc3339(self.clock.utcnow()),
            source="news.ycombinator.com",
            content=_plain_text(raw.get("story_text") or raw.get("comment_text") or raw.get("text")),
            metadata={key: value for key, value in metadata.items() if value is not None},
        )

    async def thread(self, url: str, max_replies: int, sort: str) -> ProviderResult:
        source = community_source_for_url(url)
        if source == "stackexchange":
            return await self._stack_thread(url, max_replies, sort)
        if source == "hackernews":
            return await self._hn_thread(url, max_replies, sort)
        if source == "github_discussions":
            return await self._github_thread(url, max_replies)
        raise ValueError("UNSUPPORTED_COMMUNITY_SOURCE")

    async def _stack_thread(self, url: str, max_replies: int, sort: str) -> ProviderResult:
        parsed = urllib.parse.urlsplit(url)
        host = (parsed.hostname or "").removeprefix("www.")
        site = _stack_site(host)
        match = re.match(r"/questions/(\d+)(?:/|$)", parsed.path)
        if site is None or match is None:
            raise ValueError("INVALID_COMMUNITY_THREAD")
        question_id = int(match.group(1))
        question_url = "https://api.stackexchange.com/2.3/questions/{}?{}".format(
            question_id, urllib.parse.urlencode({"site": site, "filter": "withbody"})
        )
        order, answer_sort = {
            "top": ("desc", "votes"),
            "oldest": ("asc", "creation"),
            "newest": ("desc", "creation"),
            "source_default": ("desc", "votes"),
        }[sort]
        answer_url = "https://api.stackexchange.com/2.3/questions/{}/answers?{}".format(
            question_id,
            urllib.parse.urlencode(
                {
                    "order": order,
                    "sort": answer_sort,
                    "site": site,
                    "filter": "withbody",
                    "pagesize": max_replies,
                }
            ),
        )
        question_payload = await self._json(question_url)
        answer_payload = await self._json(answer_url)
        roots = question_payload.get("items", [])
        if not roots:
            return ProviderResult("stackexchange-api", [], ["COMMUNITY_THREAD_UNAVAILABLE"], 0)
        source = "stackoverflow" if site == "stackoverflow" else "stackexchange"
        items = [self._stack_question(roots[0], source)]
        for raw in answer_payload.get("items", [])[:max_replies]:
            answer_id = raw.get("answer_id")
            metadata = {
                "community_source": source,
                "answer_id": answer_id,
                "parent_id": question_id,
                "depth": 1,
                "author": (raw.get("owner") or {}).get("display_name"),
                "score": raw.get("score"),
                "is_accepted": raw.get("is_accepted"),
            }
            items.append(
                EvidenceItem(
                    url=f"https://{host}/a/{answer_id}",
                    published_at=_unix_time(raw.get("creation_date")),
                    retrieved_at=rfc3339(self.clock.utcnow()),
                    source=host,
                    content=_plain_text(raw.get("body")),
                    metadata={key: value for key, value in metadata.items() if value is not None},
                )
            )
        warnings = ["COMMUNITY_EVIDENCE_NOT_FACT"]
        if answer_payload.get("has_more"):
            warnings.append("REPLY_LIMIT_REACHED")
        return ProviderResult("stackexchange-api", items, warnings, len(items))

    async def _hn_thread(self, url: str, max_replies: int, sort: str) -> ProviderResult:
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        item_id = (query.get("id") or [""])[0]
        if not item_id.isdigit():
            raise ValueError("INVALID_COMMUNITY_THREAD")
        root = await self._json(f"https://hn.algolia.com/api/v1/items/{item_id}")
        root_item = self._hn_node(root, 0, None)
        replies: list[EvidenceItem] = []

        def visit(nodes: list[dict[str, Any]], depth: int, parent: int | str) -> None:
            for node in nodes:
                if len(replies) >= max_replies:
                    return
                replies.append(self._hn_node(node, depth, parent))
                visit(node.get("children") or [], depth + 1, node.get("id"))

        visit(root.get("children") or [], 1, root.get("id"))
        if sort != "source_default":
            if sort == "top":
                replies.sort(key=lambda item: int(item.metadata.get("score") or 0), reverse=True)
            else:
                replies.sort(key=lambda item: item.published_at or "", reverse=sort == "newest")
        warnings = ["COMMUNITY_EVIDENCE_NOT_FACT", "HACKERNEWS_THREAD_USES_PUBLIC_ALGOLIA_INDEX"]
        if self._hn_has_more(root.get("children") or [], max_replies):
            warnings.append("REPLY_LIMIT_REACHED")
        return ProviderResult("hackernews-public-api", [root_item, *replies], warnings, len(replies) + 1)

    def _hn_node(self, raw: dict[str, Any], depth: int, parent: int | str | None) -> EvidenceItem:
        item_id = raw.get("id") or raw.get("objectID")
        metadata = {
            "community_source": "hackernews",
            "item_id": item_id,
            "parent_id": parent,
            "depth": depth,
            "author": raw.get("author"),
            "score": raw.get("points"),
        }
        return EvidenceItem(
            title=_plain_text(raw.get("title")),
            url=f"https://news.ycombinator.com/item?id={item_id}",
            published_at=raw.get("created_at") or _unix_time(raw.get("created_at_i")),
            retrieved_at=rfc3339(self.clock.utcnow()),
            source="news.ycombinator.com",
            content=_plain_text(raw.get("text")),
            metadata={key: value for key, value in metadata.items() if value is not None},
        )

    @staticmethod
    def _hn_has_more(nodes: list[dict[str, Any]], limit: int) -> bool:
        stack = list(reversed(nodes))
        count = 0
        while stack and count <= limit:
            node = stack.pop()
            count += 1
            stack.extend(reversed(node.get("children") or []))
        return count > limit

    async def _github_thread(self, url: str, max_replies: int) -> ProviderResult:
        parsed = urllib.parse.urlsplit(url)
        match = re.fullmatch(r"/([^/]+)/([^/]+)/discussions/(\d+)/?", parsed.path)
        if match is None:
            raise ValueError("INVALID_COMMUNITY_THREAD")
        repository = f"{match.group(1)}/{match.group(2)}"
        discussion_id = int(match.group(3))
        result = await self.github.discussion_thread(repository, discussion_id, max_replies)
        for item in result.items:
            item.metadata = dict(item.metadata or {}) | {
                "community_source": "github_discussions",
                "authenticated_source": result.provider == "github-api",
            }
        warnings = list(result.warnings)
        if not result.items:
            warnings.append("GITHUB_DISCUSSIONS_UNAVAILABLE")
        return ProviderResult("github-discussions", result.items, sorted(set(warnings)), result.available)
