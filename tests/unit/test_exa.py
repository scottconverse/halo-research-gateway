from halo_research_gateway.providers.exa import _is_rate_limited


def test_exa_quota_notice_is_not_treated_as_search_evidence():
    text = "You've hit Exa's free MCP rate limit. Create your own Exa API key."
    assert _is_rate_limited(text, None)
    assert not _is_rate_limited("Model Context Protocol documentation", {"results": []})
