"""Anonymous Reddit RSS discovery and thread retrieval."""

from __future__ import annotations

import re
import urllib.parse
from html import unescape

from defusedxml import ElementTree

from ..clock import SystemClock, rfc3339
from ..models import EvidenceItem, ProviderResult
from .html import extract_html

ATOM = "{http://www.w3.org/2005/Atom}"


def _rss_text(value: str | None) -> str:
    if not value:
        return ""
    _, text, _ = extract_html(unescape(value))
    return re.sub(r"\s+", " ", text).strip()


def parse_atom(payload: bytes, *, limit: int, clock=None) -> ProviderResult:
    clock = clock or SystemClock()
    root = ElementTree.fromstring(payload)
    items: list[EvidenceItem] = []
    for entry in root.findall(f"{ATOM}entry")[:limit]:
        link = entry.find(f"{ATOM}link")
        content = entry.find(f"{ATOM}content")
        author = entry.find(f"{ATOM}author/{ATOM}name")
        updated = entry.findtext(f"{ATOM}updated")
        url = link.get("href") if link is not None else ""
        if not url:
            continue
        items.append(
            EvidenceItem(
                title=_rss_text(entry.findtext(f"{ATOM}title")) or None,
                url=url,
                published_at=updated,
                retrieved_at=rfc3339(clock.utcnow()),
                source="reddit.com",
                content=_rss_text(content.text if content is not None else None),
                metadata={"author": author.text if author is not None else None},
            )
        )
    return ProviderResult("reddit-rss", items, [], len(items))


def search_url(query: str, subreddit: str | None, sort: str, time_filter: str) -> str:
    params = {"q": query, "sort": sort, "t": time_filter}
    if subreddit:
        if not re.fullmatch(r"[A-Za-z0-9_]+", subreddit):
            raise ValueError("INVALID_ARGUMENT")
        params["restrict_sr"] = "on"
        base = f"https://www.reddit.com/r/{subreddit}/search.rss"
    else:
        base = "https://www.reddit.com/search.rss"
    return f"{base}?{urllib.parse.urlencode(params)}"


def thread_rss_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {"reddit.com", "www.reddit.com"}:
        raise ValueError("INVALID_ARGUMENT")
    path = parsed.path.rstrip("/")
    if "/comments/" not in path:
        raise ValueError("INVALID_ARGUMENT")
    return urllib.parse.urlunsplit(("https", "www.reddit.com", path + "/.rss", "", ""))
