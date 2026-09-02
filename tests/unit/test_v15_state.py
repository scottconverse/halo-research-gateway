import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from halo_research_gateway.connections.import_reviews import ImportReviewStore
from halo_research_gateway.connections.store import ConnectionStore
from halo_research_gateway.connections.vault import Vault
from halo_research_gateway.coordinator import Coordinator, QueueFullError, QueuePolicy
from halo_research_gateway.jobs.manager import JobManager
from halo_research_gateway.migrations import migrate
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.rate_limit import ProviderBudgetExhausted, ProviderCircuitOpen, RateLedger


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 9, 1, tzinfo=UTC)
        self.tick = 0.0

    def utcnow(self):
        return self.now

    def monotonic(self):
        return self.tick

    async def sleep(self, seconds):
        self.tick += seconds
        self.now += timedelta(seconds=seconds)


class RecordingClock(FakeClock):
    def __init__(self):
        super().__init__()
        self.sleeps = []

    async def sleep(self, seconds):
        self.sleeps.append(seconds)
        await super().sleep(seconds)


def database(tmp_path):
    path = tmp_path / "gateway.db"
    migrate(str(path), str(tmp_path / "backups"))
    return str(path)


def test_vault_round_trip_is_encrypted(tmp_path):
    vault = Vault(tmp_path / "vault")
    reference = vault.put({"token": "not-plaintext"})
    blob = (tmp_path / "vault" / f"{reference}.dpapi").read_bytes()
    assert b"not-plaintext" not in blob
    assert vault.get(reference) == {"token": "not-plaintext"}


def test_connection_metadata_never_returns_secret_and_can_be_revoked(tmp_path):
    store = ConnectionStore(database(tmp_path), tmp_path / "vault")
    created = store.create("github", "Scott", "token", {"token": "top-secret"}, ["repo"])
    assert "secret" not in repr(created).lower()
    assert "top-secret" not in repr(store.list())
    assert store.secret(created["connection_id"])["token"] == "top-secret"
    assert store.revoke(created["connection_id"])["status"] == "revoked"
    with pytest.raises(PermissionError, match="CONNECTION_REVOKED"):
        store.secret(created["connection_id"])


def test_jobs_are_bounded_owned_and_controllable(tmp_path):
    jobs = JobManager(database(tmp_path))
    created = jobs.create("planner", "find sources", {"pages": 20, "minutes": 5})
    assert created["state"] == "queued"
    assert jobs.transition(created["job_id"], "planner", "pause")["state"] == "paused"
    with pytest.raises(PermissionError, match="JOB_NOT_OWNED"):
        jobs.status(created["job_id"], "worker")


def test_job_can_persist_completion_evidence(tmp_path):
    jobs = JobManager(database(tmp_path))
    created = jobs.create("planner", "find sources", {"pages": 2})
    assert jobs.start(created["job_id"], "planner", 30)["state"] == "running"
    finished = jobs.finish(created["job_id"], "planner", {"sources": 2})
    assert finished["state"] == "complete"
    assert finished["progress"] == {"sources": 2}


def test_rate_budget_and_circuit_survive_new_ledger_instance(tmp_path):
    db = database(tmp_path)
    clock = FakeClock()
    first = RateLedger(db, clock)
    assert first.admit("exa", 1) == 1
    with pytest.raises(ProviderBudgetExhausted):
        RateLedger(db, clock).admit("exa", 1)
    first.admit("reddit")
    first.rate_limited("reddit", threshold=1, cooldown_seconds=60)
    with pytest.raises(ProviderCircuitOpen):
        RateLedger(db, clock).admit("reddit")


@pytest.mark.asyncio
async def test_session_import_requires_approval_and_is_idempotent(tmp_path):
    store = ImportReviewStore(database(tmp_path))
    prepared = store.prepare({"action": "chrome_import", "import": {"categories": ["cookies"]}})
    calls = 0

    async def executor(plan):
        nonlocal calls
        calls += 1
        return {"status": "imported"}

    with pytest.raises(PermissionError, match="IMPORT_APPROVAL_REQUIRED"):
        await store.execute(prepared["plan_id"], "wrong", "one", executor)
    token = store.approve(prepared["plan_id"])
    first = await store.execute(prepared["plan_id"], token, "one", executor)
    second = await store.execute(prepared["plan_id"], token, "one", executor)
    assert first == second
    assert calls == 1


@pytest.mark.asyncio
async def test_singleflight_runs_one_upstream_call():
    coordinator = Coordinator({"http": QueuePolicy(1, 1, 1)})
    calls = 0

    async def operation():
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        return "ok"

    assert await asyncio.gather(
        coordinator.run("http", "a", "same", operation),
        coordinator.run("http", "b", "same", operation),
    ) == ["ok", "ok"]
    assert calls == 1


@pytest.mark.asyncio
async def test_queue_rejects_per_client_overflow():
    coordinator = Coordinator({"http": QueuePolicy(2, 1, 1)})
    entered = asyncio.Event()
    release = asyncio.Event()

    async def blocked():
        entered.set()
        await release.wait()

    first = asyncio.create_task(coordinator.run("http", "a", "one", blocked))
    await entered.wait()
    with pytest.raises(QueueFullError):
        await coordinator.run("http", "a", "two", blocked)
    release.set()
    await first


@pytest.mark.asyncio
async def test_queue_is_round_robin_across_clients_and_fifo_within_each_client():
    clock = RecordingClock()
    coordinator = Coordinator({"http": QueuePolicy(5, 3, 1, 5)}, clock)
    first_entered = asyncio.Event()
    release_first = asyncio.Event()
    started = []

    def operation(name):
        async def run():
            started.append(name)
            if name == "a0":
                first_entered.set()
                await release_first.wait()
            return name

        return run

    first = asyncio.create_task(coordinator.run("http", "a", "a0", operation("a0")))
    await first_entered.wait()
    queued = [
        asyncio.create_task(coordinator.run("http", "a", "a1", operation("a1"))),
        asyncio.create_task(coordinator.run("http", "a", "a2", operation("a2"))),
        asyncio.create_task(coordinator.run("http", "b", "b1", operation("b1"))),
        asyncio.create_task(coordinator.run("http", "b", "b2", operation("b2"))),
    ]
    await asyncio.sleep(0)
    release_first.set()

    assert await asyncio.gather(first, *queued) == ["a0", "a1", "a2", "b1", "b2"]
    assert started == ["a0", "b1", "a1", "b2", "a2"]
    assert clock.sleeps == [5, 5, 5, 5]


@pytest.mark.asyncio
async def test_cancelling_a_queued_request_removes_it_before_execution():
    coordinator = Coordinator({"http": QueuePolicy(3, 3, 1)})
    first_entered = asyncio.Event()
    release_first = asyncio.Event()
    cancelled_started = False

    async def first_operation():
        first_entered.set()
        await release_first.wait()

    async def cancelled_operation():
        nonlocal cancelled_started
        cancelled_started = True

    first = asyncio.create_task(coordinator.run("http", "a", "first", first_operation))
    await first_entered.wait()
    queued = asyncio.create_task(coordinator.run("http", "b", "cancelled", cancelled_operation))
    await asyncio.sleep(0)
    queued.cancel()
    with pytest.raises(asyncio.CancelledError):
        await queued
    release_first.set()
    await first
    await asyncio.sleep(0)

    assert cancelled_started is False
    assert coordinator.stats()["http"]["pending"] == 0


@pytest.mark.asyncio
async def test_service_reuses_cached_snapshot_without_second_upstream_call(tmp_path):
    from halo_research_gateway.config import GatewayConfig
    from halo_research_gateway.service import HaloService

    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    calls = 0

    async def fetch(url):
        nonlocal calls
        calls += 1
        return ProviderResult(
            "fixture",
            [EvidenceItem(url=url, retrieved_at="2026-09-01T00:00:00Z", content="evidence")],
            available=1,
        )

    service.http.fetch = fetch
    first = await service.web_fetch("https://example.com/cache-proof")
    second = await service.web_fetch("https://example.com/cache-proof")
    assert calls == 1
    assert first["cache"]["hit"] is False
    assert second["cache"]["hit"] is True
    assert second["cache"]["key"] == first["cache"]["key"]
    await service.close()


@pytest.mark.asyncio
async def test_cursor_continuation_uses_saved_snapshot_and_rejects_tampering(tmp_path):
    from halo_research_gateway.config import GatewayConfig
    from halo_research_gateway.service import HaloService

    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    calls = 0

    async def fetch(url):
        nonlocal calls
        calls += 1
        return ProviderResult(
            "fixture",
            [EvidenceItem(url=url, retrieved_at="2026-09-01T00:00:00Z", content="x" * 9000)],
            available=1,
        )

    service.http.fetch = fetch
    first = await service.web_fetch("https://example.com/long", max_chars=2000)
    cursor = first["page"]["next_cursor"]
    assert cursor
    second = await service.web_fetch(cursor=cursor)
    assert second["ok"] is True
    assert second["page"]["number"] == 2
    assert calls == 1
    broken = cursor[:-1] + ("A" if cursor[-1] != "A" else "B")
    rejected = await service.web_fetch(cursor=broken)
    assert rejected["ok"] is False
    assert rejected["error"]["code"] == "CURSOR_INVALID"
    await service.close()
