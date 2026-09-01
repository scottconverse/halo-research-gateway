from urllib.parse import urldefrag

import pytest

from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.service import HaloService


def make_service(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return HaloService(config)


class FakeSearch:
    def __init__(self, items=None, error=None):
        self.items = items or []
        self.error = error
        self.calls = []

    async def search(self, query, **values):
        self.calls.append((query, values))
        if self.error:
            raise self.error
        return ProviderResult("fixture-search", self.items, ["SEARCH_PARTIAL"], len(self.items))


def page(url, content, links=(), warnings=()):
    return ProviderResult(
        "fixture-http",
        [
            EvidenceItem(
                url=url,
                retrieved_at="2026-09-01T00:00:00Z",
                source=url.split("/", 3)[2],
                content=content,
                metadata={"links": list(links)},
            )
        ],
        list(warnings),
        1,
    )


@pytest.mark.asyncio
async def test_deep_research_honors_filters_depth_pages_and_seed_urls(tmp_path):
    service = make_service(tmp_path)
    service.ddgs = FakeSearch(
        [
            EvidenceItem(url="https://allowed.example/search", retrieved_at="2026-09-01T00:00:00Z"),
            EvidenceItem(url="https://excluded.allowed.example/no", retrieved_at="2026-09-01T00:00:00Z"),
            EvidenceItem(url="https://other.example/no", retrieved_at="2026-09-01T00:00:00Z"),
        ]
    )
    pages = {
        "https://allowed.example/root": page(
            "https://allowed.example/root",
            "root evidence with enough distinct words for a useful source",
            [("child", "/child"), ("same", "/root#section"), ("cross", "https://other.example/cross")],
        ),
        "https://allowed.example/search": page(
            "https://allowed.example/search", "search evidence with a separate set of useful facts"
        ),
        "https://allowed.example/child": page(
            "https://allowed.example/child",
            "child evidence is reached at depth one and retained",
            [("too deep", "/grandchild")],
        ),
        "https://allowed.example/grandchild": page(
            "https://allowed.example/grandchild", "this depth two page must not be fetched"
        ),
    }
    calls = []

    async def fetch(url):
        canonical = urldefrag(url)[0]
        calls.append(canonical)
        return pages[canonical]

    service.http.fetch = fetch
    try:
        result = await service.deep_research(
            "bounded research",
            seed_urls=["https://allowed.example/root#intro"],
            include_domains=["allowed.example"],
            exclude_domains=["excluded.allowed.example"],
            max_sources=10,
            max_pages=3,
            max_depth=1,
            freshness_days=14,
            max_chars=6000,
            client="known-planner",
        )
    finally:
        await service.close()

    assert result["ok"] is True
    assert [item["url"] for item in result["items"]] == [
        "https://allowed.example/root",
        "https://allowed.example/search",
        "https://allowed.example/child",
    ]
    assert calls == [
        "https://allowed.example/root",
        "https://allowed.example/search",
        "https://allowed.example/child",
    ]
    assert service.ddgs.calls == [
        (
            "bounded research",
            {
                "max_results": 10,
                "include_domains": ["allowed.example"],
                "exclude_domains": ["excluded.allowed.example"],
                "freshness_days": 14,
            },
        )
    ]
    assert "CROSS_SITE_LINK_SKIPPED" in result["warnings"]


@pytest.mark.asyncio
async def test_deep_research_deduplicates_canonical_urls_and_near_duplicate_bodies(tmp_path):
    service = make_service(tmp_path)
    service.ddgs = FakeSearch()
    base = " ".join(f"research-word-{number}" for number in range(200))
    pages = {
        "https://same.example/root": page("https://same.example/root", base),
        "https://same.example/alias": page("https://same.example/alias", base + " tiny-change"),
        "https://same.example/unique": page(
            "https://same.example/unique", "completely different evidence about an independent subject " * 8
        ),
    }
    calls = []

    async def fetch(url):
        canonical = urldefrag(url)[0]
        calls.append(canonical)
        return pages[canonical]

    service.http.fetch = fetch
    try:
        result = await service.deep_research(
            "deduplicate",
            seed_urls=[
                "https://same.example/root",
                "https://same.example/root#duplicate",
                "https://same.example/alias",
                "https://same.example/unique",
            ],
            max_sources=2,
            max_pages=3,
            max_depth=0,
            max_chars=6000,
        )
    finally:
        await service.close()

    assert [item["url"] for item in result["items"]] == [
        "https://same.example/root",
        "https://same.example/unique",
    ]
    assert calls == [
        "https://same.example/root",
        "https://same.example/alias",
        "https://same.example/unique",
    ]
    assert "DUPLICATE_CONTENT_SKIPPED" in result["warnings"]


@pytest.mark.asyncio
async def test_deep_research_preserves_partial_failures_and_reuses_cached_packet(tmp_path):
    service = make_service(tmp_path)
    service.ddgs = FakeSearch(error=RuntimeError("search unavailable"))
    root = page(
        "https://partial.example/root",
        "root evidence survives a search outage and child failure",
        [("bad", "/bad"), ("good", "/good"), ("cross", "https://elsewhere.example/no")],
        ["SOURCE_PARTIAL"],
    )
    good = page("https://partial.example/good", "good child evidence remains available")
    calls = []

    async def fetch(url):
        calls.append(url)
        if url.endswith("/bad"):
            raise RuntimeError("fixture fetch failed")
        return root if url.endswith("/root") else good

    service.http.fetch = fetch
    arguments = {
        "question": "partial packet",
        "seed_urls": ["https://partial.example/root"],
        "max_sources": 3,
        "max_pages": 3,
        "max_depth": 1,
        "max_chars": 6000,
        "client": "known-planner",
    }
    try:
        first = await service.deep_research(**arguments)
        second = await service.deep_research(**arguments)
    finally:
        await service.close()

    assert first["ok"] is True
    assert [item["url"] for item in first["items"]] == [
        "https://partial.example/root",
        "https://partial.example/good",
    ]
    assert {"SEARCH_UNAVAILABLE", "UPSTREAM_UNAVAILABLE", "SOURCE_PARTIAL"} <= set(first["warnings"])
    assert second["cache"]["hit"] is True
    assert calls == [
        "https://partial.example/root",
        "https://partial.example/bad",
        "https://partial.example/good",
    ]
