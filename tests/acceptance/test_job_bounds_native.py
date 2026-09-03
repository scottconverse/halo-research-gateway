"""Concurrent native MCP clients retain job evidence within whole-response budgets.

Disposable seeded public-evidence fixture, no upstream network or installed state.
"""

import asyncio
import hashlib
import json
import os
import socket
import subprocess
import sys

import httpx
from test_result_retention_native import mcp_at

from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem
from halo_research_gateway.service import HaloService


async def test_native_job_status_budgets_shared_clients_and_lossless_continuation(tmp_path):
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    assert port != 8765
    root = tmp_path.as_posix()
    config_path = tmp_path / "config.toml"
    config_path.write_text(
        f"[server]\nport={port}\nlog_level='ERROR'\n"
        f"[storage]\ndatabase='{root}/state/gateway.db'\n"
        f"backup_directory='{root}/backups'\ncontent_directory='{root}/content'\n"
        f"[crawl]\nbase_directory='{root}/browser'\n",
        encoding="utf-8",
    )
    content = "Native job evidence remains complete across clients. \u03bb\n" * 100
    service = HaloService(GatewayConfig.load(config_path))
    try:
        job = service.jobs.create("unidentified", "Question \u03bb " * 600, {"timeout_seconds": 30})
        service.jobs.start(job["job_id"], "unidentified", 30)
        item = EvidenceItem(url="https://example.org/native-job", retrieved_at="2026-09-03T00:00:00Z", content=content)
        item.title = "Coroutines and tasks — Python documentation"
        item.metadata = {"content_type": "text/html", "sha256": hashlib.sha256(content.encode()).hexdigest()}
        service.jobs.checkpoint(
            job["job_id"],
            "unidentified",
            {
                "items": [item.as_dict()],
                "attempted": 1,
                "elapsed_seconds": 0.2,
                "warnings": [
                    "PARTIAL_FIXTURE",
                    "CROSS_SITE_LINK_SKIPPED",
                    "DUPLICATE_CONTENT_SKIPPED",
                    "DUPLICATE_URL_SKIPPED",
                    "PAGE_LIMIT_REACHED",
                    "PROVIDER_FALLBACK_USED",
                    "SOURCE_LIMIT_REACHED",
                ],
            },
            service.config.storage.entry_max_bytes,
        )
        service.jobs.transition(job["job_id"], "unidentified", "pause")
    finally:
        await service.close()
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "halo_research_gateway",
        env=dict(os.environ, HALO_RESEARCH_CONFIG=str(config_path), LOCALAPPDATA=str(tmp_path)),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
    )
    output = asyncio.create_task(process.communicate())
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=1) as http:
            async with asyncio.timeout(20):
                while True:
                    if process.returncode is not None:
                        raise AssertionError((await output)[0].decode(errors="replace"))
                    try:
                        health = await http.get(f"http://127.0.0.1:{port}/health")
                        if health.status_code == 200 and health.json()["status"] == "ok":
                            break
                    except httpx.HTTPError:
                        pass
                    await asyncio.sleep(0.05)

        async def read_all(budget):
            async with mcp_at(port) as client:

                async def call(tool, arguments):
                    reply = await client.call_tool(tool, arguments)
                    wire = "\n".join(block.text for block in reply.content if hasattr(block, "text"))
                    assert not reply.is_error and len(wire) <= budget
                    return json.loads(wire), len(wire)

                status, chars = await call(
                    "research_job", {"operation": "status", "job_id": job["job_id"], "max_chars": budget}
                )
                assert status["state"] == "paused"
                assert status["request"]["question_truncated"] is True
                page, collected, pages = status["progress"]["result"], "", 0
                while True:
                    if not page.get("ok"):
                        print(json.dumps({"failed_budget": budget, "pages_read": pages, "status": status}))
                    assert page["ok"] and "PARTIAL_FIXTURE" in page["warnings"]
                    if not page["items"]:
                        assert pages == 0 and page["page"]["next_cursor"]
                        assert page["coverage"]["returned_this_page"] == 0 and not page["coverage"]["complete"]
                    collected += "".join(item.get("content") or "" for item in page["items"])
                    pages += 1
                    assert pages < 100
                    cursor = page["page"]["next_cursor"]
                    if not cursor:
                        break
                    page, _ = await call("deep_research", {"cursor": cursor, "max_chars": budget})
                assert collected == content
                rejected, _ = await call(
                    "research_job", {"operation": "create", "question": "x" * 8193, "max_chars": budget}
                )
                assert rejected["ok"] is False and rejected["error"]["code"] == "INVALID_ARGUMENT"
                return {
                    "budget": budget,
                    "status_chars": chars,
                    "pages": pages,
                    "content_sha256": hashlib.sha256(collected.encode()).hexdigest(),
                }

        results = await asyncio.gather(*(read_all(budget) for budget in (2000, 4000, 6000)), return_exceptions=True)
        assert not any(isinstance(result, BaseException) for result in results), results
        async with httpx.AsyncClient(trust_env=False) as http:
            stats = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
            assert stats["jobs"]["paused"] == 1 and sum(stats["jobs"].values()) == 1
        print(json.dumps({"clients": results, "jobs_preserved": 1, "public_egress": False}))
    finally:
        if process.returncode is None:
            process.terminate()
        await asyncio.wait_for(output, 10)
        assert process.returncode is not None
