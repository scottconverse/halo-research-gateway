"""Run a bounded real research prompt through the existing production DSH harness.

Creates one owned test session without changing model selection or settings.
No existing session is modified. Deadline cancels only the new test session.
"""

import asyncio
import json
import time
import uuid
from pathlib import Path
from urllib.parse import urldefrag

import httpx

WORKFLOW_DIRECTORY = Path(__file__).resolve().parents[2] / "evidence" / "local" / "dsh-workflow"

PROMPT = """This is a read-only Halo Research Gateway acceptance task. Use your existing research tools to answer: When one Python asyncio TaskGroup child raises a normal exception, what happens to its siblings, and why should coroutine code generally re-raise CancelledError?
Use web_search to discover official Python sources, follow at least one returned cursor using the SAME tool, and read at least two source pages using web_fetch. The official asyncio task and exceptions documentation are suitable. Compare the evidence and give a concise answer with citations to the returned source URLs. If needed, continue source pages to reach the relevant text.
Use the actual Halo Research Gateway tools, not shell scripts that imitate their results. At most twelve research calls. Do not modify files, send messages, post anything, buy anything, change settings, access private accounts, or use paid providers. A missing capability or upstream failure must be stated, not invented. Finish with the source URLs and any coverage limits."""


def evaluate_history(history):
    events = [entry["event"] for entry in history["events"]]
    endings = [event["data"].get("reason", {}) for event in events if event["type"] == "turn/end"]
    calls = [event["data"] for event in events if event["type"] == "tool/call"]
    results = [event["data"] for event in events if event["type"] == "tool/result"]
    fetched = set()
    cursor_used = False
    pending = {}
    issued = {}
    successful_search = False
    successful_results = 0
    failures = []
    # Correlate durable results to actual calls, in event order. Merely trying a
    # cursor or printing a URL does not prove continuation or source retrieval.
    for event in events:
        data = event["data"]
        if event["type"] == "tool/call":
            arguments = data.get("arguments") or {}
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except ValueError:
                    arguments = {}
            pending[data.get("callId")] = (data["name"], arguments if isinstance(arguments, dict) else {})
        elif event["type"] == "tool/result":
            for block in data.get("message", {}).get("content", []):
                if block.get("type") != "tool-result":
                    continue
                call = pending.pop(block.get("toolCallId"), None)
                if call is None:
                    continue
                name, arguments = call
                if not name.startswith("mcp__halo_research__"):
                    continue
                for content in block.get("content", []):
                    if content.get("type") != "text":
                        continue
                    try:
                        envelope = json.loads(content.get("text", ""))
                    except ValueError:
                        continue
                    if not isinstance(envelope, dict):
                        continue
                    if block.get("isError") or envelope.get("ok") is not True:
                        failures.append({"tool": name, "code": envelope.get("error", {}).get("code", "TOOL_ERROR")})
                        continue
                    items = envelope.get("items", [])
                    evidence = [
                        item
                        for item in items
                        if isinstance(item, dict) and item.get("url") and (item.get("content") or item.get("snippet"))
                    ]
                    if not evidence:
                        continue
                    successful_results += 1
                    page = envelope.get("page", {})
                    used = arguments.get("cursor")
                    cursor_used |= bool(used and issued.get(used) == name and page.get("number", 0) > 1)
                    if page.get("next_cursor"):
                        issued[page["next_cursor"]] = name
                    if name.endswith("__web_search"):
                        successful_search = True
                    if name.endswith("__web_fetch"):
                        fetched.update(urldefrag(item["url"])[0] for item in evidence)
    messages = [event["data"]["message"] for event in events if event["type"] == "assistant/message"]
    final = (
        "\n".join(block.get("text", "") for block in messages[-1].get("content", []) if block.get("type") == "text")
        if messages
        else ""
    )
    passed = bool(
        endings
        and endings[-1].get("kind") not in {"error", "aborted", "cancelled"}
        and successful_search
        and cursor_used
        and len(fetched) >= 2
        and successful_results >= 4
        and all(url in final for url in fetched)
    )
    return {
        "passed": passed,
        "turn_end": endings[-1] if endings else None,
        "calls": [call["name"] for call in calls],
        "result_events": len(results),
        "successful_evidence_results": successful_results,
        "failed_results": failures,
        "cursor_used": cursor_used,
        "fetched_urls": sorted(fetched),
        "final": final,
        "semantic_evidence_review_required": True,
    }


async def main():
    async with httpx.AsyncClient(trust_env=False, timeout=30) as client:

        async def rpc(method, payload=None):
            response = await client.post(
                "http://127.0.0.1:3080/api/" + method,
                json={
                    "type": "client-request",
                    "rpcId": str(uuid.uuid4()),
                    "method": method,
                    "payload": payload or {},
                },
            )
            response.raise_for_status()
            result = response.json()["result"]
            if not result.get("ok"):
                raise RuntimeError(f"DSH RPC failed: {method}")
            return result["value"]

        before = await rpc("session.list")
        baseline_ids = {item["sessionId"] for item in before["items"]}
        cwd = WORKFLOW_DIRECTORY
        await asyncio.to_thread(cwd.mkdir, parents=True, exist_ok=True)
        created = await rpc("session.create", {"cwd": str(cwd), "agentPreset": "halo-orchestrator"})
        session_id = created["sessionId"]
        print(json.dumps({"created_session": session_id, "baseline_sessions": len(baseline_ids)}), flush=True)
        selection = await rpc("session.models", {"sessionId": session_id})
        print(json.dumps({"model": selection["current"]}), flush=True)
        await rpc(
            "session.prompt", {"sessionId": session_id, "mode": "queue", "content": [{"type": "text", "text": PROMPT}]}
        )
        deadline = time.monotonic() + 360
        finished = False
        verdict = {"passed": False}
        try:
            while time.monotonic() < deadline:
                await asyncio.sleep(15)
                history = await rpc("session.history", {"sessionId": session_id, "maxMessages": 100})
                events = [entry["event"] for entry in history["events"]]
                types = [event["type"] for event in events]
                current = await rpc("session.list")
                owned = next(item for item in current["items"] if item["sessionId"] == session_id)
                print(
                    json.dumps(
                        {
                            "session": session_id,
                            "running": owned["running"],
                            "events": len(events),
                            "last_types": types[-4:],
                        }
                    ),
                    flush=True,
                )
                if "turn/end" in types and not owned["running"]:
                    finished = True
                    verdict = evaluate_history(history)
                    print(json.dumps({"workflow_verdict": verdict}), flush=True)
                    break
            if not finished:
                print(json.dumps({"deadline_reached": True, "session": session_id}), flush=True)
        finally:
            if not finished:
                await rpc("session.cancel", {"sessionId": session_id})
            after = await rpc("session.list")
            missing = len(baseline_ids - {item["sessionId"] for item in after["items"]})
            print(json.dumps({"finished": finished, "missing_existing_sessions": missing}), flush=True)
        return 0 if finished and verdict["passed"] and not missing else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
