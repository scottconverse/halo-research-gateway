"""Live policy-induced Exa-to-DDGS failover in a disposable native Gateway.

No provider response is mocked. One anonymous Exa admission is allowed, then
the normal persisted quota policy forces the next web query through real DDGS.
Does not change the installed Gateway, DSH, accounts, or paid-provider settings.
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
from urllib.parse import urlsplit

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    with tempfile.TemporaryDirectory(prefix="halo-live-fallback-") as temporary:
        root = Path(temporary)
        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        assert port != 8765
        config = root / "config.toml"
        base = root.as_posix()
        config.write_text(
            f"[server]\nport={port}\nlog_level='ERROR'\n"
            f"[storage]\ndatabase='{base}/state/gateway.db'\n"
            f"backup_directory='{base}/backups'\ncontent_directory='{base}/content'\n"
            f"[crawl]\nbase_directory='{base}/browser'\n"
            "[exa]\ndaily_soft_limit=1\n",
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
                            raise AssertionError((await output)[0].decode(errors="replace"))
                        try:
                            if (await http.get(f"http://127.0.0.1:{port}/health", timeout=1)).status_code == 200:
                                break
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.1)
                async with streamable_http_client(f"http://127.0.0.1:{port}/mcp", http_client=http) as streams:
                    async with ClientSession(streams[0], streams[1]) as session:
                        await session.initialize()

                        async def collect(tool, arguments, budget=2000):
                            rows, page_count, provider, warnings = [], 0, None, set()
                            while True:
                                response = await session.call_tool(
                                    tool, dict(arguments, max_chars=budget), read_timeout_seconds=90
                                )
                                wire = "\n".join(block.text for block in response.content if hasattr(block, "text"))
                                value = json.loads(wire)
                                assert value["ok"], (tool, value.get("error"))
                                assert len(wire) == value["page"]["serialized_chars"] <= budget
                                provider = value["provider"]
                                warnings.update(value["warnings"])
                                rows.extend(value["items"])
                                page_count += 1
                                cursor = value["page"]["next_cursor"]
                                if not cursor:
                                    break
                                assert page_count < 60, "live acceptance page limit"
                                arguments = {"cursor": cursor}
                            assert rows and all(row.get("url") for row in rows)
                            return rows, page_count, provider, sorted(warnings)

                        first = await collect(
                            "web_search",
                            {
                                "query": "site:docs.python.org asyncio TaskGroup CancelledError",
                                "include_domains": ["docs.python.org"],
                                "max_results": 3,
                                "max_age_seconds": 0,
                            },
                        )
                        before = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
                        assert before["providers"]["exa-anonymous"]["requests"] == 1
                        print(
                            json.dumps(
                                {
                                    "case": "primary_attempt",
                                    "provider": first[2],
                                    "urls": sorted({r["url"] for r in first[0]}),
                                    "pages": first[1],
                                    "warnings": first[3],
                                    "exa_ledger": before["providers"]["exa-anonymous"],
                                }
                            ),
                            flush=True,
                        )
                        second = await collect(
                            "web_search",
                            {
                                "query": "site:docs.python.org asyncio cancellation CancelledError exception",
                                "include_domains": ["docs.python.org"],
                                "max_results": 3,
                                "max_age_seconds": 0,
                            },
                        )
                        assert second[2] == "ddgs-accountless", second[2]
                        assert "PROVIDER_FALLBACK_USED" in second[3]
                        assert all(urlsplit(row["url"]).hostname == "docs.python.org" for row in second[0])
                        assert any((row.get("snippet") or row.get("content") or "").strip() for row in second[0])
                        after = (await http.get(f"http://127.0.0.1:{port}/stats")).json()
                        assert after["providers"]["exa-anonymous"]["requests"] == 1
                        print(
                            json.dumps(
                                {
                                    "case": "quota_induced_real_ddgs_fallback",
                                    "provider": second[2],
                                    "urls": sorted({r["url"] for r in second[0]}),
                                    "pages": second[1],
                                    "warnings": second[3],
                                    "exa_admissions_unchanged": True,
                                }
                            ),
                            flush=True,
                        )
                        target = second[0][0]["url"]
                        fetched = await collect("web_fetch", {"url": target, "max_age_seconds": 0}, budget=6000)
                        text = "".join(row.get("content") or "" for row in fetched[0])
                        assert len(text) > 500 and ("CancelledError" in text or "cancel" in text.lower())
                        print(
                            json.dumps(
                                {
                                    "case": "fallback_source_read",
                                    "url": target,
                                    "chars": len(text),
                                    "sha256": hashlib.sha256(text.encode()).hexdigest(),
                                    "pages": fetched[1],
                                    "warnings": fetched[3],
                                }
                            ),
                            flush=True,
                        )
                        assert all(
                            not item["enabled"] and item["attempts_today"] == 0
                            for item in after["optional_providers"].values()
                        )
                        print(
                            "Live native Gateway Exa admission -> quota fallback -> DDGS -> source fetch PASS",
                            flush=True,
                        )
        finally:
            if process.returncode is None:
                process.terminate()
            stdout, _ = await asyncio.wait_for(output, 15)
            if stdout:
                print("NATIVE GATEWAY OUTPUT:", stdout.decode(errors="replace"), flush=True)
            print(json.dumps({"owned_native_process_stopped": process.returncode is not None}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())
