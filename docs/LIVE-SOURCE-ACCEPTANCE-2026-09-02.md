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
## Corrected live MCP run after controlled reload

Source d9bb096 was loaded via the existing scheduled task. The first wrapper stopped the Gateway successfully but misread a stale PowerShell LASTEXITCODE and aborted before start; an immediate separate Start-ScheduledTask restored health. New Gateway start time: 2026-09-02T22:28:13.274541Z. DSH settings were not changed.

Command: `uv run --locked python tests/acceptance/research_matrix.py`.

```text
{"case": "source discovery", "passed": true, "tool": "web_search", "provider": "exa-anonymous", "items": 1, "urls": ["https://github.com/python/cpython/blob/main/Lib/asyncio/taskgroups.py"], "text_sample": "class TaskGroup:\n \"\"\"Asynchronous context manager for managing groups of tasks.\n\n Example use:\n\n async with asyncio.TaskGroup() as group:\n task1 = group.create_task(some_coroutine(...))\n task2 = group.create_task(other_coroutine(...))\n prin", "warnings": ["RESULT_TRUNCATED"], "error": null, "has_more": true}
{"case": "search continuation", "passed": true, "tool": "web_search", "provider": "exa-anonymous", "items": 1, "urls": ["https://docs.python.org/release/3.12.1/library/asyncio-task.html"], "text_sample": "The`asyncio.TaskGroup` class provides a more modern alternative to`create_task()`. Using this API, the last example becomes:\n...\nNew in version 3.11:`asyncio.TaskGroup`.\n...\n## Task Cancellation\u00b6\n...\nTasks can easily and safely be cancelled", "warnings": ["RESULT_TRUNCATED"], "error": null, "has_more": true}
{"case": "ordinary official source", "passed": true, "tool": "web_fetch", "provider": "direct-http", "items": 1, "urls": ["https://docs.python.org/3/library/asyncio-task.html"], "text_sample": "Coroutines and tasks \u2014 Python 3.14.7 documentation\n\n Theme\n\n Auto\n Light\n Dark\n\nTable of Contents\n\nCoroutines and tasks\n\nCoroutines\n\nAwaitables\n\nCreating tasks\n\nTask cancellation\n\nTask groups\n\nTerminating a task group\n\nSleeping\n\nRunning tas", "warnings": ["RESULT_TRUNCATED"], "error": null, "has_more": true}
{"case": "source continuation", "passed": true, "tool": "web_fetch", "provider": "direct-http", "items": 1, "urls": ["https://docs.python.org/3/library/asyncio-task.html"], "text_sample": "ently\n\nEager task factory\n\nShielding from cancellation\n\nTimeouts\n\nWaiting primitives\n\nRunning in threads\n\nScheduling from other threads\n\nIntrospection\n\nTask object\n\nPrevious topic\n\nRunners\n\nNext topic\n\nStreams\n\nThis page\n\nReport a bug\n\nImpr", "warnings": ["RESULT_TRUNCATED"], "error": null, "has_more": true}
{"case": "second official source", "passed": true, "tool": "web_fetch", "provider": "direct-http", "items": 1, "urls": ["https://docs.python.org/3/library/asyncio-exceptions.html"], "text_sample": "Exceptions \u2014 Python 3.14.7 documentation\n\n Theme\n\n Auto\n Light\n Dark\n\nPrevious topic\n\nQueues\n\nNext topic\n\nCall graph introspection\n\nThis page\n\nReport a bug\n\nImprove this page\n\n Show source\n\nNavigation\n\n index\n\n modules |\n\n next |\n\n previous", "warnings": ["RESULT_TRUNCATED"], "error": null, "has_more": true}
{"case": "JavaScript rendered evidence", "passed": true, "tool": "web_crawl", "provider": "crawl4ai", "items": 1, "urls": ["https://quotes.toscrape.com/js/"], "text_sample": "#  [Quotes to Scrape](https://quotes.toscrape.com/)\n[Login](https://quotes.toscrape.com/login)\n\u201cThe world as we have created it is a process of our thinking. It cannot be changed without changing our thinking.\u201dby Albert Einstein\nTags: chang", "warnings": [], "error": null, "has_more": false}
{"case": "PDF text", "passed": true, "tool": "document_extract", "provider": "pymupdf", "items": 1, "urls": ["https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf#page=1"], "text_sample": "Dummy PDF file\n", "warnings": [], "error": null, "has_more": false}
{"case": "public captioned media", "passed": true, "tool": "transcript_fetch", "provider": "public-transcript", "items": 1, "urls": ["https://iandevlin.github.io/mdn/video-player-with-captions/"], "text_sample": "[00:00.000 --> 00:12.000] [Test]\n[00:18.700 --> 00:21.500] This blade has a dark past.\n[00:22.800 --> 00:26.800] It has shed much innocent blood.\n[00:29.000 --> 00:32.450] You're a fool for traveling alone, so completely unprepared.\n[00:32.", "warnings": [], "error": null, "has_more": false}
{"case": "Reddit discovery", "passed": true, "tool": "reddit_search", "provider": "reddit-rss", "items": 2, "urls": ["https://www.reddit.com/r/LocalLLaMA/comments/1vkqnyh/whats_practical_to_run_on_strix_halo/", "https://www.reddit.com/r/LocalLLaMA/comments/1vqme4y/qwen3827b_q8_0_on_strix_halo_is_seriously/"], "text_sample": "I'm looking through some Strix Halo devices, and things like TUF 14 can have more storage than a 2230 single SSD ProArt or Z13. It caps at 64GB RAM and is way cheaper. My question is what's practical to run on it - >60\"GB\" models would fit ", "warnings": [], "error": null, "has_more": false}
{"case": "Reddit thread", "passed": false, "tool": "reddit_thread", "provider": "reddit-rss", "items": 0, "urls": [], "text_sample": "", "warnings": null, "error": {"code": "UPSTREAM_UNAVAILABLE", "message": "HTTPStatusError: operation did not complete"}, "has_more": false}
{"case": "Hacker News discovery", "passed": true, "tool": "community_search", "provider": "community-public", "items": 2, "urls": ["https://news.ycombinator.com/item?id=27016630", "https://news.ycombinator.com/item?id=31318708"], "text_sample": "\n", "warnings": ["COMMUNITY_EVIDENCE_NOT_FACT", "HACKERNEWS_SEARCH_USES_PUBLIC_ALGOLIA_INDEX"], "error": null, "has_more": false}
{"case": "Hacker News discussion", "passed": true, "tool": "community_thread", "provider": "hackernews-public-api", "items": 4, "urls": ["https://news.ycombinator.com/item?id=27016630", "https://news.ycombinator.com/item?id=27016787", "https://news.ycombinator.com/item?id=27017653", "https://news.ycombinator.com/item?id=27017679"], "text_sample": "\nTL;DR: Compile SQLite to JS with emscripten, implement a virtual fs in JS to stream chunks of a statically hosted (readonly) SQL database. If queries make use of indices, only a fraction of the database needs to be downloaded. Also, you ca", "warnings": ["COMMUNITY_EVIDENCE_NOT_FACT", "HACKERNEWS_THREAD_USES_PUBLIC_ALGOLIA_INDEX", "REPLY_LIMIT_REACHED", "RESULT_TRUNCATED"], "error": null, "has_more": true}
{"case": "multi-source research", "passed": true, "tool": "deep_research", "provider": "halo-deep", "items": 1, "urls": ["https://docs.python.org/3/library/asyncio-task.html"], "text_sample": "Coroutines and tasks \u2014 Python 3.14.7 documentation\n\n Theme\n\n Auto\n Light\n Dark\n\nTable of Contents\n\nCoroutines and tasks\n\nCoroutines\n\nAwaitables\n\nCreating tasks\n\nTask cancellation\n\nTask groups\n\nTerminating a task group\n\nSleeping\n\nRunning tas", "warnings": ["DEPTH_LIMIT_REACHED", "DUPLICATE_URL_SKIPPED", "PROVIDER_FALLBACK_USED", "RESULT_TRUNCATED"], "error": null, "has_more": true}
{"matrix_failures": ["Reddit thread"], "passed": false}

```

Remaining failure was Reddit HTTP429, confirmed by a same-transport diagnostic. Successful JavaScript/caption cases now use valid inputs. This is live MCP evidence, not a complete DSH workflow. See [RSS and session fixes](SESSION-RSS-EVIDENCE-2026-09-02.md).

