"""Recorded retrieval failures: reproduce before changing their behavior."""

import pytest

from halo_research_gateway.config import GatewayConfig, LocalTargetConfig
from halo_research_gateway.models import EvidenceItem, LocalTarget, ProviderResult
from halo_research_gateway.service import HaloService


def service_at(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return HaloService(config)


@pytest.mark.asyncio
async def test_github_public_fallback_continues_with_its_own_cursor(tmp_path):
    service = service_at(tmp_path)
    calls = 0

    async def search(query, max_results):
        nonlocal calls
        calls += 1
        return ProviderResult(
            "exa",
            [
                EvidenceItem(
                    url="https://github.com/acme/widget/blob/main/README.md",
                    retrieved_at="2026-09-02T00:00:00Z",
                    content="source evidence " * 900,
                )
            ],
        )

    service.exa.search = search
    try:
        first = await service.github_research("widget", max_chars=2000)
        assert first["page"]["next_cursor"]
        second = await service.github_research("", cursor=first["page"]["next_cursor"])
        assert second["ok"], second
        assert second["tool"] == "github_research"
        assert second["provider"] == "github-public-discovery"
        assert second["page"]["number"] == 2
        assert "GITHUB_AUTH_NOT_CONFIGURED" in second["warnings"]
        assert calls == 1
    finally:
        await service.close()


@pytest.mark.parametrize(
    "path", ["/research/../admin", "/research/%2e%2e/admin", "/research/%252e%252e/admin", "/research/..\\admin"]
)
def test_local_target_path_cannot_escape_its_prefix(path):
    target = LocalTarget("fixture", "http", "127.0.0.1", 3090, ("/research",), browser_allowed=True)
    with pytest.raises(ValueError):
        target.build_url(path)


@pytest.mark.asyncio
async def test_service_passes_exact_target_to_local_browser(tmp_path):
    service = service_at(tmp_path)
    service.config.local_targets["fixture"] = LocalTargetConfig(
        scheme="http",
        host="127.0.0.1",
        port=3090,
        path_prefixes=["/research"],
        browser_allowed=True,
    )
    captured = {}

    async def crawl(url, **kwargs):
        captured.update(kwargs)
        return ProviderResult(
            "fixture", [EvidenceItem(url=url, retrieved_at="2026-09-02T00:00:00Z", content="fixture")]
        )

    service.crawler.crawl = crawl
    try:
        result = await service.local_crawl("fixture", "/research/page")
        assert result["ok"], result
        assert "local_target" in captured
        assert captured["local_target"].host == "127.0.0.1"
        assert captured["local_target"].path_prefixes == ("/research",)
    finally:
        await service.close()
