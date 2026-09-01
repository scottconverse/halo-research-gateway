"""Live MCP contract checks that cannot be proven from Python callables alone."""

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
                tools = {tool.name: tool for tool in (await session.list_tools()).tools}
                for tool_name, original_argument in {
                    "web_search": "query",
                    "web_fetch": "url",
                    "web_crawl": "url",
                    "reddit_search": "query",
                    "reddit_thread": "url",
                    "document_extract": "url",
                    "local_fetch": "target",
                    "local_crawl": "target",
                }.items():
                    required = tools[tool_name].input_schema.get("required", [])
                    if original_argument in required:
                        raise SystemExit(
                            f"{tool_name} still requires {original_argument}; cursor-only continuation is blocked"
                        )

                first = await session.call_tool(
                    "web_fetch",
                    {"url": "https://www.rfc-editor.org/rfc/rfc9110.txt", "max_chars": 2000, "max_age_seconds": 0},
                )
                envelope = json.loads("\n".join(getattr(block, "text", "") for block in first.content))
                cursor = envelope["page"]["next_cursor"]
                if not cursor:
                    raise SystemExit("fixture did not produce a continuation cursor")
                second = await session.call_tool("web_fetch", {"cursor": cursor})
                continuation = json.loads("\n".join(getattr(block, "text", "") for block in second.content))
                if not continuation["ok"] or continuation["page"]["number"] != 2:
                    raise SystemExit(f"cursor-only continuation failed: {continuation}")
                if continuation["page"]["serialized_chars"] > 2000:
                    raise SystemExit(f"cursor lost its 2000-character bound: {continuation['page']}")
                print(
                    {
                        "cursor_only": "ok",
                        "page": 2,
                        "serialized_chars": continuation["page"]["serialized_chars"],
                    }
                )


if __name__ == "__main__":
    asyncio.run(main())
