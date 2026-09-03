"""Document request fidelity and real local PDF extraction regressions."""

import asyncio
import sys
from types import SimpleNamespace

import pymupdf
import pytest
from mcp.server.mcpserver import Context

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.providers.document_extract import DocumentProvider, _page_selection, _parse_pdf

URL = "https://example.org/research.pdf"


def application_at(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return create_application(config)


async def call_document(app, **options):
    context = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
        mcp_server=app.state.mcp_server,
    )
    return await app.state.mcp_server._tool_manager.call_tool("document_extract", {"url": URL, **options}, context)


async def test_mcp_document_options_reach_service(tmp_path):
    app = application_at(tmp_path)
    seen = []

    async def extract(*args, **kwargs):
        seen.append(kwargs)
        return {"ok": True}

    app.state.halo_service.document_extract = extract
    try:
        await call_document(app, pages="2", include_tables=False, ocr="force")
        assert seen[0].get("include_tables") is False
        assert seen[0].get("ocr") == "force"
    finally:
        await app.state.halo_service.close()


async def test_document_options_have_distinct_provider_calls_and_cache_entries(tmp_path):
    app = application_at(tmp_path)
    seen = []

    async def extract(url, pages, **options):
        seen.append(options)
        return ProviderResult(
            "fixture", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="evidence")]
        )

    app.state.halo_service.documents.extract = extract
    try:
        for include_tables, ocr in [(False, "never"), (True, "never"), (True, "force")]:
            result = await call_document(app, include_tables=include_tables, ocr=ocr)
            assert result["ok"], result
        assert len(seen) == 3, "different extraction options reused the same cached result"
        assert [(value["include_tables"], value["ocr"]) for value in seen] == [
            (False, "never"),
            (True, "never"),
            (True, "force"),
        ]
    finally:
        await app.state.halo_service.close()


def table_pdf():
    with pymupdf.open() as document:
        page = document.new_page(width=400, height=300)
        for x in (40, 190, 340):
            page.draw_line((x, 40), (x, 130))
        for y in (40, 70, 100, 130):
            page.draw_line((40, y), (340, y))
        for y, values in [(60, ("Source", "Count")), (90, ("Primary", "12")), (120, ("Community", "7"))]:
            for x, value in zip((50, 200), values, strict=True):
                page.insert_text((x, y), value)
        return document.tobytes()


class PdfFetcher:
    def __init__(self, payload):
        self.payload = payload

    async def download(self, url, accept):
        return URL, SimpleNamespace(host="example.org"), {"content-type": "application/pdf"}, self.payload


async def test_pdf_default_extracts_citable_table_structure():
    result = await DocumentProvider(PdfFetcher(table_pdf())).extract(URL)
    tables = [item for item in result.items if item.metadata.get("kind") == "table"]
    assert tables, "include_tables defaults true, but no structured table was returned"
    assert tables[0].url == URL + "#page=1"
    assert tables[0].metadata["page"] == 1
    assert "| Source | Count |" in tables[0].content
    assert "| Primary | 12 |" in tables[0].content
    assert "| Community | 7 |" in tables[0].content


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
    assert not opened_in_gateway, "PDF parser ran inside the shared Gateway process"
    assert result and "Primary" in result.items[0].content


async def test_forced_ocr_reports_missing_local_language_data(tmp_path):
    provider = DocumentProvider(PdfFetcher(table_pdf()))
    provider.tessdata_directory = str(tmp_path / "deliberately-missing-tessdata")
    with pytest.raises(RuntimeError, match="OCR_UNAVAILABLE"):
        await provider.extract(URL, ocr="force")


async def test_document_parse_has_a_real_deadline():
    provider = DocumentProvider(PdfFetcher(table_pdf()))
    provider.timeout_seconds = 0.001
    with pytest.raises(RuntimeError, match="DOCUMENT_EXTRACTION_TIMEOUT"):
        await provider.extract(URL)


@pytest.mark.parametrize("selection", ["0", "2-1", "9999", "1," * 600])
def test_invalid_or_overlong_page_selection_is_not_silently_accepted(selection):
    with pytest.raises(ValueError):
        _page_selection(selection, 5)


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
        assert children[0].returncode is not None, "cancel during spawn orphaned the parser process"
        assert not provider._workers
    finally:
        release.set()
        for child in children:
            if child.returncode is None:
                child.kill()
            await child.communicate()


async def test_repeated_cancel_finishes_worker_cleanup(monkeypatch):
    provider = DocumentProvider(PdfFetcher(table_pdf()))
    native_spawn = asyncio.create_subprocess_exec
    entered, cleaning, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    children = []

    async def instrumented_spawn(*args, **kwargs):
        child = await native_spawn(
            sys.executable, "-c", "import sys,time; sys.stdin.buffer.read(); time.sleep(60)", **kwargs
        )
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
        assert not provider._workers, "repeated cancellation abandoned worker cleanup"
        assert children[0].returncode is not None
    finally:
        release.set()
        for child in children:
            if child.returncode is None:
                child.kill()
            await child.communicate()


def test_table_count_and_size_are_bounded_with_warnings(monkeypatch):
    table = SimpleNamespace(extract=lambda: [["x" * 1000] * 40 for _ in range(150)])
    monkeypatch.setattr(pymupdf.Page, "find_tables", lambda *args, **kwargs: SimpleNamespace(tables=[table] * 60))
    result = _parse_pdf(table_pdf(), {"pages": None, "include_tables": True, "ocr": "never", "tessdata": None})
    tables = [item for item in result["items"] if item["kind"] == "table"]
    assert len(tables) <= 50
    assert all(len(item["content"]) <= 50_000 for item in tables)
    assert sum(len(item["content"]) for item in result["items"]) <= 400_000
    assert "DOCUMENT_CONTENT_TRUNCATED" in result["warnings"]
    assert "TABLE_LIMIT_REACHED" in result["warnings"] or "DOCUMENT_CHAR_LIMIT_REACHED" in result["warnings"]


def test_large_page_text_is_explicitly_partial(monkeypatch):
    monkeypatch.setattr(pymupdf.Page, "get_text", lambda *args, **kwargs: "research " * 10_000)
    result = _parse_pdf(table_pdf(), {"pages": None, "include_tables": False, "ocr": "never", "tessdata": None})
    assert len(result["items"][0]["content"]) <= 50_000
    assert "DOCUMENT_CONTENT_TRUNCATED" in result["warnings"]


async def test_include_tables_false_omits_structured_tables():
    result = await DocumentProvider(PdfFetcher(table_pdf())).extract(URL, include_tables=False, ocr="never")
    assert all(item.metadata["kind"] == "text" for item in result.items)
    assert "Primary" in result.items[0].content


async def test_page_selection_preserves_requested_citation():
    with pymupdf.open() as document:
        for number in (1, 2, 3):
            document.new_page().insert_text((40, 60), f"Evidence on page {number}")
        payload = document.tobytes()
    result = await DocumentProvider(PdfFetcher(payload)).extract(URL, "2", include_tables=False, ocr="never")
    assert len(result.items) == 1
    assert result.items[0].url == URL + "#page=2"
    assert "Evidence on page 2" in result.items[0].content
    assert result.items[0].metadata["document_pages"] == 3


def test_document_provider_discovers_its_venv_local_ocr_data(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "prefix", str(tmp_path))
    data = tmp_path / "share" / "tessdata"
    data.mkdir(parents=True)
    (data / "eng.traineddata").write_bytes(b"fixture-presence-only")
    provider = DocumentProvider(PdfFetcher(b""))
    assert provider.tessdata_directory == str(data)


def test_ocr_refuses_an_oversized_raster_before_rendering(tmp_path, monkeypatch):
    (tmp_path / "eng.traineddata").write_bytes(b"fixture")
    monkeypatch.setattr(pymupdf, "get_tessdata", lambda *args: str(tmp_path))
    invoked = []
    monkeypatch.setattr(pymupdf.Page, "get_textpage_ocr", lambda *args, **kwargs: invoked.append(True))
    monkeypatch.setattr(pymupdf.Page, "get_text", lambda *args, **kwargs: "fixture text")
    with pymupdf.open() as document:
        document.new_page(width=20_000, height=20_000)
        payload = document.tobytes()
    with pytest.raises(RuntimeError, match="OCR_PAGE_TOO_LARGE"):
        _parse_pdf(payload, {"pages": None, "include_tables": False, "ocr": "force", "tessdata": str(tmp_path)})
    assert not invoked


class TextFetcher:
    async def download(self, url, accept):
        return url, SimpleNamespace(host="example.org"), {"content-type": "text/plain"}, b"plain source"

    async def fetch(self, url):
        return ProviderResult(
            "direct-http", [EvidenceItem(url=url, retrieved_at="2026-09-03T00:00:00Z", content="plain source")]
        )


async def test_non_pdf_does_not_silently_accept_forced_ocr():
    with pytest.raises(ValueError, match="DOCUMENT_OCR_REQUIRES_PDF"):
        await DocumentProvider(TextFetcher()).extract("https://example.org/source.txt", ocr="force")


async def test_non_pdf_fallback_discloses_lack_of_pdf_structure():
    result = await DocumentProvider(TextFetcher()).extract("https://example.org/source.txt")
    assert result.items[0].content == "plain source"
    assert "DOCUMENT_TEXT_FALLBACK" in result.warnings


async def test_non_pdf_rejects_unsupported_page_selection():
    with pytest.raises(ValueError, match="DOCUMENT_PAGES_REQUIRE_PDF"):
        await DocumentProvider(TextFetcher()).extract("https://example.org/source.txt", pages="2")


def test_page_selection_does_not_silently_clip_missing_pages():
    with pytest.raises(ValueError, match="PAGE_SELECTION_INVALID"):
        _page_selection("1-6", 5)


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
            assert all("fixture-secret" not in item["url"] for item in result["items"])
            assert result["items"][0]["url"].endswith("#page=1")
            assert "SENSITIVE_URL_NOT_CACHED" in result["warnings"]
        assert len(calls) == 2, "a signed redirect was persisted in the document cache"
    finally:
        await app.state.halo_service.close()
