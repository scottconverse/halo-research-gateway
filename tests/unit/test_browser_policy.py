import pytest

from halo_research_gateway.providers.crawl4ai_provider import Crawl4AIProvider
from halo_research_gateway.security import UrlPolicyError


@pytest.mark.asyncio
async def test_browser_request_policy_blocks_private_and_allows_in_document_resources():
    with pytest.raises(UrlPolicyError):
        await Crawl4AIProvider._validate_browser_request("http://127.0.0.1/private", True)
    await Crawl4AIProvider._validate_browser_request("data:text/plain,hello", True)
    await Crawl4AIProvider._validate_browser_request("blob:https://example.com/id", True)


@pytest.mark.asyncio
async def test_local_crawl_uses_separate_operator_policy():
    with pytest.raises(ValueError, match="LOCAL_TARGET_REQUIRED"):
        await Crawl4AIProvider._validate_browser_request("http://127.0.0.1:3090/", False)


class FakeWebSocket:
    def __init__(self, url):
        self.url = url
        self.connected = False
        self.closed = None

    def connect_to_server(self):
        self.connected = True

    async def close(self, **values):
        self.closed = values


@pytest.mark.asyncio
async def test_public_websocket_to_loopback_is_blocked_before_connection():
    websocket = FakeWebSocket("ws://127.0.0.1/private")
    await Crawl4AIProvider._handle_websocket(websocket, True)
    assert websocket.connected is False
    assert websocket.closed == {"code": 1008, "reason": "Blocked by Halo egress policy"}


@pytest.mark.asyncio
async def test_operator_defined_local_websocket_mode_can_connect():
    from halo_research_gateway.models import LocalTarget

    websocket = FakeWebSocket("ws://127.0.0.1:3090/socket")
    target = LocalTarget("fixture", "http", "127.0.0.1", 3090, ("/socket",), browser_allowed=True)
    await Crawl4AIProvider._handle_websocket(websocket, False, target)
    assert websocket.connected is True
    assert websocket.closed is None


def test_managed_profile_is_gateway_owned_and_traversal_safe(tmp_path):
    profile = tmp_path / "profiles" / "scott-copy"
    profile.mkdir(parents=True)
    provider = Crawl4AIProvider(str(tmp_path))
    assert provider._profile_directory("scott-copy") == profile.resolve()
    with pytest.raises(ValueError, match="PROFILE_INVALID"):
        provider._profile_directory("../Default")
    with pytest.raises(ValueError, match="PROFILE_NOT_FOUND"):
        provider._profile_directory("missing")
