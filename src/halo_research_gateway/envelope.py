import json

SCHEMA_VERSION = "1.5"


def build_envelope(
    tool,
    provider,
    request_id,
    requested_at,
    completed_at,
    items,
    requested,
    available,
    char_budget,
    cache_hit=False,
    cache_age_seconds=0,
    cache_key="",
    cursor_state=None,
    encode_cursor=None,
    warnings=None,
):
    """Page complete evidence, carrying unreturned prose in the cursor offset.

    The exact MCP JSON representation includes the cursor and all metadata.
    An item whose non-prose fields cannot fit fails explicitly; citations and
    evidence text are never silently deleted to meet a character budget.
    """
    state = cursor_state or {}
    index, offset = state.get("i", 0), state.get("o", 0)
    cumulative, number = state.get("c", 0), state.get("n", 1)

    def render(selected, next_index, next_offset=0):
        more = next_index < len(items)
        continuation = {"i": next_index, "c": cumulative + len(selected), "n": number + 1}
        if next_offset:
            continuation["o"] = next_offset
        value = {
            "schema_version": SCHEMA_VERSION,
            "ok": True,
            "request_id": request_id,
            "tool": tool,
            "provider": provider,
            "requested_at": requested_at,
            "completed_at": completed_at,
            "cache": {"hit": cache_hit, "age_seconds": cache_age_seconds, "key": cache_key},
            "coverage": {
                "requested": requested,
                "available": available,
                "returned_this_page": len(selected),
                "returned_cumulative": cumulative + len(selected),
                "complete": not more,
            },
            "page": {
                "number": number,
                "serialized_chars": 0,
                "next_cursor": encode_cursor(continuation) if more and encode_cursor else None,
                "snapshot_expires_at": None,
            },
            "retry_after_seconds": None,
            "items": selected,
            "warnings": sorted(set([*(warnings or []), *(["RESULT_TRUNCATED"] if more else [])])),
        }
        for _ in range(10):
            size = len(json.dumps(value, indent=2, ensure_ascii=False))
            if value["page"]["serialized_chars"] == size:
                break
            value["page"]["serialized_chars"] = size
        return value

    def prose_slice(item, start, count):
        copied = dict(item)
        snippet, content = item.get("snippet") or "", item.get("content") or ""
        end = start + count
        if snippet:
            copied["snippet"] = snippet[start : min(end, len(snippet))]
        if content:
            copied["content"] = content[max(0, start - len(snippet)) : max(0, end - len(snippet))]
        if start or count < len(snippet) + len(content):
            copied["metadata"] = dict(item.get("metadata") or {}) | {
                "text_offset": start,
                "text_total": len(snippet) + len(content),
            }
        return copied

    selected = []
    best = render([], index, offset)
    while index < len(items):
        item = items[index]
        total = len(item.get("snippet") or "") + len(item.get("content") or "")
        if not 0 <= offset <= total:
            raise ValueError("CURSOR_INVALID")
        remaining = total - offset
        whole = prose_slice(item, offset, remaining)
        candidate = render([*selected, whole], index + 1)
        if candidate["page"]["serialized_chars"] <= char_budget:
            selected.append(whole)
            index, offset, best = index + 1, 0, candidate
            continue
        if selected:
            break
        # No complete item fits. Find the largest prefix of this one item's
        # remaining prose that fits with its actual signed continuation cursor.
        low, high, partial = 1, remaining - 1, None
        while low <= high:
            count = (low + high) // 2
            candidate = render([prose_slice(item, offset, count)], index, offset + count)
            if candidate["page"]["serialized_chars"] <= char_budget:
                partial = candidate
                low = count + 1
            else:
                high = count - 1
        if partial is None or encode_cursor is None:
            raise ValueError("OUTPUT_ITEM_TOO_LARGE")
        return partial
    if best["page"]["serialized_chars"] > char_budget:
        raise ValueError("OUTPUT_ITEM_TOO_LARGE")
    return best


def error_envelope(tool, provider, request_id, code, message, partial_items=None, retry_after_seconds=None):
    """
    Create an error envelope.

    Args:
        tool: The tool that generated the results
        provider: The provider used by the tool
        request_id: Unique identifier for this request
        code: Error code
        message: Error message
        partial_items: Partial items if any
        retry_after_seconds: Seconds to wait before retrying

    Returns:
        dict: Error envelope
    """
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "request_id": request_id,
        "tool": tool,
        "provider": provider,
        "error": {"code": code, "message": message},
        "coverage": {
            "requested": 0,
            "available": 0,
            "returned_this_page": 0,
            "returned_cumulative": 0,
            "complete": False,
        },
        "page": {
            "number": 1,
            "items": partial_items or [],
            "serialized_chars": 0,
            "warnings": [],
            "next_cursor": None,
            "snapshot_expires_at": None,
        },
        "retry_after_seconds": retry_after_seconds,
        "items": [],
    }
