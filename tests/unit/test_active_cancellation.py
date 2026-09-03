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


@pytest.mark.asyncio
async def test_new_call_during_cancel_cleanup_starts_fresh_shared_read():
    coordinator = Coordinator({"http": QueuePolicy(4, 4, 1)})
    entered, cleaning, release_cleanup = asyncio.Event(), asyncio.Event(), asyncio.Event()
    replacement_entered, release_replacement = asyncio.Event(), asyncio.Event()
    calls = []

    async def abandoned():
        calls.append("abandoned")
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            cleaning.set()
            await release_cleanup.wait()

    async def replacement():
        calls.append("replacement")
        replacement_entered.set()
        await release_replacement.wait()
        return "fresh evidence"

    first = asyncio.create_task(coordinator.run("http", "a", "same", abandoned))
    tasks = [first]
    try:
        await entered.wait()
        first.cancel()
        await asyncio.gather(first, return_exceptions=True)
        await cleaning.wait()
        second = asyncio.create_task(coordinator.run("http", "b", "same", replacement))
        tasks.append(second)
        await asyncio.sleep(0)
        assert not replacement_entered.is_set(), "cancel cleanup must retain its active slot"
        release_cleanup.set()
        for _ in range(12):
            await asyncio.sleep(0)
        third = asyncio.create_task(coordinator.run("http", "c", "same", replacement))
        tasks.append(third)
        await asyncio.sleep(0)
        release_replacement.set()
        results = await asyncio.wait_for(asyncio.gather(second, third, return_exceptions=True), 1)
        assert results == ["fresh evidence", "fresh evidence"]
        assert calls == ["abandoned", "replacement"], "new callers should share only the replacement"
        assert coordinator.stats()["http"]["pending"] == 0
    finally:
        release_cleanup.set()
        release_replacement.set()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.asyncio
async def test_cancel_after_operation_returns_still_releases_queue_slot():
    coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
    entered, return_result = asyncio.Event(), asyncio.Event()

    async def operation():
        entered.set()
        await return_result.wait()
        return "evidence"

    request = asyncio.create_task(coordinator.run("http", "a", "first", operation))
    await entered.wait()
    # Force waiter detachment ahead of result settlement at the state-lock boundary.
    async with coordinator._state_lock:
        request.cancel()
        await asyncio.sleep(0)
        return_result.set()
        await asyncio.sleep(0)
    await asyncio.gather(request, return_exceptions=True)
    for _ in range(12):
        await asyncio.sleep(0)
    assert coordinator.stats()["http"]["pending"] == 0
    assert await asyncio.wait_for(coordinator.run("http", "b", "next", operation), 1) == "evidence"


@pytest.mark.asyncio
async def test_repeated_caller_cancellation_cannot_abandon_waiter_detachment():
    coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
    entered, stopped, release = asyncio.Event(), asyncio.Event(), asyncio.Event()

    async def operation():
        entered.set()
        try:
            await release.wait()
        finally:
            stopped.set()

    request = asyncio.create_task(coordinator.run("http", "a", "first", operation))
    try:
        await entered.wait()
        async with coordinator._state_lock:
            request.cancel()
            await asyncio.sleep(0)
            request.cancel()
            await asyncio.gather(request, return_exceptions=True)
        for _ in range(12):
            await asyncio.sleep(0)
        assert stopped.is_set(), "repeat cancellation must not strand active upstream work"
        assert coordinator.stats()["http"]["pending"] == 0
    finally:
        release.set()
        request.cancel()
        await asyncio.gather(request, return_exceptions=True)
        for _ in range(12):
            await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_provider_cancelled_before_first_instruction_releases_capacity():
    coordinator = Coordinator({"http": QueuePolicy(2, 2, 1)})
    calls = []

    async def operation():
        calls.append("started")
        return "evidence"

    request = asyncio.create_task(coordinator.run("http", "a", "first", operation))
    await asyncio.sleep(0)
    # Inject cancellation at dispatch, before the provider coroutine can run.
    coordinator._flights[("http", "first")].task.cancel()
    result = await asyncio.wait_for(asyncio.gather(request, return_exceptions=True), 1)
    assert isinstance(result[0], asyncio.CancelledError)
    assert calls == []
    assert coordinator.stats()["http"]["pending"] == 0
    assert await coordinator.run("http", "b", "next", operation) == "evidence"


@pytest.mark.asyncio
async def test_cancel_during_provider_pacing_never_starts_upstream():
    pacing = asyncio.Event()

    class Clock:
        def monotonic(self):
            return 0

        async def sleep(self, seconds):
            assert seconds == 5
            pacing.set()
            await asyncio.Event().wait()

    coordinator = Coordinator({"http": QueuePolicy(2, 2, 1, 5)}, Clock())
    calls = []

    async def operation():
        calls.append("started")
        return "evidence"

    assert await coordinator.run("http", "a", "first", operation) == "evidence"
    request = asyncio.create_task(coordinator.run("http", "b", "second", operation))
    await asyncio.wait_for(pacing.wait(), 1)
    request.cancel()
    await asyncio.gather(request, return_exceptions=True)
    for _ in range(12):
        await asyncio.sleep(0)
    assert calls == ["started"]
    assert coordinator.stats()["http"]["pending"] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("rounds", [1, 25])
async def test_multiple_clients_cancellation_and_errors_leave_no_queue_or_cleanup_leak(rounds):
    coordinator = Coordinator({"http": QueuePolicy(16, 8, 2)})
    running = maximum = calls = 0

    async def operation(key, release):
        nonlocal running, maximum, calls
        running += 1
        calls += 1
        maximum = max(maximum, running)
        try:
            await release.wait()
            if key == 2:
                raise ValueError("fixture upstream error")
            return f"source {key}"
        finally:
            running -= 1

    for number in range(rounds):
        release = asyncio.Event()
        requests = []
        for key in range(4):
            for client in ("a", "b", "c"):
                requests.append(
                    asyncio.create_task(
                        coordinator.run(
                            "http", client, f"{number}:{key}", lambda k=key, gate=release: operation(k, gate)
                        )
                    )
                )
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        # Some reads keep another waiter; one queued read loses every waiter.
        for index in (0, 1, 3, 9, 10, 11):
            requests[index].cancel()
        await asyncio.sleep(0)
        release.set()
        results = await asyncio.wait_for(asyncio.gather(*requests, return_exceptions=True), 2)
        assert all(isinstance(results[i], asyncio.CancelledError) for i in (0, 1, 3, 9, 10, 11))
        assert results[2] == "source 0" and results[4:6] == ["source 1", "source 1"]
        assert all(isinstance(results[i], ValueError) for i in (6, 7, 8))
        for _ in range(12):
            await asyncio.sleep(0)
        assert coordinator.stats()["http"]["pending"] == 0
        assert not coordinator._cleanup_tasks
        assert not coordinator._flights
        assert all(count == 0 for count in coordinator._client_pending.values())
    assert maximum <= 2 and running == 0
    assert calls == rounds * 3
