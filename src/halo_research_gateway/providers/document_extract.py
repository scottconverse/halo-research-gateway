"""Bounded PDF extraction with page-level citation metadata."""

from __future__ import annotations

import asyncio
import contextlib
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

from ..clock import SystemClock, rfc3339
from ..models import EvidenceItem, ProviderResult
from ..security import is_sensitive_url, redact_url

MAX_PAGES = 300
MAX_INPUT_BYTES = 20_971_520
MAX_OUTPUT_BYTES = 2_097_152
MAX_ITEM_CHARS = 50_000
MAX_DOCUMENT_CHARS = 400_000
MAX_TABLES = 50
OCR_DPI = 150
MAX_OCR_PIXELS = 20_000_000


class DocumentProvider:
    def __init__(self, fetcher, clock=None) -> None:
        self.fetcher = fetcher
        self.clock = clock or SystemClock()
        self.timeout_seconds = 120.0
        bundled = Path(sys.prefix) / "share" / "tessdata"
        self.tessdata_directory: str | None = str(bundled) if (bundled / "eng.traineddata").is_file() else None
        self._workers: set = set()

    async def extract(
        self, url: str, pages: str | None = None, *, include_tables: bool = True, ocr: str = "auto"
    ) -> ProviderResult:
        if type(include_tables) is not bool or ocr not in {"auto", "never", "force"}:
            raise ValueError("DOCUMENT_OPTIONS_INVALID")
        if pages is not None and (not isinstance(pages, str) or len(pages) > 1024):
            raise ValueError("PAGE_SELECTION_INVALID")
        current_url, target, headers, payload = await self.fetcher.download(
            url, "application/pdf,application/octet-stream;q=0.8"
        )
        media = headers.get("content-type", "").split(";", 1)[0].lower()
        if media != "application/pdf" and not payload.startswith(b"%PDF-"):
            if ocr == "force":
                raise ValueError("DOCUMENT_OCR_REQUIRES_PDF")
            if pages is not None:
                raise ValueError("DOCUMENT_PAGES_REQUIRE_PDF")
            result = await self.fetcher.fetch(url)
            result.warnings.append("DOCUMENT_TEXT_FALLBACK")
            return result
        if len(payload) > MAX_INPUT_BYTES:
            raise ValueError("CONTENT_TOO_LARGE")
        parsed = await self._parse(payload, pages, include_tables, ocr)
        if is_sensitive_url(url) or is_sensitive_url(current_url):
            current_url = redact_url(current_url)
            parsed["warnings"].append("SENSITIVE_URL_NOT_CACHED")
        now = rfc3339(self.clock.utcnow())
        items = [
            EvidenceItem(
                url=f"{current_url.split('#', 1)[0]}#page={entry['page']}",
                retrieved_at=now,
                source=target.host,
                title=f"Page {entry['page']}" + (" table" if entry["kind"] == "table" else ""),
                content=entry["content"],
                metadata={key: value for key, value in entry.items() if key != "content"}
                | {"document_pages": parsed["page_count"]},
            )
            for entry in parsed["items"]
        ]
        return ProviderResult("pymupdf", items, parsed["warnings"], len(items))

    async def _parse(self, payload, pages, include_tables, ocr):
        request = (
            json.dumps(
                {"pages": pages, "include_tables": include_tables, "ocr": ocr, "tessdata": self.tessdata_directory}
            ).encode()
            + b"\n"
            + payload
        )
        spawning = asyncio.create_task(
            asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "halo_research_gateway.providers.document_extract",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
                **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
            )
        )
        process = None
        try:
            process = await asyncio.shield(spawning)
            self._workers.add(process)
            async with asyncio.timeout(self.timeout_seconds):
                output, _ = await process.communicate(request)
            if len(output) > MAX_OUTPUT_BYTES:
                raise RuntimeError("CONTENT_TOO_LARGE")
            if process.returncode != 0:
                raise RuntimeError("DOCUMENT_WORKER_FAILED")
            value = json.loads(output)
            if value.get("error"):
                raise RuntimeError(value["error"])
            return value
        except TimeoutError:
            raise RuntimeError("DOCUMENT_EXTRACTION_TIMEOUT") from None
        finally:
            if process is None:
                # Cancellation while Windows is creating the process must still
                # obtain its handle and close that exact child, never orphan it.
                with contextlib.suppress(Exception):
                    process = await _finish_cleanup(spawning)
            if process is not None:
                try:
                    if process.returncode is None:
                        with contextlib.suppress(ProcessLookupError):
                            process.kill()
                    await _finish_cleanup(asyncio.create_task(process.communicate()))
                finally:
                    self._workers.discard(process)


async def _finish_cleanup(task):
    # Called only during finally: retain cleanup even if the caller cancels again.
    while not task.done():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            continue
    return task.result()


def _table_markdown(rows: list[list], warnings: list[str]) -> str:
    if not rows:
        return ""
    width = min(30, max(len(row) for row in rows[:100]))
    if len(rows) > 100 or any(len(row) > 30 for row in rows[:100]):
        warnings.append("DOCUMENT_CONTENT_TRUNCATED")
    lines = []
    for index, row in enumerate(rows[:100]):
        cells = []
        for cell in row[:width]:
            value = str(cell if cell is not None else "")
            if len(value) > 500:
                warnings.append("DOCUMENT_CONTENT_TRUNCATED")
            cells.append(value[:500].replace("|", "\\|").replace("\n", " "))
        cells.extend([""] * (width - len(cells)))
        lines.append("| " + " | ".join(cells) + " |")
        if index == 0:
            lines.append("| " + " | ".join(["---"] * width) + " |")
    return "\n".join(lines)


def _page_selection(spec: str | None, count: int) -> list[int]:
    if not spec:
        return list(range(min(count, MAX_PAGES)))
    if len(spec) > 1024 or not re.fullmatch(
        r"\s*[0-9]+(?:\s*-\s*[0-9]+)?(?:\s*,\s*[0-9]+(?:\s*-\s*[0-9]+)?)*\s*", spec
    ):
        raise ValueError("PAGE_SELECTION_INVALID")
    result: set[int] = set()
    for part in spec.split(","):
        if "-" in part:
            start, end = (int(x) for x in part.split("-", 1))
        else:
            start = end = int(part)
        if start < 1 or end < start or end > count:
            raise ValueError("PAGE_SELECTION_INVALID")
        if end - start + 1 > MAX_PAGES:
            raise ValueError("CONTENT_TOO_LARGE")
        result.update(range(start - 1, end))
        if len(result) > MAX_PAGES:
            raise ValueError("CONTENT_TOO_LARGE")
    return sorted(result)


def _parse_pdf(payload, options):
    import pymupdf

    warnings, items = [], []
    remaining_chars, table_count = MAX_DOCUMENT_CHARS, 0

    def append_item(item):
        nonlocal remaining_chars
        content = item["content"]
        bounded = content[: min(MAX_ITEM_CHARS, remaining_chars)]
        if len(bounded) < len(content):
            warnings.append("DOCUMENT_CONTENT_TRUNCATED")
            item["truncated"] = True
        remaining_chars -= len(bounded)
        items.append(item | {"content": bounded})

    with pymupdf.open(stream=payload, filetype="pdf") as document:
        if document.needs_pass:
            raise RuntimeError("DOCUMENT_PASSWORD_REQUIRED")
        selected = _page_selection(options["pages"], len(document))
        if not options["pages"] and len(document) > MAX_PAGES:
            warnings.append("DOCUMENT_PAGE_LIMIT_REACHED")
        for number in selected:
            if remaining_chars == 0:
                warnings.append("DOCUMENT_CHAR_LIMIT_REACHED")
                break
            page = document[number]
            text = page.get_text("text")
            ocr_state = "not_needed" if options["ocr"] != "never" else "disabled"
            image_area = any(
                pymupdf.Rect(info["bbox"]).get_area() >= page.rect.get_area() * 0.2 for info in page.get_image_info()
            )
            if options["ocr"] == "force" or (options["ocr"] == "auto" and (not text.strip() or image_area)):
                pixels = math.ceil(page.rect.width * OCR_DPI / 72) * math.ceil(page.rect.height * OCR_DPI / 72)
                try:
                    if pixels > MAX_OCR_PIXELS:
                        raise RuntimeError("OCR_PAGE_TOO_LARGE")
                    tessdata = pymupdf.get_tessdata(options["tessdata"])
                    if not (Path(tessdata) / "eng.traineddata").is_file():
                        raise RuntimeError("OCR_UNAVAILABLE")
                except Exception as exc:
                    code = "OCR_PAGE_TOO_LARGE" if str(exc) == "OCR_PAGE_TOO_LARGE" else "OCR_UNAVAILABLE"
                    if options["ocr"] == "force":
                        raise RuntimeError(code) from None
                    warnings.append(code)
                    ocr_state = "unavailable"
                else:
                    try:
                        textpage = page.get_textpage_ocr(
                            language="eng", dpi=OCR_DPI, full=options["ocr"] == "force", tessdata=tessdata
                        )
                        text = page.get_text("text", textpage=textpage)
                        ocr_state = "performed"
                    except Exception:
                        if options["ocr"] == "force":
                            raise RuntimeError("OCR_FAILED") from None
                        warnings.append("OCR_FAILED")
                        ocr_state = "failed"
            append_item({"page": number + 1, "kind": "text", "content": text, "ocr": ocr_state})
            if options["include_tables"]:
                for index, table in enumerate(page.find_tables().tables, 1):
                    if table_count >= MAX_TABLES:
                        warnings.append("TABLE_LIMIT_REACHED")
                        break
                    if remaining_chars == 0:
                        warnings.append("DOCUMENT_CHAR_LIMIT_REACHED")
                        break
                    table_count += 1
                    append_item(
                        {
                            "page": number + 1,
                            "kind": "table",
                            "table": index,
                            "content": _table_markdown(table.extract(), warnings),
                        }
                    )
        if not any(item["content"].strip() for item in items):
            raise RuntimeError(
                next(
                    (code for code in warnings if code in {"OCR_UNAVAILABLE", "OCR_PAGE_TOO_LARGE", "OCR_FAILED"}),
                    "NO_DOCUMENT_TEXT",
                )
            )
        return {"page_count": len(document), "items": items, "warnings": list(dict.fromkeys(warnings))}


def _worker_main():
    # No document URL/path, credentials or raw parser diagnostics enter the protocol.
    try:
        header = sys.stdin.buffer.readline(16_385)
        if len(header) > 16_384:
            raise RuntimeError("DOCUMENT_OPTIONS_INVALID")
        options = json.loads(header)
        payload = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
        if len(payload) > MAX_INPUT_BYTES:
            raise RuntimeError("CONTENT_TOO_LARGE")
        with contextlib.redirect_stdout(sys.stderr):
            result = _parse_pdf(payload, options)
    except ImportError:
        result = {"error": "DOCUMENT_PARSER_UNAVAILABLE"}
    except Exception as exc:
        known = {
            "CONTENT_TOO_LARGE",
            "PAGE_SELECTION_INVALID",
            "DOCUMENT_OPTIONS_INVALID",
            "DOCUMENT_PASSWORD_REQUIRED",
            "OCR_UNAVAILABLE",
            "OCR_FAILED",
            "OCR_PAGE_TOO_LARGE",
            "NO_DOCUMENT_TEXT",
        }
        result = {"error": str(exc) if str(exc) in known else "DOCUMENT_INVALID"}
    encoded = json.dumps(result, ensure_ascii=False).encode("utf-8")
    if len(encoded) > MAX_OUTPUT_BYTES:
        encoded = b'{"error":"CONTENT_TOO_LARGE"}'
    sys.stdout.buffer.write(encoded)


if __name__ == "__main__":
    _worker_main()
