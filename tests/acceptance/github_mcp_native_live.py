"""Native MCP authenticated public GitHub reads using a temporary DPAPI vault.

Reuses existing gh authentication; no token printed, scopes changed, remote
writes or installed Gateway connections. Temporary encrypted state is removed.
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

from halo_research_gateway.connections.store import ConnectionStore
from halo_research_gateway.migrations import migrate


def assert_no_cleartext_secret(root, token):
    for path in root.rglob("*"):
        if path.is_file():
            assert token.encode() not in path.read_bytes(), "Credential persisted without encryption"


async def main():
    credential = await asyncio.to_thread(
        subprocess.run, ["gh", "auth", "token", "--hostname", "github.com"], capture_output=True, text=True, check=False
    )
    if credential.returncode or not credential.stdout.strip():
        raise RuntimeError("Existing GitHub sign-in unavailable")
    token = credential.stdout.strip()
    with tempfile.TemporaryDirectory(prefix="halo-github-mcp-") as temporary:
        root = Path(temporary)
        (root / "state").mkdir()
        database = str(root / "state" / "gateway.db")
        migrate(database, str(root / "backups"))
        connections = ConnectionStore(database, root / "vault")
        connections.create("GitHub", "Disposable authenticated public-source canary", "token", {"token": token})
        await asyncio.to_thread(assert_no_cleartext_secret, root, token)
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
        try:
            async with httpx.AsyncClient(trust_env=False, timeout=90) as http:
                async with asyncio.timeout(20):
                    while True:
                        if process.returncode is not None:
                            raise AssertionError("Disposable Gateway exited before ready")
                        try:
                            health = await http.get(f"http://127.0.0.1:{port}/health", timeout=1)
                            if health.status_code == 200:
                                assert health.json()["connections"]["ready"] == 1
                                break
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.1)
                async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()

                        async def collect(tool, arguments, budget=6000):
                            rows, pages, warnings = [], 0, set()
                            while True:
                                response = await session.call_tool(
                                    tool, dict(arguments, max_chars=budget), read_timeout_seconds=90
                                )
                                wire = "\n".join(block.text for block in response.content if hasattr(block, "text"))
                                assert token not in wire, "Credential leaked in MCP output"
                                value = json.loads(wire)
                                assert value["ok"], (tool, value.get("error"))
                                expected_provider = "github-discussions" if tool == "community_thread" else "github-api"
                                assert value["provider"] == expected_provider, value["provider"]
                                if tool == "community_thread":
                                    assert all(
                                        row["metadata"].get("authenticated_source") is True for row in value["items"]
                                    )
                                assert value["cache"]["key"] == "", "Authenticated result has persistent cache key"
                                assert len(wire) == value["page"]["serialized_chars"] <= budget
                                warnings.update(value["warnings"])
                                rows.extend(value["items"])
                                pages += 1
                                cursor = value["page"]["next_cursor"]
                                if not cursor:
                                    break
                                assert pages < 160, "bounded live GitHub pagination limit"
                                arguments = {"cursor": cursor}
                            assert rows and all(row.get("url", "").startswith("https://github.com/") for row in rows)
                            return rows, pages, sorted(warnings)

                        found, pages, warnings = await collect(
                            "github_research",
                            {"query": "Crawl4AI sort:comments-desc", "kinds": ["discussions"], "max_results": 3},
                        )
                        candidates = {row["url"]: row for row in found}
                        selected = max(
                            candidates.values(), key=lambda row: row.get("metadata", {}).get("reply_count") or 0
                        )
                        print(
                            json.dumps(
                                {
                                    "case": "authenticated_mcp_discussion_search",
                                    "urls": sorted(candidates),
                                    "pages": pages,
                                    "warnings": warnings,
                                    "selected_reply_count": selected.get("metadata", {}).get("reply_count"),
                                }
                            ),
                            flush=True,
                        )
                        thread, pages, warnings = await collect(
                            "community_thread", {"url": selected["url"], "max_replies": 25}
                        )
                        unique = {}
                        for row in thread:
                            unique.setdefault(row["url"], {"depth": row["metadata"]["depth"], "chars": 0})
                            unique[row["url"]]["chars"] += len(row.get("content") or "")
                        assert len(unique) > 1 and any(value["chars"] for value in unique.values())
                        print(
                            json.dumps(
                                {
                                    "case": "authenticated_mcp_discussion_thread",
                                    "root_url": selected["url"],
                                    "unique_items": len(unique),
                                    "depths": sorted({value["depth"] for value in unique.values()}),
                                    "pages": pages,
                                    "warnings": warnings,
                                    "items": unique,
                                }
                            ),
                            flush=True,
                        )
                        nested_observed = False
                        for alternative in sorted(set(candidates) - {selected["url"]}):
                            extra, extra_pages, extra_warnings = await collect(
                                "community_thread", {"url": alternative, "max_replies": 25}
                            )
                            nested_urls = sorted({row["url"] for row in extra if row["metadata"]["depth"] == 2})
                            print(
                                json.dumps(
                                    {
                                        "case": "additional_discussion_nested_coverage",
                                        "root_url": alternative,
                                        "nested_urls": nested_urls,
                                        "pages": extra_pages,
                                        "warnings": extra_warnings,
                                    }
                                ),
                                flush=True,
                            )
                            if nested_urls:
                                nested_observed = True
                                break
                        print(json.dumps({"live_nested_reply_observed": nested_observed}), flush=True)
                        assert nested_observed, "No nested reply was returned by the bounded live-source sample"
                        pinned, pages, warnings = await collect(
                            "github_research",
                            {
                                "query": "README",
                                "repository": "microsoft/playwright",
                                "kinds": ["docs"],
                                "ref": "main",
                                "max_results": 1,
                            },
                            budget=2000,
                        )
                        text = "".join(row.get("content") or "" for row in pinned)
                        assert len(text) > 500 and all(row["metadata"]["sha"] in row["url"] for row in pinned)
                        assert all(row["metadata"]["ref"] == "main" for row in pinned)
                        print(
                            json.dumps(
                                {
                                    "case": "authenticated_mcp_ref_pinned_document",
                                    "url": pinned[0]["url"],
                                    "sha": pinned[0]["metadata"]["sha"],
                                    "chars": len(text),
                                    "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                                    "pages": pages,
                                    "warnings": warnings,
                                }
                            ),
                            flush=True,
                        )
                        stats = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
                        assert stats["cache"]["entries"] == 0
                        print(
                            json.dumps({"authenticated_disk_cache_entries": 0, "temporary_connection_ready": True}),
                            flush=True,
                        )
                        print("Authenticated native MCP GitHub search/thread/ref/pagination PASS", flush=True)
        finally:
            if process.returncode is None:
                process.terminate()
            stdout, _ = await asyncio.wait_for(output, 15)
            sanitized = stdout.decode(errors="replace").replace(token, "[REDACTED]")
            if sanitized:
                print("NATIVE GATEWAY OUTPUT:", sanitized, flush=True)
            assert token.encode() not in stdout, "Credential found in native Gateway log"
            print(json.dumps({"owned_native_process_stopped": process.returncode is not None}), flush=True)
    print(json.dumps({"temporary_vault_and_state_removed": not (await asyncio.to_thread(root.exists))}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
