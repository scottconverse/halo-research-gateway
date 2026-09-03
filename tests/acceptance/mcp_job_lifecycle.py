"""Finite public-source job canary against the installed Gateway, not DSH.

Creates one owned test job; pauses/resumes it and follows retained evidence.
Cancels only that job on failure/deadline. Uses the accountless discovery path.
"""

import asyncio
import json

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

QUESTION = "site:docs.python.org Python asyncio TaskGroup child exception sibling cancellation CancelledError"


async def main():
    async with httpx.AsyncClient(trust_env=False, timeout=30) as http:
        async with streamable_http_client("http://127.0.0.1:8765/mcp", http_client=http) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()

                async def call(tool, arguments):
                    response = await session.call_tool(tool, arguments)
                    payload = json.loads("\n".join(getattr(block, "text", "") for block in response.content))
                    if response.is_error:
                        raise RuntimeError(payload)
                    return payload

                async def control(operation, **arguments):
                    return await call("research_job", {"operation": operation, **arguments})

                created = await control(
                    "create", question=QUESTION, limits={"max_sources": 2, "max_pages": 3, "timeout_seconds": 45}
                )
                job_id = created["job_id"]
                print(json.dumps({"created_job": job_id, "limits": created["limits"]}), flush=True)
                terminal = False
                try:
                    paused = await control("pause", job_id=job_id)
                    assert paused["state"] == "paused", paused["state"]
                    first = await control("status", job_id=job_id)
                    await asyncio.sleep(1)
                    second = await control("status", job_id=job_id)
                    assert first["progress"].get("checkpoint") == second["progress"].get("checkpoint")
                    print(json.dumps({"pause": "passed", "checkpoint_frozen": True}), flush=True)
                    resumed = await control("resume", job_id=job_id)
                    assert resumed["state"] == "queued", resumed["state"]
                    deadline = asyncio.get_running_loop().time() + 55
                    while asyncio.get_running_loop().time() < deadline:
                        current = await control("status", job_id=job_id)
                        if current["state"] in {"complete", "failed", "cancelled"}:
                            terminal = True
                            break
                        await asyncio.sleep(1)
                    assert terminal, "job did not reach a terminal state"
                    progress = current["progress"]
                    result = progress.get("result") or {}
                    items = result.get("items") or []
                    print(
                        json.dumps(
                            {
                                "job_id": job_id,
                                "state": current["state"],
                                "error_code": current["error_code"],
                                "checkpoint": progress.get("checkpoint"),
                                "partial": progress.get("partial"),
                                "warnings": result.get("warnings"),
                                "source_urls": [item["url"] for item in items],
                                "status_chars": len(json.dumps(current)),
                            }
                        ),
                        flush=True,
                    )
                    assert current["state"] == "complete" and items, "research returned no evidence"
                    assert progress["checkpoint"]["attempted"] <= 3
                    assert progress["checkpoint"]["elapsed_seconds"] <= 46
                    cursor = (result.get("page") or {}).get("next_cursor")
                    if cursor:
                        page = await call("deep_research", {"question": "", "cursor": cursor, "max_chars": 4000})
                        assert page["ok"] and page.get("items"), "retained evidence cursor failed"
                        print(
                            json.dumps(
                                {"evidence_cursor": "passed", "page_source_urls": [i["url"] for i in page["items"]]}
                            ),
                            flush=True,
                        )
                    print(
                        json.dumps({"live_gateway_job_canary": "PASS", "dsh_proof": False, "crash_proof": False}),
                        flush=True,
                    )
                finally:
                    if not terminal:
                        await control("cancel", job_id=job_id)
                        print(json.dumps({"owned_canary_job_cancelled": job_id}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
