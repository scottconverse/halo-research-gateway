"""Small sequential live canaries; each upstream is called at most once."""

import asyncio
import json

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def envelope(result):
    text = "\n".join(getattr(block, "text", "") for block in result.content)
    return json.loads(text)


async def main():
    outcomes = {}
    async with httpx.AsyncClient(trust_env=False, timeout=150) as http:
        async with streamable_http_client("http://127.0.0.1:8765/mcp", http_client=http) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()
                search = envelope(
                    await session.call_tool(
                        "web_search",
                        {"query": "official Model Context Protocol Python SDK", "max_results": 3},
                        read_timeout_seconds=60,
                    )
                )
                if not search["ok"] or not search["items"]:
                    raise SystemExit(f"search failed: {search}")
                outcomes["search"] = {"provider": search["provider"], "items": len(search["items"])}

                crawl = envelope(
                    await session.call_tool(
                        "web_crawl",
                        {"url": "https://example.com", "max_chars": 2000},
                        read_timeout_seconds=60,
                    )
                )
                if not crawl["ok"] or "Example Domain" not in json.dumps(crawl):
                    raise SystemExit(f"crawl failed: {crawl}")
                outcomes["crawl"] = {"provider": crawl["provider"], "items": len(crawl["items"])}

                document = envelope(
                    await session.call_tool(
                        "document_extract",
                        {
                            "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                            "pages": "1",
                            "max_chars": 4000,
                        },
                        read_timeout_seconds=60,
                    )
                )
                if not document["ok"] or not document["items"]:
                    raise SystemExit(f"document failed: {document}")
                outcomes["document"] = {"provider": document["provider"], "items": len(document["items"])}

                reddit = envelope(
                    await session.call_tool(
                        "reddit_search",
                        {"query": "Model Context Protocol", "max_results": 2, "max_chars": 4000},
                        read_timeout_seconds=60,
                    )
                )
                outcomes["reddit"] = {"ok": reddit["ok"], "provider": reddit["provider"], "items": len(reddit["items"])}
    print(outcomes)


if __name__ == "__main__":
    asyncio.run(main())
