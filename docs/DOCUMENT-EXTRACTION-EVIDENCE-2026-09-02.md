# Document extraction checkpoint — 2026-09-02

## Outcome and scope

This research-only checkpoint fixes previously ignored `document_extract` table/OCR arguments. MCP forwards both controls; option-specific `document:v2` cache keys prevent incompatible cached results. PDF extraction returns page-cited native layout tables and local English OCR, with a separate owned native parser process, cancellation cleanup, validation, and explicit limits. Non-PDF page selection/forced OCR fail explicitly. Recognized sensitive PDF redirect citation query values are redacted and the result bypasses disk cache. Generic HTTP/non-PDF redirect protection remains an independent open gap.

Read before editing: application wrapper, service cache/envelope flow, document/HTTP/crawl providers, models, URL policy, configuration, installer, adjacent tests, and current documentation/scope. The baseline was clean private main at `354fcae3f954a5e314abb5c36e01fa96d9188330`. DSH packages/models/presets/permissions/sessions were not changed. Product remains 0.2.0; this is a development checkpoint, not a complete release.

## Verification, with exact commands

Baseline command: `pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit`

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
82 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 31%]
........................................................................ [ 63%]
........................................................................ [ 95%]
...........                                                              [100%]
227 passed in 48.85s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

Final edge-case RED command:

```powershell
uv run --locked pytest -q tests/unit/test_document_options.py -k 'unsupported_page_selection or silently_clip or sensitive_pdf'
```

```text
FFF                                                                      [100%]
================================== FAILURES ===================================
_______________ test_non_pdf_rejects_unsupported_page_selection _______________

    async def test_non_pdf_rejects_unsupported_page_selection():
>       with pytest.raises(ValueError, match="DOCUMENT_PAGES_REQUIRE_PDF"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_document_options.py:308: Failed
__________ test_page_selection_does_not_silently_clip_missing_pages ___________

    def test_page_selection_does_not_silently_clip_missing_pages():
>       with pytest.raises(ValueError, match="PAGE_SELECTION_INVALID"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_document_options.py:313: Failed
_________ test_sensitive_pdf_redirect_is_redacted_and_not_disk_cached _________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1950/test_sensitive_pdf_redirect_is0')

    async def test_sensitive_pdf_redirect_is_redacted_and_not_disk_cached(tmp_path):
        app = application_at(tmp_path)
        calls = []
    
        class RedirectFetcher(PdfFetcher):
            async def download(self, url, accept):
                calls.append(url)
                return (
                    "https://example.org/research.pdf?token=fixture-secret",
                    SimpleNamespace(host="example.org"),
                    {"content-type": "application/pdf"},
                    self.payload,
                )
    
        app.state.halo_service.documents.fetcher = RedirectFetcher(table_pdf())
        try:
            for _ in range(2):
                result = await call_document(app, include_tables=False, ocr="never")
                assert result["ok"], result
>               assert all("fixture-secret" not in item["url"] for item in result["items"])
E               assert False
E                +  where False = all(<generator object test_sensitive_pdf_redirect_is_redacted_and_not_disk_cached.<locals>.<genexpr> at 0x000002B29AC5BE00>)

tests\unit\test_document_options.py:336: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_document_options.py::test_non_pdf_rejects_unsupported_page_selection
FAILED tests/unit/test_document_options.py::test_page_selection_does_not_silently_clip_missing_pages
FAILED tests/unit/test_document_options.py::test_sensitive_pdf_redirect_is_redacted_and_not_disk_cached
3 failed, 20 deselected in 1.27s
```

Combined GREEN command (30 unit cases plus four explicit native OCR fixtures):

```powershell
uv run --locked pytest -q tests/unit/test_document_options.py tests/unit/test_ocr_data.py tests/acceptance/test_document_native.py
```

```text
..................................                                       [100%]
34 passed in 5.85s
```

Final gate command (two statements in the original PowerShell invocation):

```powershell
uv run --locked ruff format src/halo_research_gateway/providers/document_extract.py tests/unit/test_document_options.py; pwsh -NoProfile -File scripts/Invoke-QualityGate.ps1 -Scope Commit
```

```text
2 files left unchanged
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
86 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 28%]
........................................................................ [ 56%]
........................................................................ [ 84%]
.........................................                                [100%]
257 passed in 49.89s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

## What the tests actually prove

- `tests/unit/test_document_options.py`: real MCP wrapper forwarding, distinct provider/cache options, generated native PDF table structure/citations, page selection, parser outside the Gateway process, forced missing-data errors, real parse deadline, native child cleanup during spawn and repeated cancellation, bounds/truncation warnings, OCR discovery and pixel guard, non-PDF behavior, and signed-redirect redaction/cache bypass.
- `tests/unit/test_ocr_data.py`: verified/idempotent asset installation, hash/size rejection, preservation of existing/racing operator files, temporary-file cleanup after fsync failure, and actual installer-script invocation of OCR setup with mocked installation commands in disposable paths. This last case is wiring proof, not a full installer run.
- `tests/acceptance/test_document_native.py`: actual English OCR of generated image-only/mixed PDFs through the real MCP dispatcher, service and native parser child. Auto/force retain `HALO LOCAL OCR EVIDENCE` and page citations; never returns an honest no-text error. Only the download boundary is replaced by generated bytes. It is not network-MCP, live-source or DSH acceptance. No document was uploaded.

Falsification covered missing data, malformed/out-of-range page selectors, oversized images before rasterization, excessive table/text content, cancellation while spawning/cleaning, non-PDF options, signed redirect URLs, interrupted asset writes and concurrent destination creation. The initial tests exposed real failures; repairs were followed by targeted and full tests. Full earlier diagnostic outputs are retained in the companion transcript, but the exact command fields for those pre-compaction invocations were not recovered, so they are not substituted for the command-bound receipts above.

## Local setup and provenance

The existing locked PyMuPDF 1.28.2 dependency supplies the parser and integrated OCR engine. No pip dependency, global Tesseract application, WSL, Docker, cloud OCR, account, or paid call was added. `Install-HaloResearch.ps1` invokes `uv run --locked python -m halo_research_gateway.ocr_data`; the same command is available for an updated environment.

Official pinned source: [tesseract-ocr/tessdata_fast revision 8741641](https://github.com/tesseract-ocr/tessdata_fast/tree/87416418657359cb625c412a48b6e1d6d41c29bd). Assets are fetched from that revision, not a moving branch, verified before exclusive atomic publication, and installed in `.venv/share/tessdata`.

| Installed asset | Bytes | SHA-256 |
| --- | ---: | --- |
| eng.traineddata | 4113088 | `7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2` |
| TESSDATA-LICENSE.txt | 11358 | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |

Git blob hashes independently checked against official GitHub metadata: `bbef4675053b5b468cdb477053e28b1c698ba08e` (English), `d645695673349e3947e8e5ae42332d0ac3164cd7` (license). Verified existing files are reused; an unrecognized existing file is preserved and setup fails. Native exclusive hardlink publication was exercised on this workstation's filesystem, not every possible Windows volume.

Primary implementation references: [PyMuPDF OCR](https://pymupdf.readthedocs.io/en/latest/recipes-ocr.html), [table detection API](https://pymupdf.readthedocs.io/en/latest/page.html#Page.find_tables), and [process guidance](https://pymupdf.readthedocs.io/en/latest/recipes-multiprocessing.html). The process design avoids using the PDF parser concurrently in Gateway threads.

## Security, performance and limits

- Inputs: existing public-only DNS-pinned downloader; PDF size/magic, option enums/types, page grammar/count, selected pages, OCR page pixels, table/text/output limits. See manual for numeric limits. No new public endpoint or tool.
- Authentication/authorization: unchanged localhost MCP and public URL policy; no DSH permissions or research-connection scopes changed.
- Secrets: PDF recognized sensitive original/final URLs are redacted and excluded from disk cache; no raw worker exception/prose/URL diagnostics are logged. Recognition is pattern-based. Generic HTTP/non-PDF fallback final-redirect handling remains open; arbitrary sensitive prose is not automatically sanitized.
- Execution/deserialization: no eval, shell command interpolation or document-supplied executable command. Parent launches a fixed Python module and exchanges bounded JSON/PDF over pipes. Native PDF parsing is attack surface: process separation/time limits are not a privilege or hard-RAM sandbox.
- Dependencies: no new Python package; existing lock unchanged. New OCR data/license are official revision/size/SHA-pinned. No fresh vulnerability database scan is claimed for the existing parser dependency.
- Performance: each uncached PDF launches one parser process. Download timeout remains the HTTP layer's limit; parse timeout is 120 seconds after process creation. Input/output/text/table/raster ceilings limit work, but internal parser/table allocations may peak before clipping. Hard native peak-memory bounds remain open.
- Coverage: English OCR only; auto uses no-text/large-image heuristic. Small labels/vector-outlined text may not trigger auto; use force deliberately. Scanned table grids are not reconstructed. OCR/table detection accuracy for arbitrary source layouts is unproved. Unsupported/password/corrupt/no-text PDFs report errors.
- Cache/deployment: cache namespace changes intentionally avoid legacy option-less entries, which remain subject to normal expiry/eviction; no user database data was erased. Restart of the Gateway is needed to load changed Python code. Production rollout/CI identity is recorded separately after verification.

## Local asset verification

Exact command (existing verified files; no download):

```powershell
uv run --locked python -m halo_research_gateway.ocr_data; Get-FileHash -Algorithm SHA256 .venv/share/tessdata/eng.traineddata,.venv/share/tessdata/TESSDATA-LICENSE.txt
```

```text
OCR data: eng.traineddata: verified-existing
OCR data: TESSDATA-LICENSE.txt: verified-existing

Algorithm       Hash                                                                   Path
---------       ----                                                                   ----
SHA256          7D4322BD2A7749724879683FC3912CB542F19906C83BCC1A52132556427170B2       C:\Users\scott\Desktop\Code\hal…
SHA256          CFC7749B96F63BD31C3C42B5C471BF756814053E847C10F3EB003417BC523D30       C:\Users\scott\Desktop\Code\hal…
```

## Delivery and remaining work

README, changelog, manual, operations, implementation status, progress and scope/reference copies are updated with actual behavior and limitations. Git/CI/runtime/recovery receipts must identify this exact checkpoint after delivery; a green local gate is not a deployed claim. DSH integration approval, crawl options, login/challenge/provider routing, broader cancellation/shared bounds, clean installation and final site alignment remain open. No Gmail, GitHub writes, shopping, account management or general actions were added.

Private-push checklist: the remote was freshly verified private; 222 tracked/new/instruction files were scanned with credential-prefix/private-key/userinfo patterns. Six candidate locations were existing redaction/security fixtures (debug_redaction.py, verify_implementation.py and three unit-test files), not actual credentials. This is a targeted pattern scan and review, not proof that every possible secret format is detected. `.gitignore` excludes environment/config, credentials, DB/vault, build/cache and installed OCR assets. README/changelog/manual/scope/operations are updated; full deterministic gate and explicit document fixtures are green. No LICENSE/CONTRIBUTING file or fresh package-release metadata is claimed; those public-release decisions remain open. The owner-only site is not republished by this code checkpoint. No new product tag or PR merge is claimed.
