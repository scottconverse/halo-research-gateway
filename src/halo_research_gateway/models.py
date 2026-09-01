"""Stable internal models shared by providers and MCP tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

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
        if not path.startswith("/") or not any(
            path == prefix or path.startswith(prefix.rstrip("/") + "/") for prefix in self.path_prefixes
        ):
            raise ValueError("LOCAL_TARGET_NOT_ALLOWED")
        return f"{self.scheme}://{self.host}:{self.port}{path}"
