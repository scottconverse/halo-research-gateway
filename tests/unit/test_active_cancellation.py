import asyncio

import pytest

from halo_research_gateway.coordinator import Coordinator, QueuePolicy


@pytest.mark.asyncio
async def test_last_cancelled_waiter_stops_active_upstream_and_releases_capacity():
    coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
    entered, stopped, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def operation():
        entered.set()
        try:
            await release.wait()
        finally:
            stopped.set()

    request = asyncio.create_task(coordinator.run("http", "a", "key", operation))
    try:
        await entered.wait()
        request.cancel()
        with pytest.raises(asyncio.CancelledError):
            await request
        for _ in range(5):
            await asyncio.sleep(0)
        assert stopped.is_set()
        assert coordinator.stats()["http"]["pending"] == 0
    finally:
        release.set()
        for _ in range(5):
            await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_one_cancelled_waiter_does_not_cancel_another_clients_shared_read():
    coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
    entered, stopped, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        entered.set()
        try:
            await release.wait()
            return "shared evidence"
        finally:
            stopped.set()

    first = asyncio.create_task(coordinator.run("http", "a", "key", operation))
    await entered.wait()
    second = asyncio.create_task(coordinator.run("http", "b", "key", operation))
    await asyncio.sleep(0)
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    assert not stopped.is_set()
    release.set()
    assert await second == "shared evidence"
    assert calls == 1
    assert coordinator.stats()["http"]["pending"] == 0
