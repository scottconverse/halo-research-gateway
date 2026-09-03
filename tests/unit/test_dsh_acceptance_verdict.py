import asyncio
import json
import runpy
from pathlib import Path

import httpx
import pytest


@pytest.mark.asyncio
async def test_dsh_finished_turn_with_runtime_error_is_not_workflow_success(monkeypatch):
    acceptance = runpy.run_path(str(Path(__file__).parents[1] / "acceptance" / "dsh_research_workflow.py"))
    history = {
        "events": [
            {
                "event": {
                    "type": "turn/end",
                    "data": {
                        "reason": {
                            "kind": "error",
                            "error": {"message": "Cannot read properties of undefined (reading 'prepare')"},
                        }
                    },
                }
            }
        ]
    }

    def respond(request):
        method = json.loads(request.content)["method"]
        values = {
            "session.list": {"items": [{"sessionId": "test-owned", "running": False}]},
            "session.create": {"sessionId": "test-owned"},
            "session.models": {"current": {"provider": "fixture", "model": "fixture"}},
            "session.prompt": {},
            "session.history": history,
        }
        return httpx.Response(200, json={"result": {"ok": True, "value": values[method]}})

    original_client = httpx.AsyncClient
    monkeypatch.setattr(
        httpx, "AsyncClient", lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs)
    )
    original_sleep = asyncio.sleep

    async def tick(_):
        await original_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", tick)
    assert await acceptance["main"]() == 1


def workflow_history(*, continuation_ok=True, copied_cursor="issued-cursor", fetch_ok=True, second_url=None):
    """DSH's recorded tool-result envelope, with one discovered continuation."""
    urls = [
        "https://docs.python.org/3/library/asyncio-task.html",
        second_url or "https://docs.python.org/3/library/asyncio-exceptions.html",
    ]
    history = {"events": []}

    def add(kind, data):
        history["events"].append({"event": {"type": kind, "data": data}})

    for number, (name, arguments, ok, items, page) in enumerate(
        [
            (
                "web_search",
                {"query": "asyncio"},
                True,
                [{"url": urls[0], "snippet": "source"}],
                {"number": 1, "next_cursor": "issued-cursor"},
            ),
            (
                "web_search",
                {"query": "asyncio", "cursor": copied_cursor},
                continuation_ok,
                [{"url": urls[1], "snippet": "source"}] if continuation_ok else [],
                {"number": 2},
            ),
            (
                "web_fetch",
                {"url": urls[0]},
                fetch_ok,
                [{"url": urls[0], "content": "first source evidence"}] if fetch_ok else [],
                {"number": 1},
            ),
            (
                "web_fetch",
                {"url": urls[1]},
                fetch_ok,
                [{"url": urls[1], "content": "second source evidence"}] if fetch_ok else [],
                {"number": 1},
            ),
        ]
    ):
        call_id = str(number)
        add("tool/call", {"callId": call_id, "name": "mcp__halo_research__" + name, "arguments": json.dumps(arguments)})
        envelope = {"ok": ok, "items": items, "page": page}
        if not ok:
            envelope["error"] = {"code": "CURSOR_INVALID" if name == "web_search" else "FETCH_FAILED"}
        add(
            "tool/result",
            {
                "message": {
                    "content": [
                        {
                            "type": "tool-result",
                            "toolCallId": call_id,
                            "isError": False,
                            "content": [{"type": "text", "text": json.dumps(envelope)}],
                        }
                    ]
                }
            },
        )
    add("assistant/message", {"message": {"content": [{"type": "text", "text": "Sources: " + " ".join(urls)}]}})
    add("turn/end", {"reason": {"kind": "completed"}})
    return history


def evaluate_workflow(history):
    acceptance = runpy.run_path(str(Path(__file__).parents[1] / "acceptance" / "dsh_research_workflow.py"))
    return acceptance["evaluate_history"](history)


def test_dsh_success_requires_returned_evidence_and_an_issued_successful_continuation():
    assert evaluate_workflow(workflow_history())["passed"] is True


def test_dsh_rejected_cursor_is_not_pagination_success():
    assert evaluate_workflow(workflow_history(continuation_ok=False))["passed"] is False


def test_dsh_unissued_cursor_is_not_verified_continuation():
    assert evaluate_workflow(workflow_history(copied_cursor="invented-cursor"))["passed"] is False


def test_dsh_failed_fetches_are_not_source_evidence():
    assert evaluate_workflow(workflow_history(fetch_ok=False))["passed"] is False


def test_dsh_two_fragments_of_one_page_are_not_two_sources():
    history = workflow_history(second_url="https://docs.python.org/3/library/asyncio-task.html#task-groups")
    assert evaluate_workflow(history)["passed"] is False
