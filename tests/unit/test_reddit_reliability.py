import httpx
import pytest

from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.service import HaloService

ATOM = b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Research</title><link href="https://www.reddit.com/r/test/comments/abc/topic/"/><content type="html">Evidence</content></entry></feed>'


def service_at(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return HaloService(config)


@pytest.mark.asyncio
async def test_rss_uses_shared_bounded_download_and_atom_accept(tmp_path, monkeypatch):
    service = service_at(tmp_path)
    calls = []

    async def download(url, accept=None):
        calls.append((url, accept))
        return url, None, {}, ATOM

    async def resolve(target):
        return "8.8.8.8"

    monkeypatch.setattr("halo_research_gateway.service.resolve_public", resolve, raising=False)
    monkeypatch.setattr(
        "halo_research_gateway.service.PinnedTransport",
        lambda *_: httpx.MockTransport(lambda req: httpx.Response(200, content=ATOM)),
        raising=False,
    )
    service.http.download = download
    try:
        result = await service._rss("https://www.reddit.com/search.rss?q=research", 2)
        assert len(result.items) == 1
        assert calls == [("https://www.reddit.com/search.rss?q=research", "application/atom+xml,application/rss+xml")]
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_reddit_429_reports_retry_and_backs_off_before_circuit_threshold(tmp_path, monkeypatch):
    service = service_at(tmp_path)

    def response(request):
        return httpx.Response(429, headers={"Retry-After": "120"}, request=request)

    async def resolve(target):
        return "8.8.8.8"

    async def download(url, accept=None):
        response(httpx.Request("GET", url)).raise_for_status()

    monkeypatch.setattr("halo_research_gateway.service.resolve_public", resolve, raising=False)
    monkeypatch.setattr(
        "halo_research_gateway.service.PinnedTransport", lambda *_: httpx.MockTransport(response), raising=False
    )
    service.http.download = download
    try:
        result = await service.reddit_thread("https://www.reddit.com/r/test/comments/abc/topic/")
        assert result["error"]["code"] == "RATE_LIMITED"
        assert result["retry_after_seconds"] == 120
        assert service.rate.status()["reddit-anonymous"]["circuit"] == "open"
        repeated = await service.reddit_thread("https://www.reddit.com/r/test/comments/abc/topic/")
        assert repeated["error"]["code"] == "PROVIDER_CIRCUIT_OPEN"
        assert repeated["retry_after_seconds"] > 0
    finally:
        await service.close()
