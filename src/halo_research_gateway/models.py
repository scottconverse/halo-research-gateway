"""Stable internal models shared by providers and MCP tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import unquote, urlsplit

MaxChars = Literal[2000, 4000, 6000]


@dataclass(slots=True)
class EvidenceItem:
    url: str
    retrieved_at: str
    title: str | None = None
    published_at: str | None = None
    source: str | None = None
    snippet: str | None = None
    content: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        result = {
            "title": self.title,
            "url": self.url,
            "published_at": self.published_at,
            "retrieved_at": self.retrieved_at,
            "source": self.source,
            "snippet": self.snippet,
            "content": self.content,
        }
        if self.metadata:
            result["metadata"] = self.metadata
        return result


@dataclass(slots=True)
class ProviderResult:
    provider: str
    items: list[EvidenceItem]
    warnings: list[str] = field(default_factory=list)
    available: int | None = None
    cache_hit: bool = False
    cache_age_seconds: int = 0
    cache_key: str = ""


@dataclass(frozen=True, slots=True)
class LocalTarget:
    target_id: str
    scheme: Literal["http", "https"]
    host: str
    port: int
    path_prefixes: tuple[str, ...]
    methods: tuple[str, ...] = ("GET", "HEAD")
    browser_allowed: bool = False
    cache_authenticated: bool = False

    def build_url(self, path: str) -> str:
        self._validate_path(path)
        host = f"[{self.host}]" if ":" in self.host else self.host
        return f"{self.scheme}://{host}:{self.port}{path}"

    def _validate_path(self, path: str) -> None:
        decoded = path.split("?", 1)[0].split("#", 1)[0]
        for _ in range(8):
            next_value = unquote(decoded)
            if next_value == decoded:
                break
            decoded = next_value
        else:
            raise ValueError("LOCAL_TARGET_NOT_ALLOWED")
        if (
            not decoded.startswith("/")
            or decoded.startswith("//")
            or "\\" in decoded
            or any(ord(char) < 32 for char in decoded)
            or any(part in {".", ".."} for part in decoded.split("/"))
            or not any(
                decoded == prefix or decoded.startswith(prefix.rstrip("/") + "/") for prefix in self.path_prefixes
            )
        ):
            raise ValueError("LOCAL_TARGET_NOT_ALLOWED")

    def validate_request(self, url: str, method: str = "GET") -> None:
        parsed = urlsplit(url)
        scheme = {"ws": "http", "wss": "https"}.get(parsed.scheme, parsed.scheme)
        if (
            not self.browser_allowed
            or scheme != self.scheme
            or parsed.hostname != self.host.lower()
            or (parsed.port or (443 if scheme == "https" else 80)) != self.port
            or parsed.username is not None
            or parsed.password is not None
            or method.upper() not in self.methods
        ):
            raise ValueError("LOCAL_TARGET_NOT_ALLOWED")
        self._validate_path(parsed.path or "/")
