# Live source acceptance and search repairs — 2026-09-02

The first live matrix exercised the running removal checkpoint (before these search/GitHub changes were reloaded). It exposed an actual Exa attribution defect: unstructured results attached the first excerpt to each discovered URL. It also exposed silently ignored domain/freshness/content-type controls.

Existing live baseline command: `uv run --locked python tests/acceptance/live_provider_canary.py`.

```text
{'search': {'provider': 'exa-anonymous', 'items': 3}, 'crawl': {'provider': 'crawl4ai', 'items': 1}, 'document': {'provider': 'pymupdf', 'items': 1}, 'reddit': {'ok': True, 'provider': 'reddit-rss', 'items': 2}}
```

Expanded live command: `uv run --locked python tests/acceptance/research_matrix.py` (preceded by ruff format).
Search/cursor, official Python pages/cursor, W3C PDF, Reddit discovery, Hacker News search/thread and the first deep-research envelope returned evidence. These checks do not prove complete multi-source synthesis. Three cases failed:

```text
JavaScript rendered evidence: UPSTREAM_UNAVAILABLE / RuntimeError: operation did not complete
public captioned media: UPSTREAM_UNAVAILABLE / HTTPStatusError: operation did not complete
Reddit thread: UPSTREAM_UNAVAILABLE / HTTPStatusError: operation did not complete
{"matrix_failures": ["JavaScript rendered evidence", "public captioned media", "Reddit thread"], "passed": false}
```

The test sent `css:.quote` where this Gateway expects the CSS selector alone; changed to `.quote`. Its assumed MDN demo URL returned HTTP404; replaced with the verified HTTP200 original author's demo containing English/German/Spanish track elements: https://iandevlin.github.io/mdn/video-player-with-captions/ . These two failures were acceptance-input mistakes, not demonstrated production defects. Reddit's same thread RSS URL later returned HTTP200 through a direct diagnostic client; intermittent provider behavior remains to verify through the Gateway.

## Search TDD

Baseline command: `uv run --locked python -m pytest -q tests/unit/test_exa.py tests/unit/test_retrieval_regressions.py`.

```text
.......                                                                  [100%]
7 passed in 0.88s
```

RED: same command after adding source-attribution and search-control regressions.

```text
.FF.FFF.....                                                             [100%]
================================== FAILURES ===================================
__________ test_exa_text_blocks_keep_each_claim_with_its_own_source ___________

    def test_exa_text_blocks_keep_each_claim_with_its_own_source():
        text = "Title: First source\nURL: https://example.com/one\nPublished: 2026-09-01\nHighlights:\nFIRST_ONLY evidence and a reference https://example.org/nested\n\nTitle: Second source\nURL: https://example.net/two\nPublished: N/A\nHighlights:\nSECOND_ONLY evidence"
        items = _normalize(None, text, 5, "2026-09-02T00:00:00Z")
>       assert [item.url for item in items] == ["https://example.com/one", "https://example.net/two"]
E       AssertionError: assert ['https://exa...mple.net/two'] == ['https://exa...mple.net/two']
E         
E         At index 1 diff: 'https://example.org/nested' != 'https://example.net/two'
E         Left contains one more item: 'https://example.net/two'
E         Use -v to get more diff

tests\unit\test_exa.py:13: AssertionError
_________ test_unstructured_exa_links_never_borrow_surrounding_claims _________

    def test_unstructured_exa_links_never_borrow_surrounding_claims():
        items = _normalize(None, "Unattributed claim https://example.com/one https://example.net/two", 5, "2026-09-02T00:00:00Z")
        assert len(items) == 2
>       assert all(item.snippet is None for item in items)
E       assert False
E        +  where False = all(<generator object test_unstructured_exa_links_never_borrow_surrounding_claims.<locals>.<genexpr> at 0x00000202C07897D0>)

tests\unit\test_exa.py:22: AssertionError
____________ test_search_filters_exa_sources_by_requested_domains _____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1849/test_search_filters_exa_source0')

    @pytest.mark.asyncio
    async def test_search_filters_exa_sources_by_requested_domains(tmp_path):
        service = service_at(tmp_path)
    
        async def search(query, max_results):
            return ProviderResult("exa-anonymous", [EvidenceItem(url=url, retrieved_at="2026-09-02T00:00:00Z", snippet="evidence") for url in ["https://outside.org/", "https://docs.example.com/", "https://private.example.com/"]])
    
        service.exa.search = search
        try:
            result = await service.web_search("test", include_domains=["example.com"], exclude_domains=["private.example.com"])
>           assert [item["url"] for item in result["items"]] == ["https://docs.example.com/"]
E           AssertionError: assert ['https://out...example.com/'] == ['https://docs.example.com/']
E             
E             At index 0 diff: 'https://outside.org/' != 'https://docs.example.com/'
E             Left contains 2 more items, first extra item: 'https://docs.example.com/'
E             Use -v to get more diff

tests\unit\test_retrieval_regressions.py:62: AssertionError
_____ test_search_routes_controls_to_provider_that_accepts_them[options0] _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1849/test_search_routes_controls_to0')
options = {'content_type': 'news'}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("options", [{"content_type": "news"}, {"freshness_days": 7}])
    async def test_search_routes_controls_to_provider_that_accepts_them(tmp_path, options):
        service = service_at(tmp_path)
        calls = []
    
        async def exa(*args):
            calls.append("unfiltered-exa")
            return ProviderResult("exa-anonymous", [EvidenceItem(url="https://example.com/stale", retrieved_at="2026-09-02T00:00:00Z")])
    
        async def ddgs(query, **kwargs):
            calls.append(kwargs)
            return ProviderResult("ddgs-accountless", [EvidenceItem(url="https://example.com/current", retrieved_at="2026-09-02T00:00:00Z")])
    
        service.exa.search, service.ddgs.search = exa, ddgs
        try:
            result = await service.web_search("test", **options)
>           assert result["provider"] == "ddgs-accountless"
E           AssertionError: assert 'exa-anonymous' == 'ddgs-accountless'
E             
E             - ddgs-accountless
E             + exa-anonymous

tests\unit\test_retrieval_regressions.py:84: AssertionError
_____ test_search_routes_controls_to_provider_that_accepts_them[options1] _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1849/test_search_routes_controls_to1')
options = {'freshness_days': 7}

    @pytest.mark.asyncio
    @pytest.mark.parametrize("options", [{"content_type": "news"}, {"freshness_days": 7}])
    async def test_search_routes_controls_to_provider_that_accepts_them(tmp_path, options):
        service = service_at(tmp_path)
        calls = []
    
        async def exa(*args):
            calls.append("unfiltered-exa")
            return ProviderResult("exa-anonymous", [EvidenceItem(url="https://example.com/stale", retrieved_at="2026-09-02T00:00:00Z")])
    
        async def ddgs(query, **kwargs):
            calls.append(kwargs)
            return ProviderResult("ddgs-accountless", [EvidenceItem(url="https://example.com/current", retrieved_at="2026-09-02T00:00:00Z")])
    
        service.exa.search, service.ddgs.search = exa, ddgs
        try:
            result = await service.web_search("test", **options)
>           assert result["provider"] == "ddgs-accountless"
E           AssertionError: assert 'exa-anonymous' == 'ddgs-accountless'
E             
E             - ddgs-accountless
E             + exa-anonymous

tests\unit\test_retrieval_regressions.py:84: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_exa.py::test_exa_text_blocks_keep_each_claim_with_its_own_source
FAILED tests/unit/test_exa.py::test_unstructured_exa_links_never_borrow_surrounding_claims
FAILED tests/unit/test_retrieval_regressions.py::test_search_filters_exa_sources_by_requested_domains
FAILED tests/unit/test_retrieval_regressions.py::test_search_routes_controls_to_provider_that_accepts_them[options0]
FAILED tests/unit/test_retrieval_regressions.py::test_search_routes_controls_to_provider_that_accepts_them[options1]
5 failed, 7 passed in 1.30s

```

GREEN commands:

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/exa.py src/halo_research_gateway/service.py tests/unit/test_exa.py tests/unit/test_retrieval_regressions.py
uv run --locked python -m pytest -q tests/unit/test_exa.py tests/unit/test_retrieval_regressions.py
```

```text
4 files reformatted
............                                                             [100%]
12 passed in 1.36s
```

Files read before editing: Exa adapter, service search path and imports, deep domain helper, existing Exa/retrieval tests, manual/changelog, acceptance matrix. No dependency or external write added. Falsification includes a link embedded inside another source's excerpt, unlabelled text with multiple links, overlapping include/exclude domains, non-web and freshness routing. Model/DSH permissions unchanged. Whole-repository gate and corrected live matrix results are recorded separately below.

