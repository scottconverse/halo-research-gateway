import asyncio
from datetime import UTC, datetime, timedelta

import pytest

from halo_research_gateway.actions.store import ActionStore
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
async def test_action_requires_approval_and_is_idempotent(tmp_path):
    store = ActionStore(database(tmp_path))
    prepared = store.prepare({"action": "post", "target_url": "https://example.com/post", "fields": {"body": "hello"}})
    calls = 0

    async def executor(plan):
        nonlocal calls
        calls += 1
        return {"status": "submitted"}

    with pytest.raises(PermissionError, match="ACTION_APPROVAL_REQUIRED"):
        await store.execute(prepared["plan_id"], "wrong", "one", executor)
    token = store.approve(prepared["plan_id"])
    first = await store.execute(prepared["plan_id"], token, "one", executor)
    second = await store.execute(prepared["plan_id"], token, "one", executor)
    assert first == second
    assert calls == 1


@pytest.mark.asyncio
async def test_generic_form_action_executes_once_after_exact_approval(tmp_path):
    from halo_research_gateway.config import GatewayConfig
    from halo_research_gateway.service import HaloService

    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    calls = 0

    async def submit(url, fields):
        nonlocal calls
        calls += 1
        return {"status": "submitted", "http_status": 204}

    service.http.submit_form = submit
    plan = service.web_action_prepare(
        "form_submit", "https://example.com/contact", "Send inquiry", {"message": "hello"}
    )
    token = service.actions.approve(plan["plan_id"])
    first = await service.web_action_execute(plan["plan_id"], token, "one-submit")
    second = await service.web_action_execute(plan["plan_id"], token, "one-submit")
    assert first == second
    assert first["outcome"]["status"] == "submitted"
    assert calls == 1
    await service.close()


@pytest.mark.asyncio
async def test_singleflight_runs_one_upstream_call():
    coordinator = Coordinator({"http": QueuePolicy(4, 4, 2)})
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
