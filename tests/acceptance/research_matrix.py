"""Explicit live MCP research acceptance; public sources and no paid calls.

Prints bounded public-source receipts, never credentials or private profile data.
Run separately from deterministic CI. Site failures remain visible, not skipped.
"""

import asyncio
import json
import sys

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


def envelope(result):
    return json.loads("\n".join(getattr(block, "text", "") for block in result.content))


async def main():
    failures = []
    async with httpx.AsyncClient(trust_env=False, timeout=100) as http:
        async with streamable_http_client("http://127.0.0.1:8765/mcp", http_client=http) as streams:
            async with ClientSession(streams[0], streams[1]) as session:
                await session.initialize()

                async def check(label, tool, args, expected=None):
                    try:
                        async with asyncio.timeout(95):
                            result = envelope(await session.call_tool(tool, args, read_timeout_seconds=90))
                        items = result.get("items", [])
                        text = "\n".join(str(item.get("content") or item.get("snippet") or "") for item in items)
                        passed = bool(result.get("ok") and items and all(item.get("url") for item in items))
                        if expected:
                            passed = passed and expected.casefold() in text.casefold()
                        receipt = {
                            "case": label,
                            "passed": passed,
                            "tool": tool,
                            "provider": result.get("provider"),
                            "items": len(items),
                            "urls": [item.get("url") for item in items],
                            "text_sample": text[:240],
                            "warnings": result.get("warnings"),
                            "error": result.get("error"),
                            "has_more": bool(result.get("page", {}).get("next_cursor")),
                        }
                    except Exception as exc:
                        result = {}
                        passed = False
                        receipt = {"case": label, "passed": False, "error_type": type(exc).__name__}
                    if not passed:
                        failures.append(label)
                    print(json.dumps(receipt), flush=True)
                    return result

                search = await check(
                    "source discovery",
                    "web_search",
                    {
                        "query": "Python asyncio TaskGroup cancellation official documentation",
                        "max_results": 5,
                        "max_chars": 2000,
                        "max_age_seconds": 0,
                    },
                )
                cursor = search.get("page", {}).get("next_cursor")
                if cursor:
                    await check("search continuation", "web_search", {"cursor": cursor})
                first = await check(
                    "ordinary official source",
                    "web_fetch",
                    {
                        "url": "https://docs.python.org/3/library/asyncio-task.html",
                        "max_chars": 2000,
                        "max_age_seconds": 0,
                    },
                    "coroutine",
                )
                cursor = first.get("page", {}).get("next_cursor")
                if cursor:
                    await check("source continuation", "web_fetch", {"cursor": cursor})
                await check(
                    "second official source",
                    "web_fetch",
                    {
                        "url": "https://docs.python.org/3/library/asyncio-exceptions.html",
                        "max_chars": 4000,
                        "max_age_seconds": 0,
                    },
                    "CancelledError",
                )
                await check(
                    "JavaScript rendered evidence",
                    "web_crawl",
                    {
                        "url": "https://quotes.toscrape.com/js/",
                        "wait_for": ".quote",
                        "max_chars": 4000,
                        "max_age_seconds": 0,
                    },
                    "Albert Einstein",
                )
                await check(
                    "PDF text",
                    "document_extract",
                    {
                        "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                        "pages": "1",
                        "max_chars": 4000,
                        "max_age_seconds": 0,
                    },
                    "Dummy PDF",
                )
                await check(
                    "public captioned media",
                    "transcript_fetch",
                    {
                        "url": "https://iandevlin.github.io/mdn/video-player-with-captions/",
                        "language": "en",
                        "max_chars": 4000,
                    },
                )
                reddit = await check(
                    "Reddit discovery",
                    "reddit_search",
                    {
                        "query": "Strix Halo",
                        "subreddit": "LocalLLaMA",
                        "max_results": 2,
                        "max_chars": 4000,
                        "max_age_seconds": 0,
                    },
                )
                if reddit.get("items"):
                    await check(
                        "Reddit thread",
                        "reddit_thread",
                        {
                            "url": reddit["items"][0]["url"],
                            "max_comments": 5,
                            "max_chars": 4000,
                            "max_age_seconds": 0,
                        },
                    )
                community = await check(
                    "Hacker News discovery",
                    "community_search",
                    {
                        "query": "SQLite",
                        "sources": ["hackernews"],
                        "max_results": 2,
                        "max_chars": 4000,
                    },
                )
                if community.get("items"):
                    await check(
                        "Hacker News discussion",
                        "community_thread",
                        {
                            "url": community["items"][0]["url"],
                            "max_replies": 5,
                            "max_chars": 4000,
                        },
                    )
                await check(
                    "multi-source research",
                    "deep_research",
                    {
                        "question": "How do Python asyncio TaskGroup and CancelledError interact?",
                        "seed_urls": [
                            "https://docs.python.org/3/library/asyncio-task.html",
                            "https://docs.python.org/3/library/asyncio-exceptions.html",
                        ],
                        "include_domains": ["docs.python.org"],
                        "max_sources": 2,
                        "max_pages": 2,
                        "max_depth": 0,
                        "max_chars": 6000,
                    },
                )
    print(json.dumps({"matrix_failures": failures, "passed": not failures}), flush=True)
    return bool(failures)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
