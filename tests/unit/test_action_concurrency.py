import asyncio

import pytest

from halo_research_gateway.actions.store import ActionStore
from halo_research_gateway.migrations import migrate


def database(tmp_path):
    path = tmp_path / "gateway.db"
    migrate(str(path), str(tmp_path / "backups"))
    return str(path)


@pytest.mark.asyncio
async def test_concurrent_different_keys_invoke_executor_once(tmp_path):
    store = ActionStore(database(tmp_path))
    prepared = store.prepare({"action": "post", "target_url": "https://example.com/post"})
    token = store.approve(prepared["plan_id"])
    entered = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def executor(plan):
        nonlocal calls
        calls += 1
        entered.set()
        await release.wait()
        return {"status": "submitted"}

    first = asyncio.create_task(store.execute(prepared["plan_id"], token, "first-key", executor))
    await entered.wait()
    second = asyncio.create_task(store.execute(prepared["plan_id"], token, "second-key", executor))
    try:
        await asyncio.sleep(0)
        assert calls == 1
    finally:
        release.set()
        results = await asyncio.gather(first, second, return_exceptions=True)

    assert sum(isinstance(result, PermissionError) for result in results) == 1
    assert calls == 1


@pytest.mark.asyncio
async def test_durable_reservation_blocks_a_second_store_instance(tmp_path):
    db_path = database(tmp_path)
    first_store = ActionStore(db_path)
    second_store = ActionStore(db_path)
    prepared = first_store.prepare({"action": "post", "target_url": "https://example.com/post"})
    token = first_store.approve(prepared["plan_id"])
    entered = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def executor(plan):
        nonlocal calls
        calls += 1
        entered.set()
        await release.wait()
        return {"status": "submitted"}

    first = asyncio.create_task(first_store.execute(prepared["plan_id"], token, "first-key", executor))
    await entered.wait()
    with pytest.raises(PermissionError, match="ACTION_ALREADY_EXECUTED"):
        await second_store.execute(prepared["plan_id"], token, "second-key", executor)
    release.set()
    await first
    assert calls == 1


@pytest.mark.asyncio
async def test_executor_exception_records_ambiguous_receipt_without_replay(tmp_path):
    store = ActionStore(database(tmp_path))
    prepared = store.prepare({"action": "post", "target_url": "https://example.com/post"})
    token = store.approve(prepared["plan_id"])
    calls = 0

    async def executor(plan):
        nonlocal calls
        calls += 1
        raise TimeoutError("upstream detail containing secret-value")

    first = await store.execute(prepared["plan_id"], token, "first-key", executor)
    replay = await store.execute(prepared["plan_id"], token, "first-key", executor)

    assert first == replay
    assert first["outcome"] == {"status": "ambiguous", "error_code": "ACTION_EXECUTION_AMBIGUOUS"}
    assert "secret-value" not in repr(first)
    assert store.list_receipts() == [first]
    assert calls == 1
    with pytest.raises(PermissionError, match="ACTION_ALREADY_EXECUTED"):
        await store.execute(prepared["plan_id"], token, "second-key", executor)


@pytest.mark.asyncio
async def test_cancelled_execution_records_ambiguous_receipt(tmp_path):
    store = ActionStore(database(tmp_path))
    prepared = store.prepare({"action": "post", "target_url": "https://example.com/post"})
    token = store.approve(prepared["plan_id"])
    entered = asyncio.Event()
    calls = 0

    async def executor(plan):
        nonlocal calls
        calls += 1
        entered.set()
        await asyncio.Future()

    task = asyncio.create_task(store.execute(prepared["plan_id"], token, "first-key", executor))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task

    [receipt] = store.list_receipts()
    assert receipt["outcome"] == {"status": "ambiguous", "error_code": "ACTION_EXECUTION_AMBIGUOUS"}
    assert await store.execute(prepared["plan_id"], token, "first-key", executor) == receipt
    assert calls == 1
