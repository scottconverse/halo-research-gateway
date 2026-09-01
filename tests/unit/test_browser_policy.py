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
    await Crawl4AIProvider._validate_browser_request("http://127.0.0.1:3090/", False)
