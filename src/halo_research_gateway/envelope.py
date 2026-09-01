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
    """
    Create a paginated envelope of items with proper cursor management.

    Args:
        tool: The tool that generated the results
        provider: The provider used by the tool
        request_id: Unique identifier for this request
        requested_at: When the request was made
        completed_at: When processing completed
        items: List of items to paginate
        requested: Number of items requested
        available: Total number of items available
        char_budget: Maximum serialized size for each page
        cache_hit: Whether this came from cache
        cache_age_seconds: Age of cached content in seconds
        cache_key: Cache key used
        cursor: Base64 encoded cursor from previous request
        warnings: Warnings to include

    Returns:
        dict: Envelope containing pagination info, items and metadata
    """
    if cursor_state is not None:
        next_index = cursor_state["i"]
        cumulative_so_far = cursor_state["c"]
        page_number = cursor_state["n"]
    else:
        next_index = 0
        cumulative_so_far = 0
        page_number = 1

    # Collect items for this page
    page_items = []

    # Add items one by one while staying within budget, with fixed-point iteration to make sure we get the exact length
    total_items_added = 0

    # Build a base envelope structure - including ALL required fields from start
    env_base = {
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
            "returned_this_page": 0,
            "returned_cumulative": cumulative_so_far,
            "complete": False,
        },
        "page": {
            "number": page_number,
            "serialized_chars": 0,
            "next_cursor": None,
            "snapshot_expires_at": None,
        },
        "retry_after_seconds": None,
        "items": [],
        "warnings": warnings or [],
    }

    # Add items one by one while staying within budget using fixed-point approach
    for i in range(next_index, len(items)):
        item = items[i]

        # Test adding this item to see if it fits - use a copy to avoid affecting the real env
        test_env = json.loads(json.dumps(env_base))
        test_env["items"] = page_items + [item]

        # Calculate exact serialized size using fixed-point iteration (Defect 1)
        calculated_chars = 0
        for _ in range(10):
            env_copy = json.loads(json.dumps(test_env))
            # MCP Python SDK renders mapping results as indented JSON text. The
            # host budget must measure that wire-visible representation.
            actual_size = len(json.dumps(env_copy, indent=2, ensure_ascii=False))
            if calculated_chars == actual_size:
                break
            calculated_chars = actual_size

        # If adding this would exceed budget and we already have items, stop
        if calculated_chars > char_budget and len(page_items) > 0:
            break

        page_items.append(item)
        total_items_added += 1

    # Ensure forward progress: include at least one item even if it exceeds budget (Defect 2)
    if not page_items and next_index < len(items):
        page_items = [items[next_index]]
        total_items_added = 1

    # Final envelope construction with all fields set
    env = json.loads(json.dumps(env_base))  # Start with clean base
    env["items"] = page_items
    env["coverage"]["returned_this_page"] = len(page_items)
    env["coverage"]["returned_cumulative"] = cumulative_so_far + len(page_items)

    # Set next cursor properly for pagination (Defect 2)
    next_index = next_index + total_items_added

    # Terminate pagination when all items are consumed (Defect 2)
    if next_index >= len(items):
        env["page"]["next_cursor"] = None
        env["coverage"]["complete"] = True
        env["warnings"] = warnings or []
    else:
        payload = {"i": next_index, "c": cumulative_so_far + len(page_items), "n": page_number + 1}
        next_cursor = encode_cursor(payload) if encode_cursor else None
        env["page"]["next_cursor"] = next_cursor
        env["warnings"] = sorted(set([*(warnings or []), "RESULT_TRUNCATED"]))

    # The envelope itself has variable overhead (URLs, metadata, cursor). If a
    # single chunk still exceeds the host ceiling, trim only its prose fields;
    # never remove the citation URL or retrieval time required on every page.
    for item in env["items"]:
        while True:
            actual = len(json.dumps(env, indent=2, ensure_ascii=False))
            if actual <= char_budget:
                break
            field = "content" if item.get("content") else "snippet" if item.get("snippet") else None
            if field is None:
                item.pop("metadata", None)
                break
            value = item[field]
            excess = actual - char_budget
            keep = max(0, len(value) - excess - 16)
            item[field] = value[:keep]
            if keep == 0:
                break
        if len(json.dumps(env, indent=2, ensure_ascii=False)) <= char_budget:
            break
    # Fixed-point iteration to make serialized_chars exactly match json.dumps(env) (Defect 1)
    for _ in range(10):
        actual = len(json.dumps(env, indent=2, ensure_ascii=False))
        if env["page"]["serialized_chars"] == actual:
            break
        env["page"]["serialized_chars"] = actual

    return env


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
