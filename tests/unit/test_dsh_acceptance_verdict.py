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
