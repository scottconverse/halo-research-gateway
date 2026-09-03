# Document checkpoint: recovered diagnostic transcript

These are complete saved outputs from earlier incremental runs in this task. The exact invocation commands were not retained in the recovered tool-state objects; do not treat this appendix as command-bound verification. The companion DOCUMENT-EXTRACTION-EVIDENCE-2026-09-02.md contains subsequent exact-command RED/GREEN/full-gate receipts. Labels below identify stored outputs, not shell commands. Fixtures contain deliberately artificial example URLs/tokens only.

## documentOptionsRed

```text
FFF                                                                      [100%]
================================== FAILURES ===================================
___________________ test_mcp_document_options_reach_service ___________________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1936/test_mcp_document_options_reac0')

    async def test_mcp_document_options_reach_service(tmp_path):
        app = application_at(tmp_path)
        seen = []
    
        async def extract(*args, **kwargs):
            seen.append(kwargs)
            return {"ok": True}
    
        app.state.halo_service.document_extract = extract
        try:
            await call_document(app, pages="2", include_tables=False, ocr="force")
>           assert seen[0].get("include_tables") is False
E           AssertionError: assert None is False
E            +  where None = <built-in method get of dict object at 0x0000029C1EF65A40>('include_tables')
E            +    where <built-in method get of dict object at 0x0000029C1EF65A40> = {'client': 'unidentified', 'max_age_seconds': None}.get

tests\unit\test_document_options.py:44: AssertionError
____ test_document_options_have_distinct_provider_calls_and_cache_entries _____

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1936/test_document_options_have_dis0')

    async def test_document_options_have_distinct_provider_calls_and_cache_entries(tmp_path):
        app = application_at(tmp_path)
        seen = []
    
        async def extract(url, pages, **options):
            seen.append(options)
            return ProviderResult("fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="evidence")])
    
        app.state.halo_service.documents.extract = extract
        try:
            for include_tables, ocr in [(False, "never"), (True, "never"), (True, "force")]:
                result = await call_document(app, include_tables=include_tables, ocr=ocr)
                assert result["ok"], result
>           assert len(seen) == 3, "different extraction options reused the same cached result"
E           AssertionError: different extraction options reused the same cached result
E           assert 1 == 3
E            +  where 1 = len([{}])

tests\unit\test_document_options.py:63: AssertionError
______________ test_pdf_default_extracts_citable_table_structure ______________

    async def test_pdf_default_extracts_citable_table_structure():
        result = await DocumentProvider(PdfFetcher(table_pdf())).extract(URL)
        tables = [item for item in result.items if item.metadata.get("kind") == "table"]
>       assert tables, "include_tables defaults true, but no structured table was returned"
E       AssertionError: include_tables defaults true, but no structured table was returned
E       assert []

tests\unit\test_document_options.py:95: AssertionError
---------------------------- Captured stdout call -----------------------------
warning: The `fitz` API is deprecated and will be removed in future. Use `import pymupdf` instead.
=========================== short test summary info ===========================
FAILED tests/unit/test_document_options.py::test_mcp_document_options_reach_service
FAILED tests/unit/test_document_options.py::test_document_options_have_distinct_provider_calls_and_cache_entries
FAILED tests/unit/test_document_options.py::test_pdf_default_extracts_citable_table_structure
3 failed in 1.26s
```

## documentOptionsGreen

```text
...                                                                      [100%]
3 passed in 1.15s
```

## documentWorkerRed

```text
FFFFF.                                                                   [100%]
================================== FAILURES ===================================
____________ test_pdf_parsing_does_not_run_in_the_gateway_process _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x00000159A84A8C50>

    async def test_pdf_parsing_does_not_run_in_the_gateway_process(monkeypatch):
        payload = table_pdf()
        opened_in_gateway = []
    
        def forbidden_parent_parser(*args, **kwargs):
            opened_in_gateway.append(True)
            raise RuntimeError("parent parser called")
    
        monkeypatch.setattr(pymupdf, "open", forbidden_parent_parser)
        try:
            result = await DocumentProvider(PdfFetcher(payload)).extract(URL, include_tables=False)
        except RuntimeError:
            result = None
>       assert not opened_in_gateway, "PDF parser ran inside the shared Gateway process"
E       AssertionError: PDF parser ran inside the shared Gateway process
E       assert not [True]

tests\unit\test_document_options.py:116: AssertionError
_____________ test_forced_ocr_reports_missing_local_language_data _____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1938/test_forced_ocr_reports_missin0')

    async def test_forced_ocr_reports_missing_local_language_data(tmp_path):
        provider = DocumentProvider(PdfFetcher(table_pdf()))
        provider.tessdata_directory = str(tmp_path / "deliberately-missing-tessdata")
>       with pytest.raises(RuntimeError, match="OCR_UNAVAILABLE"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE RuntimeError

tests\unit\test_document_options.py:123: Failed
---------------------------- Captured stdout call -----------------------------
Consider using the pymupdf_layout package for a greatly improved page layout analysis.
_____ test_invalid_or_overlong_page_selection_is_not_silently_accepted[0] _____

selection = '0'

    @pytest.mark.parametrize("selection", ["0", "2-1", "9999", "1," * 600])
    def test_invalid_or_overlong_page_selection_is_not_silently_accepted(selection):
>       with pytest.raises(ValueError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_document_options.py:129: Failed
____ test_invalid_or_overlong_page_selection_is_not_silently_accepted[2-1] ____

selection = '2-1'

    @pytest.mark.parametrize("selection", ["0", "2-1", "9999", "1," * 600])
    def test_invalid_or_overlong_page_selection_is_not_silently_accepted(selection):
>       with pytest.raises(ValueError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_document_options.py:129: Failed
___ test_invalid_or_overlong_page_selection_is_not_silently_accepted[9999] ____

selection = '9999'

    @pytest.mark.parametrize("selection", ["0", "2-1", "9999", "1," * 600])
    def test_invalid_or_overlong_page_selection_is_not_silently_accepted(selection):
>       with pytest.raises(ValueError):
             ^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_document_options.py:129: Failed
=========================== short test summary info ===========================
FAILED tests/unit/test_document_options.py::test_pdf_parsing_does_not_run_in_the_gateway_process
FAILED tests/unit/test_document_options.py::test_forced_ocr_reports_missing_local_language_data
FAILED tests/unit/test_document_options.py::test_invalid_or_overlong_page_selection_is_not_silently_accepted[0]
FAILED tests/unit/test_document_options.py::test_invalid_or_overlong_page_selection_is_not_silently_accepted[2-1]
FAILED tests/unit/test_document_options.py::test_invalid_or_overlong_page_selection_is_not_silently_accepted[9999]
5 failed, 1 passed, 3 deselected in 1.47s
```

## documentTimeoutRed

```text
F                                                                        [100%]
================================== FAILURES ===================================
___________________ test_document_parse_has_a_real_deadline ___________________

    async def test_document_parse_has_a_real_deadline():
        provider = DocumentProvider(PdfFetcher(table_pdf()))
        provider.timeout_seconds = 0.001
>       with pytest.raises(RuntimeError, match="DOCUMENT_EXTRACTION_TIMEOUT"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE RuntimeError

tests\unit\test_document_options.py:130: Failed
---------------------------- Captured stdout call -----------------------------
Consider using the pymupdf_layout package for a greatly improved page layout analysis.
=========================== short test summary info ===========================
FAILED tests/unit/test_document_options.py::test_document_parse_has_a_real_deadline
1 failed, 9 deselected in 0.90s
```

## documentWorkerGreen

```text
..........                                                               [100%]
10 passed in 1.73s
```

## documentCancelRed

```text
FF                                                                       [100%]
================================== FAILURES ===================================
___________ test_cancel_during_worker_start_does_not_orphan_process ___________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000018296922930>

    async def test_cancel_during_worker_start_does_not_orphan_process(monkeypatch):
        provider = DocumentProvider(PdfFetcher(table_pdf()))
        native_spawn = asyncio.create_subprocess_exec
        spawned, release = asyncio.Event(), asyncio.Event()
        children = []
    
        async def slow_spawn(*args, **kwargs):
            process = await native_spawn(sys.executable, "-c", "import time; time.sleep(60)", **kwargs)
            children.append(process)
            spawned.set()
            await release.wait()
            return process
    
        monkeypatch.setattr(asyncio, "create_subprocess_exec", slow_spawn)
        task = asyncio.create_task(provider.extract(URL))
        try:
            await asyncio.wait_for(spawned.wait(), 5)
            task.cancel()
            await asyncio.sleep(0)
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await task
>           assert children[0].returncode is not None, "cancel during spawn orphaned the parser process"
E           AssertionError: cancel during spawn orphaned the parser process
E           assert None is not None
E            +  where None = <Process 43204>.returncode

tests\unit\test_document_options.py:164: AssertionError
________________ test_repeated_cancel_finishes_worker_cleanup _________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000018296921970>

    async def test_repeated_cancel_finishes_worker_cleanup(monkeypatch):
        provider = DocumentProvider(PdfFetcher(table_pdf()))
        native_spawn = asyncio.create_subprocess_exec
        entered, cleaning, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
        children = []
    
        async def instrumented_spawn(*args, **kwargs):
            child = await native_spawn(sys.executable, "-c", "import sys,time; sys.stdin.buffer.read(); time.sleep(60)", **kwargs)
            children.append(child)
            communicate = child.communicate
            count = 0
    
            async def instrumented_communicate(input=None):
                nonlocal count
                count += 1
                if count == 1:
                    entered.set()
                else:
                    cleaning.set()
                    await release.wait()
                return await communicate(input)
    
            child.communicate = instrumented_communicate
            return child
    
        monkeypatch.setattr(asyncio, "create_subprocess_exec", instrumented_spawn)
        task = asyncio.create_task(provider.extract(URL))
        try:
            await asyncio.wait_for(entered.wait(), 5)
            task.cancel()
            await asyncio.wait_for(cleaning.wait(), 5)
            task.cancel()
            await asyncio.sleep(0)
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await task
>           assert not provider._workers, "repeated cancellation abandoned worker cleanup"
E           AssertionError: repeated cancellation abandoned worker cleanup
E           assert not {<Process 5344>}
E            +  where {<Process 5344>} = <halo_research_gateway.providers.document_extract.DocumentProvider object at 0x00000182968B1A00>._workers

tests\unit\test_document_options.py:210: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_document_options.py::test_cancel_during_worker_start_does_not_orphan_process
FAILED tests/unit/test_document_options.py::test_repeated_cancel_finishes_worker_cleanup
2 failed, 10 deselected in 0.93s
```

## documentCancelGreen

```text
............                                                             [100%]
12 passed in 1.85s
```

## documentBoundsRed

```text
FF                                                                       [100%]
================================== FAILURES ===================================
_____________ test_table_count_and_size_are_bounded_with_warnings _____________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002376443F8F0>

    def test_table_count_and_size_are_bounded_with_warnings(monkeypatch):
        table = SimpleNamespace(extract=lambda: [["x" * 1000] * 40 for _ in range(150)])
        monkeypatch.setattr(pymupdf.Page, "find_tables", lambda *args, **kwargs: SimpleNamespace(tables=[table] * 60))
        result = _parse_pdf(table_pdf(), {"pages": None, "include_tables": True, "ocr": "never", "tessdata": None})
        tables = [item for item in result["items"] if item["kind"] == "table"]
>       assert len(tables) <= 50
E       AssertionError: assert 60 <= 50
E        +  where 60 = len([{'page': 1, 'kind': 'table', 'table': 1, 'content': '| xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx...xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx |'}, ...])

tests\unit\test_document_options.py:225: AssertionError
_________________ test_large_page_text_is_explicitly_partial __________________

monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000023764923A70>

    def test_large_page_text_is_explicitly_partial(monkeypatch):
        monkeypatch.setattr(pymupdf.Page, "get_text", lambda *args, **kwargs: "research " * 10_000)
        result = _parse_pdf(table_pdf(), {"pages": None, "include_tables": False, "ocr": "never", "tessdata": None})
>       assert len(result["items"][0]["content"]) <= 50_000
E       AssertionError: assert 90000 <= 50000
E        +  where 90000 = len('research research research research research research research research research research research research research ... research research research research research research research research research research research research research ')

tests\unit\test_document_options.py:235: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_document_options.py::test_table_count_and_size_are_bounded_with_warnings
FAILED tests/unit/test_document_options.py::test_large_page_text_is_explicitly_partial
2 failed, 14 deselected in 1.15s
```

## documentBoundsGreen

```text
................                                                         [100%]
16 passed in 2.39s
```

## documentOcrDiscoveryRed

```text
F                                                                        [100%]
================================== FAILURES ===================================
__________ test_document_provider_discovers_its_venv_local_ocr_data ___________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1942/test_document_provider_discove0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x000002226DCE31A0>

    def test_document_provider_discovers_its_venv_local_ocr_data(tmp_path, monkeypatch):
        monkeypatch.setattr(sys, "prefix", str(tmp_path))
        data = tmp_path / "share" / "tessdata"
        data.mkdir(parents=True)
        (data / "eng.traineddata").write_bytes(b"fixture-presence-only")
        provider = DocumentProvider(PdfFetcher(b""))
>       assert provider.tessdata_directory == str(data)
E       AssertionError: assert None == 'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott\\pytest-1942\\test_document_provider_discove0\\share\\tessdata'
E        +  where None = <halo_research_gateway.providers.document_extract.DocumentProvider object at 0x000002226DCE3710>.tessdata_directory
E        +  and   'C:\\Users\\scott\\AppData\\Local\\Temp\\pytest-of-scott\\pytest-1942\\test_document_provider_discove0\\share\\tessdata' = str(WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1942/test_document_provider_discove0/share/tessdata'))

tests\unit\test_document_options.py:263: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_document_options.py::test_document_provider_discovers_its_venv_local_ocr_data
1 failed, 16 deselected in 0.94s
```

## ocrInstallerRed

```text
FFFF                                                                     [100%]
================================== FAILURES ===================================
_________ test_installs_only_verified_bytes_and_reuses_existing_file __________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1943/test_installs_only_verified_by0')

    def test_installs_only_verified_bytes_and_reuses_existing_file(tmp_path):
        calls = []
    
        def fetch(url, max_bytes):
            calls.append((url, max_bytes))
            return PAYLOAD
    
        destination = tmp_path / "tessdata" / "eng.traineddata"
        install_asset(destination, URL, DIGEST, len(PAYLOAD), fetch)
>       assert destination.exists(), "verified OCR data was not installed"
E       AssertionError: verified OCR data was not installed
E       assert False
E        +  where False = exists()
E        +    where exists = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1943/test_installs_only_verified_by0/tessdata/eng.traineddata').exists

tests\unit\test_ocr_data.py:21: AssertionError
_____________ test_rejects_download_hash_or_size_mismatch[wrong] ______________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1943/test_rejects_download_hash_or_0')
payload = b'wrong'

    @pytest.mark.parametrize("payload", [b"wrong", PAYLOAD + b"oversize"])
    def test_rejects_download_hash_or_size_mismatch(tmp_path, payload):
        destination = tmp_path / "eng.traineddata"
>       with pytest.raises(RuntimeError, match="OCR_DATA_INTEGRITY_ERROR"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE RuntimeError

tests\unit\test_ocr_data.py:30: Failed
_ test_rejects_download_hash_or_size_mismatch[deterministic OCR data fixtureoversize] _

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1943/test_rejects_download_hash_or_1')
payload = b'deterministic OCR data fixtureoversize'

    @pytest.mark.parametrize("payload", [b"wrong", PAYLOAD + b"oversize"])
    def test_rejects_download_hash_or_size_mismatch(tmp_path, payload):
        destination = tmp_path / "eng.traineddata"
>       with pytest.raises(RuntimeError, match="OCR_DATA_INTEGRITY_ERROR"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE RuntimeError

tests\unit\test_ocr_data.py:30: Failed
_____________ test_preserves_unrecognized_existing_language_data ______________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1943/test_preserves_unrecognized_ex0')

    def test_preserves_unrecognized_existing_language_data(tmp_path):
        destination = tmp_path / "eng.traineddata"
        destination.write_bytes(b"operator-owned alternate OCR model")
>       with pytest.raises(RuntimeError, match="OCR_DATA_EXISTS_WITH_DIFFERENT_HASH"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE RuntimeError

tests\unit\test_ocr_data.py:38: Failed
=========================== short test summary info ===========================
FAILED tests/unit/test_ocr_data.py::test_installs_only_verified_bytes_and_reuses_existing_file
FAILED tests/unit/test_ocr_data.py::test_rejects_download_hash_or_size_mismatch[wrong]
FAILED tests/unit/test_ocr_data.py::test_rejects_download_hash_or_size_mismatch[deterministic OCR data fixtureoversize]
FAILED tests/unit/test_ocr_data.py::test_preserves_unrecognized_existing_language_data
4 failed in 0.16s
```

## ocrInstallerWiringRed

```text
F                                                                        [100%]
================================== FAILURES ===================================
_________________ test_full_installer_invokes_local_ocr_setup _________________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1944/test_full_installer_invokes_lo0')

    @pytest.mark.skipif(os.name != "nt", reason="Windows installer")
    def test_full_installer_invokes_local_ocr_setup(tmp_path):
        root = tmp_path / "fixture-repo"
        (root / "scripts").mkdir(parents=True)
        (root / "config").mkdir()
        (root / "skills" / "halo-research").mkdir(parents=True)
        (root / "config" / "config.example.toml").write_text("[server]\nport = 8765\n", encoding="utf-8")
        (root / "skills" / "halo-research" / "SKILL.md").write_text("fixture", encoding="utf-8")
        (root / "scripts" / "Invoke-QualityGate.ps1").write_text("$global:LASTEXITCODE = 0\n", encoding="utf-8")
        source = Path(__file__).resolve().parents[2] / "scripts" / "Install-HaloResearch.ps1"
        shutil.copyfile(source, root / "scripts" / source.name)
        wrapper = tmp_path / "wrapper.ps1"
        wrapper.write_text(
            "$ErrorActionPreference = 'Stop'\n"
            "function global:uv { ($args -join ' ') | Add-Content -LiteralPath $env:HALO_OCR_INSTALL_TRACE; $global:LASTEXITCODE = 0 }\n"
            "function global:git { $global:LASTEXITCODE = 0 }\n"
            "& (Join-Path $env:HALO_OCR_INSTALL_REPO 'scripts\\Install-HaloResearch.ps1')\n", encoding="utf-8"
        )
        trace = tmp_path / "calls.txt"
        env = dict(os.environ, LOCALAPPDATA=str(tmp_path / "appdata"), USERPROFILE=str(tmp_path / "user"),
                   HALO_OCR_INSTALL_TRACE=str(trace), HALO_OCR_INSTALL_REPO=str(root))
        result = subprocess.run(["pwsh", "-NoProfile", "-File", str(wrapper)], env=env,
                                capture_output=True, text=True, timeout=15)
        assert result.returncode == 0, result.stdout + result.stderr
>       assert "run --locked python -m halo_research_gateway.ocr_data" in trace.read_text(encoding="utf-8-sig")
E       AssertionError: assert 'run --locked python -m halo_research_gateway.ocr_data' in 'sync --locked --extra crawl --extra documents --group dev\n'
E        +  where 'sync --locked --extra crawl --extra documents --group dev\n' = read_text(encoding='utf-8-sig')
E        +    where read_text = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1944/test_full_installer_invokes_lo0/calls.txt').read_text

tests\unit\test_ocr_data.py:71: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_ocr_data.py::test_full_installer_invokes_local_ocr_setup
1 failed, 4 deselected in 0.98s
```

## ocrSetupGreen

```text
......................                                                   [100%]
22 passed in 3.16s
```

## documentNativeOcr

```text
....                                                                     [100%]
4 passed in 2.27s
```

## documentFalsificationRed

```text
FFFF.                                                                    [100%]
================================== FAILURES ===================================
____________ test_ocr_refuses_an_oversized_raster_before_rendering ____________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1947/test_ocr_refuses_an_oversized_0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000026ADD256FF0>

    def test_ocr_refuses_an_oversized_raster_before_rendering(tmp_path, monkeypatch):
        (tmp_path / "eng.traineddata").write_bytes(b"fixture")
        monkeypatch.setattr(pymupdf, "get_tessdata", lambda *args: str(tmp_path))
        invoked = []
        monkeypatch.setattr(pymupdf.Page, "get_textpage_ocr", lambda *args, **kwargs: invoked.append(True))
        monkeypatch.setattr(pymupdf.Page, "get_text", lambda *args, **kwargs: "fixture text")
        with pymupdf.open() as document:
            document.new_page(width=20_000, height=20_000)
            payload = document.tobytes()
>       with pytest.raises(RuntimeError, match="OCR_PAGE_TOO_LARGE"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE RuntimeError

tests\unit\test_document_options.py:281: Failed
______________ test_non_pdf_does_not_silently_accept_forced_ocr _______________

    async def test_non_pdf_does_not_silently_accept_forced_ocr():
>       with pytest.raises(ValueError, match="DOCUMENT_OCR_REQUIRES_PDF"):
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       Failed: DID NOT RAISE ValueError

tests\unit\test_document_options.py:295: Failed
____________ test_non_pdf_fallback_discloses_lack_of_pdf_structure ____________

    async def test_non_pdf_fallback_discloses_lack_of_pdf_structure():
        result = await DocumentProvider(TextFetcher()).extract("https://example.org/source.txt")
        assert result.items[0].content == "plain source"
>       assert "DOCUMENT_TEXT_FALLBACK" in result.warnings
E       AssertionError: assert 'DOCUMENT_TEXT_FALLBACK' in []
E        +  where [] = ProviderResult(provider='direct-http', items=[EvidenceItem(url='https://example.org/source.txt', retrieved_at='2026-09...content='plain source', metadata={})], warnings=[], available=None, cache_hit=False, cache_age_seconds=0, cache_key='').warnings

tests\unit\test_document_options.py:302: AssertionError
___________ test_write_failure_cleans_only_installer_temporary_file ___________

tmp_path = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1947/test_write_failure_cleans_only0')
monkeypatch = <_pytest.monkeypatch.MonkeyPatch object at 0x0000026ADD282990>

    def test_write_failure_cleans_only_installer_temporary_file(tmp_path, monkeypatch):
        def failed_flush(descriptor):
            raise OSError("fixture disk error")
    
        monkeypatch.setattr(os, "fsync", failed_flush)
        with pytest.raises(OSError, match="fixture disk error"):
            install_asset(tmp_path / "eng.traineddata", URL, DIGEST, len(PAYLOAD), lambda *args: PAYLOAD)
>       assert not list(tmp_path.glob(".ocr-*")), "failed write leaked an installer temporary file"
E       AssertionError: failed write leaked an installer temporary file
E       assert not [WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1947/test_write_failure_cleans_only0/.ocr-76pqbtlr')]
E        +  where [WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1947/test_write_failure_cleans_only0/.ocr-76pqbtlr')] = list(<generator object Path.glob at 0x0000026ADD314AE0>)
E        +    where <generator object Path.glob at 0x0000026ADD314AE0> = glob('.ocr-*')
E        +      where glob = WindowsPath('C:/Users/scott/AppData/Local/Temp/pytest-of-scott/pytest-1947/test_write_failure_cleans_only0').glob

tests\unit\test_ocr_data.py:88: AssertionError
=========================== short test summary info ===========================
FAILED tests/unit/test_document_options.py::test_ocr_refuses_an_oversized_raster_before_rendering
FAILED tests/unit/test_document_options.py::test_non_pdf_does_not_silently_accept_forced_ocr
FAILED tests/unit/test_document_options.py::test_non_pdf_fallback_discloses_lack_of_pdf_structure
FAILED tests/unit/test_ocr_data.py::test_write_failure_cleans_only_installer_temporary_file
4 failed, 1 passed, 22 deselected in 0.99s
```

## documentFalsificationGreen

```text
2 files reformatted, 2 files left unchanged
...............................                                          [100%]
31 passed in 5.30s
```

## documentFullGateStart

```text
[GATE] lock check
Resolved 130 packages in 1ms
[GATE] format
86 files already formatted
[GATE] lint
All checks passed!
[GATE] unit and fixture tests
........................................................................ [ 28%]
...........................................```

## documentFullGateEnd

```text
............................. [ 56%]
...............................................```

## documentFullGateFinal

```text
......................... [ 85%]
......................................                                   [100%]
254 passed in 49.42s
[GATE] skill package
halo-research skill package valid
[GATE] PASS (Commit)
```

