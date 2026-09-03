"""Lossless transcript text and timing metadata through bounded MCP pages."""

import copy
import json
from types import SimpleNamespace

import pytest
from mcp.server.mcpserver import Context

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult


@pytest.fixture
async def app(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    application = create_application(config)
    try:
        yield application
    finally:
        await application.state.halo_service.close()


async def call(app, arguments):
    context = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
        mcp_server=app.state.mcp_server,
    )
    return await app.state.mcp_server._tool_manager.call_tool("transcript_fetch", arguments, context)


def source(case):
    texts = [f"Caption {index}: research evidence with timing." for index in range(14)]
    if case == "long_caption":
        texts = ["A single long caption: " + '研究 🔎 \\ "\n' * 250]
    elif case == "many":
        texts = [f"Caption {index}." for index in range(200)]
    elif case == "empty":
        texts = ["", "Visible caption.", ""]
    elif case == "timing_only":
        texts = [""] * 25
    segments = [
        {"start_seconds": index * 1.5, "end_seconds": index * 1.5 + 1.25, "text": text}
        for index, text in enumerate(texts)
    ]
    body = "\n".join(f"[{row['start_seconds']} --> {row['end_seconds']}] {row['text']}" for row in segments)
    if case == "timing_only":
        body = ""
    result = ProviderResult(
        "public-transcript",
        [
            EvidenceItem(
                url="https://media.example/research",
                retrieved_at="2026-09-03T04:00:00Z",
                title="Research talk",
                snippet="Transcript summary.",
                content=body,
                metadata={
                    "language": "en",
                    "auto_generated": False,
                    "segment_count": len(segments),
                    "segments": segments,
                },
            )
        ],
        available=len(segments),
    )
    return result, body, segments


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
                if not segment["text"] and not segment.get("text_total"):
                    assert key not in segments, "Empty caption timing was repeated"
                previous = segments.setdefault(
                    key, {"start_seconds": segment["start_seconds"], "end_seconds": segment["end_seconds"], "text": ""}
                )
                assert (previous["start_seconds"], previous["end_seconds"]) == (
                    segment["start_seconds"],
                    segment["end_seconds"],
                )
                assert segment.get("text_offset", 0) == len(previous["text"]), "Caption fragment repeated or missing"
                previous["text"] += segment["text"]
                assert len(previous["text"]) <= segment.get("text_total", len(previous["text"]))
        pages += 1
        cursor = page["page"]["next_cursor"]
        if not cursor:
            break
        assert pages < 900, "Transcript pagination did not terminate"
        arguments = {"cursor": cursor}
    return "".join(body), "".join(snippet), [segments[key] for key in sorted(segments)], pages


@pytest.mark.parametrize("budget", [2000, 4000, 6000])
@pytest.mark.parametrize("case", ["short", "long_caption", "many", "empty", "timing_only"])
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
    if case != "empty" and not (case == "short" and budget == 6000) and not (case == "timing_only" and budget > 2000):
        assert pages > 1


async def test_previous_cursor_layout_is_rejected_instead_of_misreading_evidence(app):
    result = ProviderResult(
        "fixture",
        [
            EvidenceItem(
                url="https://media.example/research", retrieved_at="2026-09-03T04:00:00Z", content="text " * 1000
            )
        ],
    )
    service = app.state.halo_service
    page = service._envelope("transcript_fetch", result, 2000)
    old_state = service.cursors.decode(page["page"]["next_cursor"])
    old_state["v"] = 2
    old_cursor = service.cursors.encode(old_state)
    rejected = await call(app, {"cursor": old_cursor})
    assert not rejected["ok"], "Old cursor layout was silently interpreted by the new paginator"
    assert rejected["error"]["code"] == "CURSOR_EVICTED"
