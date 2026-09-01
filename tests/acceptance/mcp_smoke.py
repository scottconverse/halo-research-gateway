"""Bounded live Streamable HTTP MCP smoke against the installed service."""

import asyncio
import json

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main():
    async with httpx.AsyncClient(trust_env=False, timeout=30) as http:
        async with streamable_http_client("http://127.0.0.1:8765/mcp", http_client=http) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = [tool.name for tool in tools.tools]
                expected = {
                    "web_search",
                    "web_fetch",
                    "web_crawl",
                    "reddit_search",
                    "reddit_thread",
                    "document_extract",
                    "deep_research",
                    "github_research",
                    "transcript_fetch",
                    "community_search",
                    "community_thread",
                    "local_fetch",
                    "local_crawl",
                    "research_job",
                    "web_action_prepare",
                    "web_action_execute",
                }
                if set(names) != expected:
                    raise SystemExit(f"tool mismatch: {names}")
                fetched = await session.call_tool("web_fetch", {"url": "https://example.com", "max_chars": 2000})
                text = "\n".join(getattr(block, "text", "") for block in fetched.content)
                if "Example Domain" not in text or '"ok": true' not in text.lower():
                    raise SystemExit(f"web_fetch failed: {text[:500]}")
                envelope = json.loads(text)
                if len(text) > 2000 or envelope["page"]["serialized_chars"] != len(text):
                    raise SystemExit(
                        f"envelope exceeded budget: wire={len(text)} internal={envelope['page']['serialized_chars']}"
                    )
                print({"tools": len(names), "web_fetch": "ok", "chars": len(text)})


if __name__ == "__main__":
    asyncio.run(main())
