# Transcript metadata paging evidence — 2026-09-02

## Outcome and scope

Fixes the real short-transcript OUTPUT_ITEM_TOO_LARGE failure at max_chars=2000 and repeated caption metadata on later pages. Common envelope paging now treats snippet, body and retained caption-segment text as one logical stream. Partial captions preserve timestamps and explicit segment/text offsets. Empty timing records advance one cursor unit. Caption items bypass pre-chunking that previously replicated the whole metadata array. Ordinary non-caption text paging remains unchanged.

Cursor layout 3 replaces layout 2; older cursors return CURSOR_EVICTED rather than silently referring to changed item/offset positions. Start a new original request after the upgrade. Immutable cached evidence and existing durable jobs/data are not erased. Product remains 0.2.0, result schema 1.5 and database schema 3; fragment metadata fields are additive.

## Verification and limitations

- Read before edit: app/service and shared envelope/model/cursor paths, transcript provider, cursor/retention/envelope/transcript tests, native live script lifecycle, affected docs and operator/repository instructions. Provider parser itself is not changed.
- Baseline Full gate: 343 passed in 78.48s (0:01:18). First attempt mistakenly used unsupported Scope Local and ran no tests; the complete error is retained below.
- Initial new tests: 10 failed, 3 passed in 3.32s. Nine failures reproduce rejection, duplicated captions and the changed-layout rejection requirement. One test incorrectly required multiple pages for a short source fitting 6000; corrected before implementation. Corrected RED: 9 failed, 4 passed in 2.35s. Full assertions/errors below.
- Focused GREEN: 89 passed in 8.31s. Three added timing-only falsification cases check metadata progress without body text; no empty timing record repeats. Final Full gate: 359 passed in 99.81s (0:01:39).
- Sixteen new cases cover every supported budget, short/long/Unicode captions, 200 structured segments, mixed empty captions, timing-only evidence, provider immutability, exact text/timestamp/order restoration, wire-budget equality, cursor-only calls and old-layout rejection. Existing all-reader, immutable snapshot, snippet, unsafe URL and oversized unrelated metadata regressions stay green.
- Explicit native script: real public transcript produced identical 783-character content and all 14 timestamps at budgets 2000/4000/6000 (14/2/1 pages). Combined evidence SHA256: 239cce812bb6de2f92bc8fd78c6a8740a934a6e3e288caefe7ac1161d9791843. Native process/client restart continued the matching cached payload, restoring identical evidence. Owned temporary processes and state were removed.
- The first native script used the SDK's wrong attribute spelling isError and failed before checking the response. Fixed to the actual is_error attribute, not a product workaround. Complete traceback retained below. Native SDK INFO output still appears despite configured ERROR level.
- No installed service or DSH reload occurred during these tests. Installed activation, commit and CI receipts are recorded separately under the operator folder after delivery. DSH still requires approved scoped repair/restart; none was performed. No account, paid adapter or personal profile was used.
- Provider caps are unchanged: at most 5000 collected caption segments, structured metadata for the first 200 with an explicit warning beyond that. All retained structured metadata is paged, not newly synthesized. Missing captions, arbitrary malformed media, extreme titles/publishers/other metadata, total native RAM and full DSH/research-login/stress/install acceptance remain open. Do not interpret this source as universal transcript-provider acceptance.

## Security / release review

Existing HMAC tool/budget/version/hash validation remains; no auth route or host permission changed. No new rendering/eval/deserialization path or dependency. Inputs remain untrusted evidence. Whole selected repository/instruction-file scan and ignore checks precede commit; no credentials are needed by this native canary. LICENSE and CONTRIBUTING remain absent, dependency/package metadata and final website alignment remain unfinished. This is a private development checkpoint, not a public/package release or PR merge. No license choice is inferred.

## Exact commands and outputs

### transcriptPagingBaseline

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Local
```

```text
Invoke-QualityGate.ps1: Cannot validate argument on parameter 'Scope'. The argument "Local" does not belong to the set "Commit,CI,Full" specified by the ValidateSet attribute. Supply an argument that is in the set and then try the command again.

```

### transcriptPagingBaselineCorrected

```powershell
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
93 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
.........................................
```

### transcriptPagingBaselineEnd

```powershell
Continuation of the recorded command; no new command launched.
```

```text
............................... [ 20%]
........................................................................ [ 41%]
........................................................................ [ 62%]
........................................................................ [ 83%]
.......................................................                  [100%]
343 passed in 78.48s (0:01:18)
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```

### transcriptPagingRed

```powershell
uv run --locked python -m pytest -q tests/unit/test_transcript_paging.py
```

```text
FFFFFFFFF...F                                                            [100%]
================================== FAILURES ===================================
___ test_transcript_preserves_text_and_all_retained_timestamps[short-2000] ____

app = <starlette.applications.Starlette object at 0x0000016C242D2A80>
budget = 2000, case = 'short'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x0000016C242D2A80>
arguments = {'url': 'https://media.example/research'}, budget = 2000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
___ test_transcript_preserves_text_and_all_retained_timestamps[short-4000] ____

app = <starlette.applications.Starlette object at 0x0000016C247A3710>
budget = 4000, case = 'short'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x0000016C247A3710>
arguments = {'cursor': 'eyJiIjo0MDAwLCJjIjoxLCJleHAiOjE3ODg0MTI3MzgsImkiOjAsImsiOiJ0cmFuc2NyaXB0OjE1MjJlNGZhNTI5ZTRlZmVhYTU4OTMwZD...iNmY4YmFjM2ZmYjU2Y2YwN2RmNWRkOWU3IiwidCI6InRyYW5zY3JpcHRfZmV0Y2giLCJ2IjoyfTqW57tohmbZkuVKFKpnV93hysWM2AA4wxqnug6ZXv07'}
budget = 4000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
            assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
            wire = json.dumps(page, indent=2, ensure_ascii=False)
            assert len(wire) == page["page"]["serialized_chars"] <= budget
            for item in page["items"]:
                assert item["url"] == "https://media.example/research"
                assert item["metadata"]["language"] == "en"
                body.append(item.get("content") or "")
                snippet.append(item.get("snippet") or "")
                for index, segment in enumerate(item["metadata"].get("segments", [])):
                    key = segment.get("segment_index", index)
                    previous = segments.setdefault(key, {"start_seconds": segment["start_seconds"], "end_seconds": segment["end_seconds"], "text": ""})
                    assert (previous["start_seconds"], previous["end_seconds"]) == (segment["start_seconds"], segment["end_seconds"])
>                   assert segment.get("text_offset", 0) == len(previous["text"]), "Caption fragment repeated or missing"
E                   AssertionError: Caption fragment repeated or missing
E                   assert 0 == 41
E                    +  where 0 = <built-in method get of dict object at 0x0000016C24853BC0>('text_offset', 0)
E                    +    where <built-in method get of dict object at 0x0000016C24853BC0> = {'start_seconds': 0.0, 'end_seconds': 1.25, 'text': 'Caption 0: research evidence with timing.'}.get
E                    +  and   41 = len('Caption 0: research evidence with timing.')

tests\unit\test_transcript_paging.py:80: AssertionError
___ test_transcript_preserves_text_and_all_retained_timestamps[short-6000] ____

app = <starlette.applications.Starlette object at 0x0000016C24875BB0>
budget = 6000, case = 'short'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
        actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
        assert actual_body == body, "Caption body changed across pages"
        assert snippet == "Transcript summary."
        assert actual_segments == segments, "Structured captions lost, reordered or duplicated"
        assert result.items[0].as_dict() == before, "Pagination mutated the provider's evidence"
        if case != "empty":
>           assert pages > 1
E           assert 1 > 1

tests\unit\test_transcript_paging.py:108: AssertionError
_ test_transcript_preserves_text_and_all_retained_timestamps[long_caption-2000] _

app = <starlette.applications.Starlette object at 0x0000016C2490CA40>
budget = 2000, case = 'long_caption'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x0000016C2490CA40>
arguments = {'url': 'https://media.example/research'}, budget = 2000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
_ test_transcript_preserves_text_and_all_retained_timestamps[long_caption-4000] _

app = <starlette.applications.Starlette object at 0x0000016C24990260>
budget = 4000, case = 'long_caption'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x0000016C24990260>
arguments = {'url': 'https://media.example/research'}, budget = 4000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
_ test_transcript_preserves_text_and_all_retained_timestamps[long_caption-6000] _

app = <starlette.applications.Starlette object at 0x0000016C24A1DA30>
budget = 6000, case = 'long_caption'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x0000016C24A1DA30>
arguments = {'cursor': 'eyJiIjo2MDAwLCJjIjoxLCJleHAiOjE3ODg0MTI3MzgsImkiOjAsImsiOiJ0cmFuc2NyaXB0OjE1MjJlNGZhNTI5ZTRlZmVhYTU4OTMwZD...iY2JlMzJmZGRmMzc1YjgxYmQwYzU4NjNmIiwidCI6InRyYW5zY3JpcHRfZmV0Y2giLCJ2IjoyfcxLjeao3TqPgJN1SEQax2YvLNZqJ2RjgnHfUv2kWCqZ'}
budget = 6000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
            assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
            wire = json.dumps(page, indent=2, ensure_ascii=False)
            assert len(wire) == page["page"]["serialized_chars"] <= budget
            for item in page["items"]:
                assert item["url"] == "https://media.example/research"
                assert item["metadata"]["language"] == "en"
                body.append(item.get("content") or "")
                snippet.append(item.get("snippet") or "")
                for index, segment in enumerate(item["metadata"].get("segments", [])):
                    key = segment.get("segment_index", index)
                    previous = segments.setdefault(key, {"start_seconds": segment["start_seconds"], "end_seconds": segment["end_seconds"], "text": ""})
                    assert (previous["start_seconds"], previous["end_seconds"]) == (segment["start_seconds"], segment["end_seconds"])
>                   assert segment.get("text_offset", 0) == len(previous["text"]), "Caption fragment repeated or missing"
E                   AssertionError: Caption fragment repeated or missing
E                   assert 0 == 2273
E                    +  where 0 = <built-in method get of dict object at 0x0000016C24966F80>('text_offset', 0)
E                    +    where <built-in method get of dict object at 0x0000016C24966F80> = {'start_seconds': 0.0, 'end_seconds': 1.25, 'text': 'A single long caption: \u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "... \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n'}.get
E                    +  and   2273 = len('A single long caption: \u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\...\U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n')

tests\unit\test_transcript_paging.py:80: AssertionError
____ test_transcript_preserves_text_and_all_retained_timestamps[many-2000] ____

app = <starlette.applications.Starlette object at 0x0000016C24A974A0>
budget = 2000, case = 'many'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x0000016C24A974A0>
arguments = {'url': 'https://media.example/research'}, budget = 2000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
____ test_transcript_preserves_text_and_all_retained_timestamps[many-4000] ____

app = <starlette.applications.Starlette object at 0x0000016C24B3B7D0>
budget = 4000, case = 'many'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x0000016C24B3B7D0>
arguments = {'url': 'https://media.example/research'}, budget = 4000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
____ test_transcript_preserves_text_and_all_retained_timestamps[many-6000] ____

app = <starlette.applications.Starlette object at 0x0000016C24BC88F0>
budget = 6000, case = 'many'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x0000016C24BC88F0>
arguments = {'url': 'https://media.example/research'}, budget = 6000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
___ test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence ____

app = <starlette.applications.Starlette object at 0x0000016C24CC79B0>

    async def test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence(app):
        result = ProviderResult(
            "fixture",
            [EvidenceItem(url="https://media.example/research", retrieved_at="2026-09-03T04:00:00Z", content="text " * 1000)],
        )
        service = app.state.halo_service
        page = service._envelope("transcript_fetch", result, 2000)
        old_state = service.cursors.decode(page["page"]["next_cursor"])
        old_state["v"] = 2
        old_cursor = service.cursors.encode(old_state)
        rejected = await call(app, {"cursor": old_cursor})
>       assert not rejected["ok"], "Old cursor layout was silently interpreted by the new paginator"
E       AssertionError: Old cursor layout was silently interpreted by the new paginator
E       assert not True

tests\unit\test_transcript_paging.py:122: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[short-2000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[short-4000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[short-6000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[long_caption-2000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[long_caption-4000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[long_caption-6000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[many-2000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[many-4000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[many-6000]
FAILED tests/unit/test_transcript_paging.py::test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence
10 failed, 3 passed in 3.32s

```

### transcriptPagingRedCorrected

```powershell
uv run --locked python -m pytest -q tests/unit/test_transcript_paging.py
```

```text
FF.FFFFFF...F                                                            [100%]
================================== FAILURES ===================================
___ test_transcript_preserves_text_and_all_retained_timestamps[short-2000] ____

app = <starlette.applications.Starlette object at 0x000002C8198217F0>
budget = 2000, case = 'short'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000002C8198217F0>
arguments = {'url': 'https://media.example/research'}, budget = 2000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
___ test_transcript_preserves_text_and_all_retained_timestamps[short-4000] ____

app = <starlette.applications.Starlette object at 0x000002C819920DD0>
budget = 4000, case = 'short'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000002C819920DD0>
arguments = {'cursor': 'eyJiIjo0MDAwLCJjIjoxLCJleHAiOjE3ODg0MTI4MDksImkiOjAsImsiOiJ0cmFuc2NyaXB0OjE1MjJlNGZhNTI5ZTRlZmVhYTU4OTMwZD...iNmY4YmFjM2ZmYjU2Y2YwN2RmNWRkOWU3IiwidCI6InRyYW5zY3JpcHRfZmV0Y2giLCJ2IjoyfcTgqzIdsPoi1poHRC73ESr-RmKZRlaDzUcmQ0759xjG'}
budget = 4000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
            assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
            wire = json.dumps(page, indent=2, ensure_ascii=False)
            assert len(wire) == page["page"]["serialized_chars"] <= budget
            for item in page["items"]:
                assert item["url"] == "https://media.example/research"
                assert item["metadata"]["language"] == "en"
                body.append(item.get("content") or "")
                snippet.append(item.get("snippet") or "")
                for index, segment in enumerate(item["metadata"].get("segments", [])):
                    key = segment.get("segment_index", index)
                    previous = segments.setdefault(key, {"start_seconds": segment["start_seconds"], "end_seconds": segment["end_seconds"], "text": ""})
                    assert (previous["start_seconds"], previous["end_seconds"]) == (segment["start_seconds"], segment["end_seconds"])
>                   assert segment.get("text_offset", 0) == len(previous["text"]), "Caption fragment repeated or missing"
E                   AssertionError: Caption fragment repeated or missing
E                   assert 0 == 41
E                    +  where 0 = <built-in method get of dict object at 0x000002C81999A680>('text_offset', 0)
E                    +    where <built-in method get of dict object at 0x000002C81999A680> = {'start_seconds': 0.0, 'end_seconds': 1.25, 'text': 'Caption 0: research evidence with timing.'}.get
E                    +  and   41 = len('Caption 0: research evidence with timing.')

tests\unit\test_transcript_paging.py:80: AssertionError
_ test_transcript_preserves_text_and_all_retained_timestamps[long_caption-2000] _

app = <starlette.applications.Starlette object at 0x000002C819A2F8C0>
budget = 2000, case = 'long_caption'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000002C819A2F8C0>
arguments = {'url': 'https://media.example/research'}, budget = 2000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
_ test_transcript_preserves_text_and_all_retained_timestamps[long_caption-4000] _

app = <starlette.applications.Starlette object at 0x000002C819B0B6E0>
budget = 4000, case = 'long_caption'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000002C819B0B6E0>
arguments = {'url': 'https://media.example/research'}, budget = 4000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
_ test_transcript_preserves_text_and_all_retained_timestamps[long_caption-6000] _

app = <starlette.applications.Starlette object at 0x000002C819B0AFC0>
budget = 6000, case = 'long_caption'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000002C819B0AFC0>
arguments = {'cursor': 'eyJiIjo2MDAwLCJjIjoxLCJleHAiOjE3ODg0MTI4MTAsImkiOjAsImsiOiJ0cmFuc2NyaXB0OjE1MjJlNGZhNTI5ZTRlZmVhYTU4OTMwZD...iY2JlMzJmZGRmMzc1YjgxYmQwYzU4NjNmIiwidCI6InRyYW5zY3JpcHRfZmV0Y2giLCJ2IjoyfaHbJY3uutu7oHVSv-9hcKwKBxYO1SEqx01P0aO48ShH'}
budget = 6000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
            assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
            wire = json.dumps(page, indent=2, ensure_ascii=False)
            assert len(wire) == page["page"]["serialized_chars"] <= budget
            for item in page["items"]:
                assert item["url"] == "https://media.example/research"
                assert item["metadata"]["language"] == "en"
                body.append(item.get("content") or "")
                snippet.append(item.get("snippet") or "")
                for index, segment in enumerate(item["metadata"].get("segments", [])):
                    key = segment.get("segment_index", index)
                    previous = segments.setdefault(key, {"start_seconds": segment["start_seconds"], "end_seconds": segment["end_seconds"], "text": ""})
                    assert (previous["start_seconds"], previous["end_seconds"]) == (segment["start_seconds"], segment["end_seconds"])
>                   assert segment.get("text_offset", 0) == len(previous["text"]), "Caption fragment repeated or missing"
E                   AssertionError: Caption fragment repeated or missing
E                   assert 0 == 2273
E                    +  where 0 = <built-in method get of dict object at 0x000002C819BE4E40>('text_offset', 0)
E                    +    where <built-in method get of dict object at 0x000002C819BE4E40> = {'start_seconds': 0.0, 'end_seconds': 1.25, 'text': 'A single long caption: \u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "... \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n'}.get
E                    +  and   2273 = len('A single long caption: \u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\...\U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n\u7814\u7a76 \U0001f50e \\\\ "\\n')

tests\unit\test_transcript_paging.py:80: AssertionError
____ test_transcript_preserves_text_and_all_retained_timestamps[many-2000] ____

app = <starlette.applications.Starlette object at 0x000002C819C12ED0>
budget = 2000, case = 'many'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000002C819C12ED0>
arguments = {'url': 'https://media.example/research'}, budget = 2000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
____ test_transcript_preserves_text_and_all_retained_timestamps[many-4000] ____

app = <starlette.applications.Starlette object at 0x000002C819C81C40>
budget = 4000, case = 'many'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000002C819C81C40>
arguments = {'url': 'https://media.example/research'}, budget = 4000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
____ test_transcript_preserves_text_and_all_retained_timestamps[many-6000] ____

app = <starlette.applications.Starlette object at 0x000002C819D255B0>
budget = 6000, case = 'many'

    @pytest.mark.parametrize("budget", [2000, 4000, 6000])
    @pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty"])
    async def test_transcript_preserves_text_and_all_retained_timestamps(app, budget, case):
        result, body, segments = source(case)
        before = copy.deepcopy(result.items[0].as_dict())
    
        async def fetch(*args):
            return result
    
        app.state.halo_service.transcripts.fetch = fetch
>       actual_body, snippet, actual_segments, pages = await collect(app, {"url": result.items[0].url}, budget)
                                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

tests\unit\test_transcript_paging.py:102: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

app = <starlette.applications.Starlette object at 0x000002C819D255B0>
arguments = {'url': 'https://media.example/research'}, budget = 6000

    async def collect(app, arguments, budget):
        body, snippet, segments = [], [], {}
        pages = 0
        while True:
            page = await call(app, dict(arguments, max_chars=budget))
>           assert page["ok"], f"Readable caption evidence rejected: {page.get('error')}"
E           AssertionError: Readable caption evidence rejected: {'code': 'OUTPUT_ITEM_TOO_LARGE', 'message': 'ValueError: operation did not complete'}
E           assert False

tests\unit\test_transcript_paging.py:68: AssertionError
___ test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence ____

app = <starlette.applications.Starlette object at 0x000002C819E45BB0>

    async def test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence(app):
        result = ProviderResult(
            "fixture",
            [EvidenceItem(url="https://media.example/research", retrieved_at="2026-09-03T04:00:00Z", content="text " * 1000)],
        )
        service = app.state.halo_service
        page = service._envelope("transcript_fetch", result, 2000)
        old_state = service.cursors.decode(page["page"]["next_cursor"])
        old_state["v"] = 2
        old_cursor = service.cursors.encode(old_state)
        rejected = await call(app, {"cursor": old_cursor})
>       assert not rejected["ok"], "Old cursor layout was silently interpreted by the new paginator"
E       AssertionError: Old cursor layout was silently interpreted by the new paginator
E       assert not True

tests\unit\test_transcript_paging.py:122: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[short-2000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[short-4000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[long_caption-2000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[long_caption-4000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[long_caption-6000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[many-2000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[many-4000]
FAILED tests/unit/test_transcript_paging.py::test_transcript_preserves_text_and_all_retained_timestamps[many-6000]
FAILED tests/unit/test_transcript_paging.py::test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence
9 failed, 4 passed in 2.35s

```

### transcriptPagingGreen

```powershell
uv run --locked ruff format src/halo_research_gateway/envelope.py src/halo_research_gateway/service.py tests/unit/test_transcript_paging.py
uv run --locked python -m pytest -q tests/unit/test_transcript_paging.py tests/unit/test_result_retention.py tests/unit/test_cursor_tool_contract.py tests/unit/test_envelope.py tests/unit/test_transcript_community.py
```

```text
1 file reformatted, 2 files left unchanged
........................................................................ [ 80%]
.................                                                        [100%]
89 passed in 8.31s

```

### transcriptPagingNative

```powershell
uv run --locked ruff format tests/acceptance/transcript_mcp_native_live.py
uv run --locked ruff check src tests
if ($LASTEXITCODE) { exit $LASTEXITCODE }
uv run --locked python tests/acceptance/transcript_mcp_native_live.py
```

```text
1 file reformatted
All checks passed!
NATIVE GATEWAY OUTPUT: [09/02/26 22:22:46] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager                                   
                             started                                           
[09/02/26 22:22:47] INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     HTTP Request: GET                  _client.py:1740
                             https://iandevlin.github.io/mdn/vi                
                             deo-player-with-captions/                         
                             "HTTP/1.1 200 OK"                                 
[09/02/26 22:22:48] INFO     HTTP Request: GET                  _client.py:1740
                             https://iandevlin.github.io/mdn/vi                
                             deo-player-with-captions/subtitles                
                             /vtt/sintel-en.vtt "HTTP/1.1 200                  
                             OK"                                               
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814

{"owned_native_process_stopped": true}
  + Exception Group Traceback (most recent call last):
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\transcript_mcp_native_live.py", line 196, in <module>
  |     asyncio.run(main())
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 195, in run
  |     return runner.run(main)
  |            ^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\runners.py", line 118, in run
  |     return self._loop.run_until_complete(task)
  |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\asyncio\base_events.py", line 691, in run_until_complete
  |     return future.result()
  |            ^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\transcript_mcp_native_live.py", line 130, in main
  |     async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
  |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\AppData\Local\Programs\Python\Python312\Lib\contextlib.py", line 231, in __aexit__
  |     await self.gen.athrow(value)
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 688, in streamable_http_client
  |     anyio.create_task_group() as tg,
  |     ^^^^^^^^^^^^^^^^^^^^^^^^^
  |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
  |     raise BaseExceptionGroup(
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Exception Group Traceback (most recent call last):
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\streamable_http.py", line 705, in streamable_http_client
    |     yield read_stream, write_stream
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\transcript_mcp_native_live.py", line 131, in main
    |     async with ClientSession(streams[0], streams[1]) as session:
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\mcp\client\session.py", line 521, in __aexit__
    |     result = await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\anyio\_backends\_asyncio.py", line 815, in __aexit__
    |     raise BaseExceptionGroup(
    | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
    +-+---------------- 1 ----------------
      | Traceback (most recent call last):
      |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\transcript_mcp_native_live.py", line 134, in main
      |     first = await page(session, {"url": URL, "language": "en"}, budget)
      |             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\tests\acceptance\transcript_mcp_native_live.py", line 47, in page
      |     assert not reply.isError
      |                ^^^^^^^^^^^^^
      |   File "C:\Users\scott\Desktop\Code\halo-research-gateway\.venv\Lib\site-packages\pydantic\main.py", line 1042, in __getattr__
      |     raise AttributeError(f'{type(self).__name__!r} object has no attribute {item!r}')
      | AttributeError: 'CallToolResult' object has no attribute 'isError'. Did you mean: 'is_error'?
      +------------------------------------

```

### transcriptPagingNativeCorrected

```powershell
uv run --locked python tests/acceptance/transcript_mcp_native_live.py
```

```text
{"case": "public_transcript", "url": "https://iandevlin.github.io/mdn/video-player-with-captions/", "max_chars": 2000, "pages": 14, "content_chars": 783, "segments": 14, "evidence_sha256": "239cce812bb6de2f92bc8fd78c6a8740a934a6e3e288caefe7ac1161d9791843", "warnings": ["RESULT_TRUNCATED"]}
{"case": "public_transcript", "url": "https://iandevlin.github.io/mdn/video-player-with-captions/", "max_chars": 4000, "pages": 2, "content_chars": 783, "segments": 14, "evidence_sha256": "239cce812bb6de2f92bc8fd78c6a8740a934a6e3e288caefe7ac1161d9791843", "warnings": ["RESULT_TRUNCATED"]}
{"case": "public_transcript", "url": "https://iandevlin.github.io/mdn/video-player-with-captions/", "max_chars": 6000, "pages": 1, "content_chars": 783, "segments": 14, "evidence_sha256": "239cce812bb6de2f92bc8fd78c6a8740a934a6e3e288caefe7ac1161d9791843", "warnings": []}
NATIVE GATEWAY OUTPUT: [09/02/26 22:23:16] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager                                   
                             started                                           
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
[09/02/26 22:23:17] INFO     HTTP Request: GET                  _client.py:1740
                             https://iandevlin.github.io/mdn/vi                
                             deo-player-with-captions/                         
                             "HTTP/1.1 200 OK"                                 
[09/02/26 22:23:18] INFO     HTTP Request: GET                  _client.py:1740
                             https://iandevlin.github.io/mdn/vi                
                             deo-player-with-captions/subtitles                
                             /vtt/sintel-en.vtt "HTTP/1.1 200                  
                             OK"                                               
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814

{"case": "new_process_and_client_continue_cached_transcript", "remaining_pages": 13, "identical_evidence": true, "warnings": ["RESULT_TRUNCATED"]}
Native transcript text/timestamps at all budgets and restart continuation PASS
NATIVE GATEWAY OUTPUT: [09/02/26 22:23:20] INFO     StreamableHTTP      streamable_http_manager.py:148
                             session manager                                   
                             started                                           
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814
                    INFO     Terminating session: None   streamable_http.py:814

{"owned_native_process_stopped": true}
Temporary native Gateway state removed

```

### transcriptPagingFullGate

```powershell
uv run --locked ruff format tests/unit/test_transcript_paging.py
pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Full
```

```text
1 file left unchanged
[GATE] lock check
Resolved 130 packages in 2ms
[GATE] format
95 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
.....................................
```

### transcriptPagingFullGateEnd

```powershell
Continuation of the recorded command; no new command launched.
```

```text
................................... [ 20%]
........................................................................ [ 40%]
........................................................................ [ 60%]
........................................................................ [ 80%]
.......................................................................  [100%]
359 passed in 99.81s (0:01:39)

```

### transcriptPagingFullGateFinal

```powershell
Continuation of the recorded command; no new command launched.
```

```text
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Full)

```
