"""Explicit native MCP transcript paging and restart proof using a public source.

Starts only disposable loopback Gateway processes; never reloads installed Gateway
or DSH. No accounts, personal profiles, paid providers or media payloads are used.
"""

import asyncio
import hashlib
import json
import os
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "https://iandevlin.github.io/mdn/video-player-with-captions/"


def reconstruct(rows):
    content, segments = [], {}
    for row in rows:
        assert row["url"] == URL and row["retrieved_at"]
        content.append(row.get("content") or "")
        for index, fragment in enumerate(row.get("metadata", {}).get("segments", [])):
            key = fragment.get("segment_index", index)
            item = segments.setdefault(
                key,
                {
                    "start_seconds": fragment["start_seconds"],
                    "end_seconds": fragment["end_seconds"],
                    "text": "",
                },
            )
            assert (item["start_seconds"], item["end_seconds"]) == (fragment["start_seconds"], fragment["end_seconds"])
            assert fragment.get("text_offset", 0) == len(item["text"]), "Repeated or missing segment text"
            item["text"] += fragment["text"]
    return "".join(content), [segments[key] for key in sorted(segments)]


async def page(session, arguments, budget):
    reply = await session.call_tool("transcript_fetch", dict(arguments, max_chars=budget), read_timeout_seconds=30)
    assert not reply.is_error
    wire = "\n".join(block.text for block in reply.content if hasattr(block, "text"))
    value = json.loads(wire)
    assert value["ok"], value.get("error")
    assert value["provider"] == "public-transcript"
    assert len(wire) == value["page"]["serialized_chars"] <= budget
    return value


async def remaining(session, first, budget):
    current, rows, pages, warnings = first, [], 0, set()
    while True:
        rows.extend(current["items"])
        warnings.update(current["warnings"])
        pages += 1
        cursor = current["page"]["next_cursor"]
        if not cursor:
            return rows, pages, sorted(warnings)
        assert pages < 150, "Bounded transcript acceptance page limit"
        current = await page(session, {"cursor": cursor}, budget)


async def main():
    with tempfile.TemporaryDirectory(prefix="halo-transcript-paging-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        assert port != 8765
        base = root.as_posix()
        config = root / "config.toml"
        config.write_text(
            f"[server]\nport={port}\nlog_level='ERROR'\n"
            f"[storage]\ndatabase='{base}/state/gateway.db'\n"
            f"backup_directory='{base}/backups'\ncontent_directory='{base}/content'\n"
            f"[crawl]\nbase_directory='{base}/browser'\n",
            encoding="utf-8",
        )
        process, output = None, None

        async def launch():
            nonlocal process, output
            process = await asyncio.create_subprocess_exec(
                sys.executable,
                "-m",
                "halo_research_gateway",
                env=dict(os.environ, HALO_RESEARCH_CONFIG=str(config), LOCALAPPDATA=str(root)),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                **({"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}),
            )
            output = asyncio.create_task(process.communicate())
            async with httpx.AsyncClient(trust_env=False, timeout=1) as http:
                async with asyncio.timeout(20):
                    while True:
                        assert process.returncode is None, "Owned native Gateway exited during startup"
                        try:
                            response = await http.get(f"http://127.0.0.1:{port}/health")
                            if response.status_code == 200:
                                return response.json()["started_at"]
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.1)

        async def stop():
            if process is None:
                return
            if process.returncode is None:
                process.terminate()
            try:
                stdout, _ = await asyncio.wait_for(asyncio.shield(output), 15)
            except TimeoutError:
                process.kill()
                stdout, _ = await asyncio.wait_for(output, 5)
            if stdout:
                print("NATIVE GATEWAY OUTPUT:", stdout.decode(errors="replace"), flush=True)
            assert process.returncode is not None

        try:
            first_start = await launch()
            expected, saved_first = None, None
            async with asyncio.timeout(120):
                async with httpx.AsyncClient(trust_env=False, timeout=35) as http:
                    async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
                        async with ClientSession(streams[0], streams[1]) as session:
                            await session.initialize()
                            for budget in (2000, 4000, 6000):
                                first = await page(session, {"url": URL, "language": "en"}, budget)
                                rows, pages, warnings = await remaining(session, first, budget)
                                actual = reconstruct(rows)
                                assert len(actual[0]) >= 500 and len(actual[1]) > 1
                                assert len(actual[1]) == rows[0]["metadata"]["segment_count"]
                                assert all(s["end_seconds"] >= s["start_seconds"] and s["text"] for s in actual[1])
                                if expected is None:
                                    expected, saved_first = actual, first
                                    assert pages > 1 and first["page"]["next_cursor"]
                                else:
                                    assert actual == expected, "Budget changed collected text or timing"
                                print(
                                    json.dumps(
                                        {
                                            "case": "public_transcript",
                                            "url": URL,
                                            "max_chars": budget,
                                            "pages": pages,
                                            "content_chars": len(actual[0]),
                                            "segments": len(actual[1]),
                                            "evidence_sha256": hashlib.sha256(
                                                json.dumps(actual, ensure_ascii=False).encode()
                                            ).hexdigest(),
                                            "warnings": warnings,
                                        }
                                    ),
                                    flush=True,
                                )
            await stop()
            second_start = await launch()
            assert second_start != first_start
            async with asyncio.timeout(60):
                async with httpx.AsyncClient(trust_env=False, timeout=35) as http:
                    async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
                        async with ClientSession(streams[0], streams[1]) as session:
                            await session.initialize()
                            resumed = await page(session, {"cursor": saved_first["page"]["next_cursor"]}, 2000)
                            assert resumed["cache"]["hit"]
                            rows, pages, warnings = await remaining(session, resumed, 2000)
                            assert reconstruct(saved_first["items"] + rows) == expected
                            print(
                                json.dumps(
                                    {
                                        "case": "new_process_and_client_continue_cached_transcript",
                                        "remaining_pages": pages,
                                        "identical_evidence": True,
                                        "warnings": warnings,
                                    }
                                ),
                                flush=True,
                            )
            print("Native transcript text/timestamps at all budgets and restart continuation PASS", flush=True)
        finally:
            await stop()
            print(
                json.dumps({"owned_native_process_stopped": process is None or process.returncode is not None}),
                flush=True,
            )
    print("Temporary native Gateway state removed", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
