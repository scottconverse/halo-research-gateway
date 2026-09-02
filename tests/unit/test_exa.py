from halo_research_gateway.providers.exa import _is_rate_limited, _normalize


def test_exa_quota_notice_is_not_treated_as_search_evidence():
    text = "You've hit Exa's free MCP rate limit. Create your own Exa API key."
    assert _is_rate_limited(text, None)
    assert not _is_rate_limited("Model Context Protocol documentation", {"results": []})


def test_exa_text_blocks_keep_each_claim_with_its_own_source():
    text = "Title: First source\nURL: https://example.com/one\nPublished: 2026-09-01\nHighlights:\nFIRST_ONLY evidence and a reference https://example.org/nested\n\nTitle: Second source\nURL: https://example.net/two\nPublished: N/A\nHighlights:\nSECOND_ONLY evidence"
    items = _normalize(None, text, 5, "2026-09-02T00:00:00Z")
    assert [item.url for item in items] == ["https://example.com/one", "https://example.net/two"]
    assert "FIRST_ONLY" in items[0].snippet and "SECOND_ONLY" not in items[0].snippet
    assert "SECOND_ONLY" in items[1].snippet and "FIRST_ONLY" not in items[1].snippet
    assert items[1].title == "Second source"


def test_unstructured_exa_links_never_borrow_surrounding_claims():
    items = _normalize(
        None, "Unattributed claim https://example.com/one https://example.net/two", 5, "2026-09-02T00:00:00Z"
    )
    assert len(items) == 2
    assert all(item.snippet is None for item in items)
