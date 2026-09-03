"""Every pageable MCP reader must accept its signed cursor without seed arguments."""

import json
from types import SimpleNamespace

import pytest
from mcp.server.mcpserver import Context

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult

READERS = (
    "web_search",
    "web_fetch",
    "web_crawl",
    "reddit_search",
    "reddit_thread",
    "document_extract",
    "deep_research",
    "github_research",
    "transcript_fetch",
    "community_search",
    "community_thread",
    "local_fetch",
    "local_crawl",
)
REPAIRED = {
    "deep_research": ("question", "INVALID_DEEP_RESEARCH_LIMITS"),
    "transcript_fetch": ("url", "URL_REQUIRED"),
    "community_search": ("query", "INVALID_COMMUNITY_QUERY"),
    "community_thread": ("url", "URL_REQUIRED"),
}


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


async def dispatch(app, tool, arguments):
    context = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
        mcp_server=app.state.mcp_server,
    )
    rejected = None
    try:
        result = await app.state.mcp_server._tool_manager.call_tool(tool, arguments, context)
    except Exception as exc:
        rejected = str(exc)
        result = None
    assert rejected is None, f"MCP rejected a valid continuation or missing-input envelope: {rejected}"
    return result


@pytest.mark.parametrize("tool", REPAIRED)
async def test_schema_does_not_require_original_selector_for_continuation(app, tool):
    definitions = {entry.name: entry for entry in await app.state.mcp_server.list_tools()}
    selector, _ = REPAIRED[tool]
    assert selector not in definitions[tool].input_schema.get("required", []), (
        f"{tool} advertises a cursor but requires {selector} before dispatch"
    )


@pytest.mark.parametrize("tool", READERS)
async def test_cursor_only_dispatch_returns_all_retained_evidence_for_each_reader(app, tool):
    body = "Retained source evidence must survive every cursor-only call. " * 100
    result = ProviderResult(
        "contract-fixture",
        [EvidenceItem(url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content=body)],
    )
    page = app.state.halo_service._envelope(tool, result, 2000)
    content, pages = "", 0
    assert page["page"]["next_cursor"]
    while True:
        assert page["ok"] and page["tool"] == tool
        assert page["provider"] == "contract-fixture"
        assert len(json.dumps(page, indent=2, ensure_ascii=False)) == page["page"]["serialized_chars"] <= 2000
        content += "".join(item.get("content") or "" for item in page["items"])
        pages += 1
        cursor = page["page"]["next_cursor"]
        if not cursor:
            break
        assert pages < 100
        page = await dispatch(app, tool, {"cursor": cursor, "max_chars": 2000})
    assert content == body
    assert pages > 1


@pytest.mark.parametrize("tool", REPAIRED)
async def test_missing_selector_without_cursor_still_returns_policy_error(app, tool):
    result = await dispatch(app, tool, {})
    assert result["ok"] is False
    assert result["error"]["code"] == REPAIRED[tool][1]


@pytest.mark.parametrize("tool", REPAIRED)
async def test_invalid_cursor_without_selector_reaches_cursor_validation(app, tool):
    result = await dispatch(app, tool, {"cursor": "not-a-valid-cursor"})
    assert result["ok"] is False
    assert result["error"]["code"] == "CURSOR_INVALID"


@pytest.mark.parametrize("tool", REPAIRED)
async def test_direct_service_also_accepts_cursor_without_selector(app, tool):
    first = app.state.halo_service._envelope(
        tool,
        ProviderResult(
            "contract-fixture",
            [
                EvidenceItem(
                    url="https://example.org/research", retrieved_at="2026-09-03T03:00:00Z", content="evidence " * 500
                )
            ],
        ),
        2000,
    )
    rejected = None
    try:
        resumed = await getattr(app.state.halo_service, tool)(cursor=first["page"]["next_cursor"], max_chars=2000)
    except TypeError as exc:
        rejected = str(exc)
        resumed = None
    assert rejected is None, f"Service still requires an irrelevant seed argument: {rejected}"
    assert resumed["ok"] and resumed["page"]["number"] == 2
