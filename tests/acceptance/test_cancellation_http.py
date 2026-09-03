"""Real loopback HTTP transport cancellation; no external or private account access.

Exercises Coordinator with HTTPX, not the public URL-policy adapter or DSH.
"""

import asyncio

import httpx
import pytest

from halo_research_gateway.coordinator import Coordinator, QueuePolicy


@pytest.mark.asyncio
async def test_shared_http_read_disconnects_only_after_last_caller_and_can_restart():
    accepted, disconnected = asyncio.Event(), asyncio.Event()
    handlers, writers = set(), set()
    requests = 0

    async def serve(reader, writer):
        nonlocal requests
        task = asyncio.current_task()
        handlers.add(task)
        writers.add(writer)
        try:
            await reader.readuntil(b"\r\n\r\n")
            requests += 1
            if requests == 1:
                accepted.set()
                assert await reader.read() == b""
                disconnected.set()
            else:
                writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 14\r\nConnection: close\r\n\r\nfresh evidence")
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
            writers.discard(writer)
            handlers.discard(task)

    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    coordinator = Coordinator({"http": QueuePolicy(4, 4, 1)})
    callers = []
    try:
        async with httpx.AsyncClient(trust_env=False, timeout=5) as client:

            async def fetch():
                response = await client.get(f"http://127.0.0.1:{port}/evidence")
                response.raise_for_status()
                return response.text

            for name in ("first", "second", "third"):
                callers.append(asyncio.create_task(coordinator.run("http", name, "same", fetch)))
            await asyncio.wait_for(accepted.wait(), 3)
            assert requests == 1
            callers[0].cancel()
            callers[1].cancel()
            await asyncio.gather(*callers[:2], return_exceptions=True)
            assert not disconnected.is_set(), "remaining caller still needs this read"
            callers[2].cancel()
            await asyncio.gather(callers[2], return_exceptions=True)
            await asyncio.wait_for(disconnected.wait(), 3)
            replacement = await asyncio.wait_for(coordinator.run("http", "new", "same", fetch), 3)
            assert replacement == "fresh evidence"
            assert requests == 2
            assert coordinator.stats()["http"]["pending"] == 0
        for _ in range(12):
            await asyncio.sleep(0)
        assert not coordinator._cleanup_tasks
    finally:
        for caller in callers:
            caller.cancel()
        await asyncio.gather(*callers, return_exceptions=True)
        server.close()
        await server.wait_closed()
        for writer in list(writers):
            writer.close()
        if handlers:
            await asyncio.wait_for(asyncio.gather(*handlers), 3)
