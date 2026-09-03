"""Read-only GitHub API research with optional operator-owned authentication."""

from __future__ import annotations

import asyncio
import base64
import json
import re
import urllib.parse
from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from contextvars import ContextVar
from datetime import datetime, timedelta
from typing import Any

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from ..clock import SystemClock, rfc3339
from ..connections.store import ConnectionStore
from ..models import EvidenceItem, ProviderResult
from ..security import validate_url
from .http_fetch import PinnedTransport, resolve_public

API_BASE = "https://api.github.com"
API_VERSION = "2026-03-10"
ACCEPT = "application/vnd.github+json"
RequestJson = Callable[[str, str, dict[str, str], dict[str, Any] | None], Awaitable[Any]]


def _b64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def build_app_jwt(app_id: str, private_key_pem: str, issued_at: int) -> str:
    """Build the short-lived RS256 JWT required to mint an installation token."""

    header = _b64url(json.dumps({"alg": "RS256", "typ": "JWT"}, separators=(",", ":")).encode())
    claims = _b64url(
        json.dumps(
            {"iat": issued_at - 60, "exp": issued_at + 540, "iss": str(app_id)},
            separators=(",", ":"),
        ).encode()
    )
    signing_input = f"{header}.{claims}".encode("ascii")
    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    signature = key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    return f"{header}.{claims}.{_b64url(signature)}"


class GitHubProvider:
    """Use a configured token/GitHub App without exposing credentials to callers."""

    SUPPORTED_KINDS = {"code", "issues", "pulls", "commits", "releases", "docs", "discussions"}

    def __init__(
        self,
        connections: ConnectionStore,
        clock=None,
        requester: RequestJson | None = None,
        *,
        max_response_bytes: int = 20_971_520,
        timeout_seconds: float = 30,
    ) -> None:
        self.connections = connections
        self.clock = clock or SystemClock()
        self._requester = requester or self._request_json
        self.max_response_bytes = max_response_bytes
        self.timeout_seconds = timeout_seconds
        self._installation_token: str | None = None
        self._installation_token_expires_at = None
        self._installation_token_connection_id: str | None = None
        self._mint_lock = asyncio.Lock()
        self._remaining_operation_bytes: ContextVar[int | None] = ContextVar("github_operation_bytes", default=None)

    @asynccontextmanager
    async def _operation(self):
        # Task-local accounting: parallel callers must not spend each other's
        # budget. Token setup and every REST/GraphQL follow-up share this scope.
        budget = self._remaining_operation_bytes.set(self.max_response_bytes)
        deadline = asyncio.timeout(self.timeout_seconds)
        try:
            async with deadline:
                yield
                # Synchronous parsing cannot be preempted, but an over-deadline
                # result must not be reported as successful after it returns.
                if asyncio.get_running_loop().time() >= deadline.when():
                    raise TimeoutError("GITHUB_OPERATION_TIMEOUT")
        except TimeoutError:
            if deadline.expired():
                raise TimeoutError("GITHUB_OPERATION_TIMEOUT") from None
            raise
        finally:
            self._remaining_operation_bytes.reset(budget)

    def _connection(self) -> dict | None:
        for connection in self.connections.list():
            if connection["status"] == "ready" and connection["provider"].strip().casefold() in {
                "github",
                "github_app",
                "github app",
            }:
                return connection
        return None

    async def _request_json(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any] | None,
    ) -> Any:
        url = API_BASE + path
        target = validate_url(url)
        try:
            async with asyncio.timeout(self.timeout_seconds):
                address = await resolve_public(target)
                async with httpx.AsyncClient(
                    transport=PinnedTransport(target, address),
                    trust_env=False,
                    timeout=self.timeout_seconds,
                    follow_redirects=False,
                ) as client:
                    async with client.stream(method, url, headers=headers, json=body) as response:
                        response.raise_for_status()
                        payload = bytearray()
                        async for chunk in response.aiter_bytes():
                            if len(payload) + len(chunk) > self.max_response_bytes:
                                raise ValueError("GITHUB_RESPONSE_TOO_LARGE")
                            remaining = self._remaining_operation_bytes.get()
                            if remaining is not None:
                                if len(chunk) > remaining:
                                    raise ValueError("GITHUB_OPERATION_TOO_LARGE")
                                self._remaining_operation_bytes.set(remaining - len(chunk))
                            payload.extend(chunk)
        except (TimeoutError, httpx.TimeoutException):
            raise TimeoutError("GITHUB_REQUEST_TIMEOUT") from None
        try:
            result = json.loads(payload)
        except (ValueError, UnicodeError):
            raise ValueError("GITHUB_RESPONSE_INVALID") from None
        if not isinstance(result, (dict, list)):
            raise ValueError("GITHUB_RESPONSE_INVALID")
        return result

    @staticmethod
    def _headers(token: str | None) -> dict[str, str]:
        headers = {
            "Accept": ACCEPT,
            "X-GitHub-Api-Version": API_VERSION,
            "User-Agent": "halo-research-gateway/0.1",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    async def _token(self, connection: dict) -> str:
        secret = self.connections.secret(connection["connection_id"])
        static_token = secret.get("access_token") or secret.get("token") or secret.get("value")
        if static_token:
            return static_token
        required = {"app_id", "installation_id", "private_key_pem"}
        if not required.issubset(secret):
            raise ValueError("GITHUB_CONNECTION_INVALID")
        async with self._mint_lock:
            now = self.clock.utcnow()
            if (
                self._installation_token
                and self._installation_token_connection_id == connection["connection_id"]
                and self._installation_token_expires_at
                and now + timedelta(minutes=5) < self._installation_token_expires_at
            ):
                return self._installation_token
            jwt = build_app_jwt(secret["app_id"], secret["private_key_pem"], int(now.timestamp()))
            response = await self._requester(
                "POST",
                f"/app/installations/{urllib.parse.quote(secret['installation_id'], safe='')}/access_tokens",
                self._headers(jwt),
                None,
            )
            token = str(response.get("token", ""))
            if not token:
                raise ValueError("GITHUB_INSTALLATION_TOKEN_MISSING")
            expires_at = response.get("expires_at")
            self._installation_token = token
            self._installation_token_connection_id = connection["connection_id"]
            self._installation_token_expires_at = (
                datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
                if expires_at
                else now + timedelta(minutes=55)
            )
            return token

    @staticmethod
    def _item(raw: dict[str, Any], kind: str, retrieved_at: str) -> EvidenceItem:
        repository = raw.get("repository") or {}
        url = raw.get("html_url") or raw.get("url") or "https://github.com"
        title = raw.get("title") or raw.get("name") or raw.get("path") or raw.get("sha")
        snippet = raw.get("body") or raw.get("description") or raw.get("message")
        if isinstance(snippet, str):
            snippet = snippet[:4000]
        metadata = {
            "kind": kind,
            "repository": repository.get("full_name") or raw.get("repository_url"),
            "path": raw.get("path"),
            "sha": raw.get("sha") or raw.get("head_sha") or raw.get("target_commitish"),
            "number": raw.get("number"),
            "state": raw.get("state"),
            "author": (raw.get("user") or raw.get("author") or {}).get("login")
            if isinstance(raw.get("user") or raw.get("author") or {}, dict)
            else None,
        }
        return EvidenceItem(
            title=str(title) if title is not None else None,
            url=str(url),
            published_at=raw.get("published_at")
            or raw.get("created_at")
            or raw.get("commit", {}).get("author", {}).get("date"),
            retrieved_at=retrieved_at,
            source="api.github.com",
            snippet=snippet,
            metadata={key: value for key, value in metadata.items() if value is not None},
        )

    async def research(
        self,
        query: str,
        repository: str | None,
        kinds: list[str] | None,
        ref: str | None,
        max_results: int,
    ) -> ProviderResult:
        async with self._operation():
            return await self._research(query, repository, kinds, ref, max_results)

    async def _research(
        self,
        query: str,
        repository: str | None,
        kinds: list[str] | None,
        ref: str | None,
        max_results: int,
    ) -> ProviderResult:
        if repository and (
            not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
            or any(part in {".", ".."} for part in repository.split("/"))
        ):
            raise ValueError("GITHUB_REPOSITORY_INVALID")
        if ref and (len(ref) > 256 or any(ord(char) < 32 for char in ref)):
            raise ValueError("GITHUB_REF_INVALID")
        connection = self._connection()
        if connection is None:
            return ProviderResult("github-public", [], ["GITHUB_AUTH_NOT_CONFIGURED"], 0)
        token = await self._token(connection)
        selected = list(dict.fromkeys(kinds or ["code", "issues", "pulls", "commits", "releases", "docs"]))
        warnings: list[str] = []
        unsupported = [kind for kind in selected if kind not in self.SUPPORTED_KINDS]
        if unsupported:
            warnings.append("GITHUB_KIND_UNSUPPORTED:" + ",".join(sorted(unsupported)))
        selected = [kind for kind in selected if kind in self.SUPPORTED_KINDS]
        non_ref_kinds = set(selected) & {"issues", "pulls", "discussions"}
        if ref and non_ref_kinds:
            warnings.append("GITHUB_REF_NOT_APPLICABLE:" + ",".join(sorted(non_ref_kinds)))
        headers = self._headers(token)
        retrieved_at = rfc3339(self.clock.utcnow())
        items: list[EvidenceItem] = []
        per_kind = max(1, min(30, max_results))
        for kind in selected:
            if len(items) >= max_results:
                break
            if kind == "discussions":
                discussion_result = await self._discussion_search(query, repository, max_results - len(items), headers)
                items.extend(discussion_result.items)
                warnings.extend(discussion_result.warnings)
                continue
            if ref and kind in {"code", "docs"}:
                if not repository:
                    warnings.append("GITHUB_REF_REQUIRES_REPOSITORY")
                    continue
                ref_result = await self._ref_content(query, repository, kind, ref, max_results - len(items), headers)
                items.extend(ref_result.items)
                warnings.extend(ref_result.warnings)
                continue
            if kind == "releases":
                if not repository:
                    warnings.append("GITHUB_RELEASES_REQUIRE_REPOSITORY")
                    continue
                path = (
                    f"/repos/{repository}/releases/tags/{urllib.parse.quote(ref, safe='')}"
                    if ref
                    else f"/repos/{repository}/releases?per_page={per_kind}"
                )
                payload = await self._requester("GET", path, headers, None)
                rows = [
                    row for row in ([payload] if ref else payload) if query.casefold() in json.dumps(row).casefold()
                ]
            elif ref and kind == "commits":
                if not repository:
                    warnings.append("GITHUB_REF_REQUIRES_REPOSITORY")
                    continue
                path = f"/repos/{repository}/commits?" + urllib.parse.urlencode({"sha": ref, "per_page": 100})
                payload = await self._requester("GET", path, headers, None)
                rows = [
                    row
                    for row in payload
                    if query.casefold() in str((row.get("commit") or {}).get("message", "")).casefold()
                ]
                if len(payload) == 100:
                    warnings.append("GITHUB_COMMIT_HISTORY_PAGE_LIMIT")
            else:
                endpoint = (
                    "code" if kind in {"code", "docs"} else "issues" if kind in {"issues", "pulls"} else "commits"
                )
                qualifiers = []
                if repository:
                    qualifiers.append(f"repo:{repository}")
                if kind == "issues":
                    qualifiers.append("is:issue")
                elif kind == "pulls":
                    qualifiers.append("is:pr")
                elif kind == "docs":
                    qualifiers.append("extension:md")
                q = " ".join([query, *qualifiers])
                path = f"/search/{endpoint}?q={urllib.parse.quote(q)}&per_page={per_kind}"
                payload = await self._requester("GET", path, headers, None)
                rows = payload.get("items", [])
            for row in rows:
                items.append(self._item(row, kind, retrieved_at))
                if len(items) >= max_results:
                    break
        return ProviderResult("github-api", items, warnings, len(items))

    @staticmethod
    def _discussion_item(raw: dict, retrieved_at: str, depth: int = 0) -> EvidenceItem:
        return EvidenceItem(
            url=raw["url"],
            title=raw.get("title"),
            content=raw.get("bodyText") or raw.get("body") or "",
            published_at=raw.get("createdAt"),
            retrieved_at=retrieved_at,
            source="api.github.com",
            metadata={
                "kind": "discussions",
                "repository": (raw.get("repository") or {}).get("nameWithOwner"),
                "number": raw.get("number"),
                "node_id": raw.get("id"),
                "author": (raw.get("author") or {}).get("login"),
                "depth": depth,
                "is_answer": bool(raw.get("isAnswer")),
                "reply_count": (raw.get("comments") or {}).get("totalCount"),
            },
        )

    async def _graphql(self, query: str, variables: dict, headers: dict) -> dict:
        # Only internal constant read queries use this path; user text is bound
        # as a variable, never interpolated into GraphQL syntax.
        if not query.lstrip().startswith("query"):
            raise ValueError("GITHUB_READ_QUERY_REQUIRED")
        payload = await self._requester("POST", "/graphql", headers, {"query": query, "variables": variables})
        if payload.get("errors") or not isinstance(payload.get("data"), dict):
            raise ValueError("GITHUB_GRAPHQL_ERROR")
        return payload["data"]

    async def _discussion_search(self, query: str, repository: str | None, limit: int, headers: dict) -> ProviderResult:
        query_text = query + (f" repo:{repository}" if repository else "")
        data = await self._graphql(
            """query ResearchDiscussions($query: String!, $limit: Int!) {
          search(query: $query, type: DISCUSSION, first: $limit) {
            discussionCount pageInfo { hasNextPage }
            nodes { ... on Discussion { id number title url bodyText createdAt
              author { login } repository { nameWithOwner } comments { totalCount }
            } }
          }
        }""",
            {"query": query_text, "limit": min(30, limit)},
            headers,
        )
        found = data["search"]
        items = [self._discussion_item(raw, rfc3339(self.clock.utcnow())) for raw in found.get("nodes", []) if raw]
        warnings = ["GITHUB_RESULTS_LIMIT_REACHED"] if found.get("pageInfo", {}).get("hasNextPage") else []
        return ProviderResult("github-api", items, warnings, found.get("discussionCount", len(items)))

    async def discussion_thread(self, repository: str, number: int, max_replies: int) -> ProviderResult:
        async with self._operation():
            return await self._discussion_thread(repository, number, max_replies)

    async def _discussion_thread(self, repository: str, number: int, max_replies: int) -> ProviderResult:
        if (
            not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)
            or not 0 <= max_replies <= 100
            or number < 1
        ):
            raise ValueError("GITHUB_DISCUSSION_INVALID")
        connection = self._connection()
        if connection is None:
            return ProviderResult("github-public", [], ["GITHUB_AUTH_NOT_CONFIGURED"], 0)
        owner, name = repository.split("/")
        headers = self._headers(await self._token(connection))
        data = await self._graphql(
            """query ResearchDiscussion($owner: String!, $name: String!, $number: Int!, $limit: Int!) {
          repository(owner: $owner, name: $name) { discussion(number: $number) {
            id number title url bodyText createdAt author { login } repository { nameWithOwner }
            comments(first: $limit) { totalCount pageInfo { hasNextPage }
              nodes { id url bodyText createdAt author { login } isAnswer
                replies(first: 1) { totalCount pageInfo { hasNextPage endCursor }
                  nodes { id url bodyText createdAt author { login } isAnswer }
                }
              }
            }
          } }
        }""",
            {"owner": owner, "name": name, "number": number, "limit": max_replies},
            headers,
        )
        raw = (data.get("repository") or {}).get("discussion")
        if not raw:
            return ProviderResult("github-api", [], ["GITHUB_DISCUSSION_UNAVAILABLE"], 0)
        now = rfc3339(self.clock.utcnow())
        items = [self._discussion_item(raw, now)]
        comments = raw.get("comments") or {}
        warnings = ["REPLY_LIMIT_REACHED"] if comments.get("pageInfo", {}).get("hasNextPage") else []
        reply_requests = 0
        for comment in comments.get("nodes", []):
            if len(items) > max_replies:
                warnings.append("REPLY_LIMIT_REACHED")
                break
            items.append(self._discussion_item(comment, now, 1))
            replies = comment.get("replies") or {}
            seen_cursors = set()
            while True:
                for reply in replies.get("nodes", []):
                    if len(items) > max_replies:
                        warnings.append("REPLY_LIMIT_REACHED")
                        break
                    items.append(self._discussion_item(reply, now, 2))
                page = replies.get("pageInfo", {})
                if not page.get("hasNextPage"):
                    break
                if len(items) > max_replies:
                    warnings.append("REPLY_LIMIT_REACHED")
                    break
                cursor = page.get("endCursor")
                if not cursor or cursor in seen_cursors or reply_requests >= 10:
                    warnings.append("NESTED_REPLIES_PARTIAL")
                    break
                seen_cursors.add(cursor)
                reply_requests += 1
                more = await self._graphql(
                    """query ResearchDiscussionReplies($id: ID!, $after: String!, $limit: Int!) {
                      node(id: $id) { ... on DiscussionComment {
                        replies(first: $limit, after: $after) { pageInfo { hasNextPage endCursor }
                          nodes { id url bodyText createdAt author { login } isAnswer }
                        }
                      } }
                    }""",
                    {"id": comment["id"], "after": cursor, "limit": max_replies + 1 - len(items)},
                    headers,
                )
                replies = (more.get("node") or {}).get("replies")
                if not replies:
                    warnings.append("NESTED_REPLIES_PARTIAL")
                    break
        return ProviderResult("github-api", items, sorted(set(warnings)), len(items))

    async def _ref_content(
        self, query: str, repository: str, kind: str, ref: str, limit: int, headers: dict
    ) -> ProviderResult:
        commit = await self._requester(
            "GET", f"/repos/{repository}/commits/{urllib.parse.quote(ref, safe='')}", headers, None
        )
        sha = commit.get("sha", "")
        tree_sha = ((commit.get("commit") or {}).get("tree") or {}).get("sha", "")
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha) or not re.fullmatch(r"[0-9a-f]{40,64}", tree_sha):
            raise ValueError("GITHUB_REF_RESPONSE_INVALID")
        tree = await self._requester("GET", f"/repos/{repository}/git/trees/{tree_sha}?recursive=1", headers, None)
        warnings = ["GITHUB_REF_LITERAL_SEARCH"]
        if tree.get("truncated"):
            warnings.append("GITHUB_REF_TREE_TRUNCATED")
        files = [row for row in tree.get("tree", []) if row.get("type") == "blob"]
        if kind == "docs":
            files = [
                row
                for row in files
                if str(row.get("path", "")).lower().endswith((".md", ".mdx", ".rst", ".txt", ".adoc"))
            ]
        files.sort(key=lambda row: (query.casefold() not in row["path"].casefold(), row["path"]))
        items = []
        total_bytes = 0
        scanned = 0
        for row in files:
            if scanned >= 40 or total_bytes >= 4_000_000 or len(items) >= limit:
                warnings.append("GITHUB_REF_SCAN_LIMIT_REACHED")
                break
            if row.get("size", 0) > 250_000:
                warnings.append("GITHUB_REF_LARGE_FILE_SKIPPED")
                continue
            blob_sha = row.get("sha", "")
            if not re.fullmatch(r"[0-9a-f]{40,64}", blob_sha):
                raise ValueError("GITHUB_BLOB_RESPONSE_INVALID")
            blob = await self._requester("GET", f"/repos/{repository}/git/blobs/{blob_sha}", headers, None)
            scanned += 1
            if blob.get("encoding") != "base64":
                warnings.append("GITHUB_REF_FILE_UNAVAILABLE")
                continue
            body = base64.b64decode(blob.get("content", ""))
            total_bytes += len(body)
            if len(body) > 250_000:
                warnings.append("GITHUB_REF_LARGE_FILE_SKIPPED")
                continue
            if b"\x00" in body:
                continue
            text = body.decode("utf-8", errors="replace")
            if query.casefold() not in (row["path"] + "\n" + text).casefold():
                continue
            items.append(
                EvidenceItem(
                    url=f"https://github.com/{repository}/blob/{sha}/{urllib.parse.quote(row['path'], safe='/')}",
                    title=row["path"],
                    content=text,
                    retrieved_at=rfc3339(self.clock.utcnow()),
                    source="api.github.com",
                    metadata={
                        "kind": kind,
                        "repository": repository,
                        "path": row["path"],
                        "sha": sha,
                        "blob_sha": blob_sha,
                        "ref": ref,
                    },
                )
            )
        return ProviderResult("github-api", items, sorted(set(warnings)), len(items))
