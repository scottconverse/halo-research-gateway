"""Explicit native OCR through the real MCP tool dispatcher and local reader.

Only the public-download boundary is replaced by generated PDF bytes. No document
is uploaded and no personal data is read. This is not live-upstream or DSH proof.
"""

from pathlib import Path
from types import SimpleNamespace

import pymupdf
import pytest
from mcp.server.mcpserver import Context

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig

URL = "https://example.org/fixture-scanned-research.pdf"
TEXT = "HALO LOCAL OCR EVIDENCE"


def scanned_pdf(mixed=False):
    with pymupdf.open() as source:
        page = source.new_page(width=500, height=200)
        page.insert_text((35, 70), TEXT, fontsize=24)
        page.insert_text((35, 110), "Primary sources: 12", fontsize=20)
        png = page.get_pixmap(dpi=150, alpha=False).tobytes("png")
    with pymupdf.open() as document:
        page = document.new_page(width=500, height=300)
        if mixed:
            page.insert_text((35, 35), "Native heading", fontsize=18)
        page.insert_image(pymupdf.Rect(0, 70, 500, 270), stream=png)
        return document.tobytes()


async def extract(tmp_path, payload, ocr):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    app = create_application(config)
    service = app.state.halo_service
    assert service.documents.tessdata_directory
    assert (Path(service.documents.tessdata_directory) / "eng.traineddata").is_file()

    async def download(url, accept):
        assert url == URL
        return url, SimpleNamespace(host="example.org"), {"content-type": "application/pdf"}, payload

    service.http.download = download
    context = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={})), mcp_server=app.state.mcp_server
    )
    try:
        result = await app.state.mcp_server._tool_manager.call_tool(
            "document_extract", {"url": URL, "ocr": ocr, "include_tables": False, "max_chars": 2000}, context
        )
        assert not service.documents._workers, "native parser process remains registered"
        return result
    finally:
        await service.close()


@pytest.mark.parametrize("mode", ["auto", "force"])
async def test_native_scanned_text_is_recognized_and_page_cited(tmp_path, mode):
    result = await extract(tmp_path, scanned_pdf(), mode)
    assert result["ok"], result
    assert TEXT in "\n".join(item.get("content", "") for item in result["items"])
    assert all(item["url"] == URL + "#page=1" for item in result["items"])
    assert result["items"][0]["metadata"]["ocr"] == "performed"


async def test_native_auto_preserves_text_and_reads_large_scanned_region(tmp_path):
    result = await extract(tmp_path, scanned_pdf(mixed=True), "auto")
    assert result["ok"], result
    content = "\n".join(item.get("content", "") for item in result["items"])
    assert "Native heading" in content
    assert TEXT in content


async def test_native_never_does_not_ocr_or_claim_empty_scan_success(tmp_path):
    result = await extract(tmp_path, scanned_pdf(), "never")
    assert not result["ok"], result
    assert result["error"]["code"] == "NO_DOCUMENT_TEXT"
