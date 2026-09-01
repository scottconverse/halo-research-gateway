"""Read-only GitHub API research with optional operator-owned authentication."""

from __future__ import annotations

import asyncio
import base64
import json
import urllib.parse
from collections.abc import Awaitable, Callable
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

    SUPPORTED_KINDS = {"code", "issues", "pulls", "commits", "releases", "docs"}

    def __init__(
        self,
        connections: ConnectionStore,
        clock=None,
        requester: RequestJson | None = None,
    ) -> None:
        self.connections = connections
        self.clock = clock or SystemClock()
        self._requester = requester or self._request_json
        self._installation_token: str | None = None
        self._installation_token_expires_at = None
        self._installation_token_connection_id: str | None = None
        self._mint_lock = asyncio.Lock()

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
        address = await resolve_public(target)
        transport = PinnedTransport(target, address)
        async with httpx.AsyncClient(
            transport=transport,
            trust_env=False,
            timeout=30,
            follow_redirects=False,
        ) as client:
            response = await client.request(method, url, headers=headers, json=body)
            response.raise_for_status()
            return response.json()

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
        static_token = secret.get("access_token") or secret.get("token")
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
        if ref and any(kind in {"code", "docs", "issues", "pulls", "releases"} for kind in selected):
            warnings.append("GITHUB_REF_FILTER_PARTIAL")
        headers = self._headers(token)
        retrieved_at = rfc3339(self.clock.utcnow())
        items: list[EvidenceItem] = []
        per_kind = max(1, min(30, max_results))
        for kind in selected:
            if len(items) >= max_results:
                break
            if kind == "releases":
                if not repository:
                    warnings.append("GITHUB_RELEASES_REQUIRE_REPOSITORY")
                    continue
                path = f"/repos/{repository}/releases?per_page={per_kind}"
                payload = await self._requester("GET", path, headers, None)
                rows = [row for row in payload if query.casefold() in json.dumps(row).casefold()]
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
                if ref and kind == "commits":
                    qualifiers.append(ref)
                q = " ".join([query, *qualifiers])
                path = f"/search/{endpoint}?q={urllib.parse.quote(q)}&per_page={per_kind}"
                payload = await self._requester("GET", path, headers, None)
                rows = payload.get("items", [])
            for row in rows:
                items.append(self._item(row, kind, retrieved_at))
                if len(items) >= max_results:
                    break
        return ProviderResult("github-api", items, warnings, len(items))
