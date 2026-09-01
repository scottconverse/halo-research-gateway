# Gate-authored acceptance tests (frozen). The worker implements src/ to make
# these pass and may not modify this file. Authored by the coordinator 2026-08-26.
#
# Unit under test: halo_research_gateway.envelope — the common result envelope
# and character-budget pagination of spec v1.3 §9.6.
#
# Public API this file pins:
#   build_envelope(tool, provider, request_id, requested_at, completed_at,
#                  items, requested, available, char_budget,
#                  cache_hit=False, cache_age_seconds=0, cache_key="",
#                  cursor=None, warnings=None) -> dict
#   error_envelope(tool, provider, request_id, code, message,
#                  partial_items=None, retry_after_seconds=None) -> dict
#   SCHEMA_VERSION: str
import json

from halo_research_gateway.envelope import (
    SCHEMA_VERSION,
    build_envelope,
    error_envelope,
)
from halo_research_gateway.service import HaloService

REQ = "2026-08-26T01:00:00Z"
DONE = "2026-08-26T01:00:01Z"


def make_items(n, content_len=200):
    return [
        {
            "title": f"item {i}",
            "url": f"https://example.com/{i}",
            "published_at": None,
            "retrieved_at": REQ,
            "source": "example.com",
            "snippet": None,
            "content": "x" * content_len,
        }
        for i in range(n)
    ]


def build(items, requested=None, available=None, char_budget=6000, cursor=None):
    return build_envelope(
        tool="web_search",
        provider="exa-anonymous",
        request_id="11111111-1111-1111-1111-111111111111",
        requested_at=REQ,
        completed_at=DONE,
        items=items,
        requested=requested if requested is not None else len(items),
        available=available if available is not None else len(items),
        char_budget=char_budget,
        cursor_state=json.loads(cursor) if cursor else None,
        encode_cursor=lambda value: json.dumps(value, separators=(",", ":")),
    )


def test_envelope_has_required_shape():
    env = build(make_items(2))
    for key in (
        "schema_version",
        "ok",
        "request_id",
        "tool",
        "provider",
        "requested_at",
        "completed_at",
        "cache",
        "coverage",
        "page",
        "items",
        "warnings",
        "retry_after_seconds",
    ):
        assert key in env, f"missing top-level key: {key}"
    assert env["schema_version"] == SCHEMA_VERSION
    assert env["ok"] is True
    assert set(env["cache"]) >= {"hit", "age_seconds", "key"}
    assert set(env["coverage"]) >= {
        "requested",
        "available",
        "returned_this_page",
        "returned_cumulative",
        "complete",
    }
    assert set(env["page"]) >= {
        "number",
        "serialized_chars",
        "next_cursor",
        "snapshot_expires_at",
    }


def test_coverage_counts_reflect_the_page():
    env = build(make_items(3), requested=6, available=3)
    assert env["coverage"]["requested"] == 6
    assert env["coverage"]["available"] == 3
    assert env["coverage"]["returned_this_page"] == len(env["items"])
    assert env["coverage"]["returned_cumulative"] == len(env["items"])


def test_page_respects_char_budget():
    env = build(make_items(50), char_budget=3000)
    assert env["page"]["serialized_chars"] <= 3000
    assert env["page"]["serialized_chars"] == len(json.dumps(env, indent=2, ensure_ascii=False))
    assert 0 < len(env["items"]) < 50


def test_truncated_page_emits_cursor_and_warning():
    env = build(make_items(50), char_budget=3000)
    assert env["page"]["next_cursor"], "a truncated page must carry a continuation cursor"
    assert "RESULT_TRUNCATED" in env["warnings"]


def test_complete_page_has_no_cursor():
    env = build(make_items(2), char_budget=6000)
    assert env["page"]["next_cursor"] is None
    assert env["warnings"] == []
    assert env["coverage"]["complete"] is True


def test_cursor_resumes_without_gaps_or_duplicates():
    items = make_items(40)
    seen, cursor, pages = [], None, 0
    while True:
        env = build(items, char_budget=3000, cursor=cursor)
        assert env["page"]["number"] == pages + 1
        seen.extend(i["url"] for i in env["items"])
        pages += 1
        cursor = env["page"]["next_cursor"]
        assert pages < 25, "pagination did not terminate"
        if cursor is None:
            break
    assert seen == [i["url"] for i in items], "pages must cover every item, in order, exactly once"
    assert pages > 1
    assert len(seen) == len(set(seen))


def test_cumulative_count_grows_across_pages():
    items = make_items(40)
    first = build(items, char_budget=3000)
    second = build(items, char_budget=3000, cursor=first["page"]["next_cursor"])
    assert second["coverage"]["returned_cumulative"] == (
        first["coverage"]["returned_this_page"] + second["coverage"]["returned_this_page"]
    )


def test_every_item_carries_its_own_citation():
    # Spec §9.6: every page must stand alone; no citation may live only on
    # another page.
    env = build(make_items(30), char_budget=3000)
    for item in env["items"]:
        assert item["url"], "every item needs a canonical URL on its own page"
        assert item["retrieved_at"], "every item needs a retrieval date on its own page"


def test_error_envelope_shape():
    env = error_envelope(
        tool="web_fetch",
        provider="http",
        request_id="22222222-2222-2222-2222-222222222222",
        code="UNSAFE_URL",
        message="blocked by URL policy",
    )
    assert env["ok"] is False
    assert env["schema_version"] == SCHEMA_VERSION
    assert env["error"]["code"] == "UNSAFE_URL"
    assert env["coverage"]["complete"] is False
    assert env["items"] == []


def test_error_envelope_never_leaks_a_traceback():
    # Forbidden outcome: exception internals must never reach model-facing output.
    try:
        raise ValueError("secret internal detail")
    except ValueError as exc:
        env = error_envelope(
            tool="web_fetch",
            provider="http",
            request_id="33333333-3333-3333-3333-333333333333",
            code="UPSTREAM_ERROR",
            message=f"upstream failed: {type(exc).__name__}",
        )
    blob = json.dumps(env)
    assert "Traceback" not in blob
    assert "secret internal detail" not in blob
    assert 'File "' not in blob


def test_envelope_is_json_serializable():
    env = build(make_items(5))
    json.dumps(env)  # must not raise


def test_long_single_source_is_chunked_below_dsh_page_limit():
    items = make_items(1, content_len=10_000)
    chunks = HaloService._chunk_items(items, 2000)
    env = build(chunks, requested=1, available=1, char_budget=2000)
    assert env["page"]["serialized_chars"] <= 2000
    assert env["page"]["next_cursor"]
    assert env["items"][0]["url"] == items[0]["url"]
