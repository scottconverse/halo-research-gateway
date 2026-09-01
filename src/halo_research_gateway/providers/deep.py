"""Pure URL and content-deduplication helpers for bounded deep research."""

from __future__ import annotations

import hashlib
import re
import urllib.parse


def canonical_url(url: str, base_url: str | None = None) -> str | None:
    """Return a fragment-free public HTTP(S) URL suitable for frontier identity."""
    try:
        joined = urllib.parse.urljoin(base_url, url) if base_url else url
        parsed = urllib.parse.urlsplit(joined)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            return None
        if parsed.username is not None or parsed.password is not None:
            return None
        scheme = parsed.scheme.lower()
        host = parsed.hostname.rstrip(".").lower()
        port = parsed.port
        rendered_host = f"[{host}]" if ":" in host else host
        netloc = (
            rendered_host
            if port is None or (scheme, port) in {("http", 80), ("https", 443)}
            else f"{rendered_host}:{port}"
        )
        return urllib.parse.urlunsplit((scheme, netloc, parsed.path or "/", parsed.query, ""))
    except (TypeError, ValueError, UnicodeError):
        return None


def url_host(url: str) -> str | None:
    try:
        return urllib.parse.urlsplit(url).hostname
    except ValueError:
        return None


def domain_allowed(url: str, include_domains: list[str] | None, exclude_domains: list[str] | None) -> bool:
    host = (url_host(url) or "").rstrip(".").lower()

    def normalized(values):
        return [value.strip().rstrip(".").lower() for value in (values or []) if value.strip()]

    def matches(domain: str) -> bool:
        return host == domain or host.endswith("." + domain)

    included = normalized(include_domains)
    excluded = normalized(exclude_domains)
    return (not included or any(matches(domain) for domain in included)) and not any(
        matches(domain) for domain in excluded
    )


class BodyDeduplicator:
    """Bounded exact and near-duplicate detection using normalized word shingles."""

    def __init__(self, threshold: float = 0.9) -> None:
        self.threshold = threshold
        self._signatures: list[tuple[bytes, frozenset[bytes]]] = []

    @staticmethod
    def _signature(content: str) -> tuple[bytes, frozenset[bytes]] | None:
        words = re.findall(r"\w+", content.casefold())[:5000]
        if not words:
            return None
        normalized = " ".join(words).encode("utf-8")
        width = min(5, len(words))
        shingles = frozenset(
            hashlib.blake2b("\x1f".join(words[index : index + width]).encode("utf-8"), digest_size=8).digest()
            for index in range(len(words) - width + 1)
        )
        return hashlib.sha256(normalized).digest(), shingles

    def duplicate(self, content: str) -> bool:
        signature = self._signature(content)
        if signature is None:
            return False
        digest, shingles = signature
        for prior_digest, prior_shingles in self._signatures:
            if digest == prior_digest:
                return True
            union = len(shingles | prior_shingles)
            if union and len(shingles & prior_shingles) / union >= self.threshold:
                return True
        self._signatures.append(signature)
        return False
