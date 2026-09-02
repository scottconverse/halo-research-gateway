"""Research jobs must stop, stay bounded, and report failed retrieval honestly."""

import asyncio

import pytest

from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.service import HaloService


def service_at(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return HaloService(config)


@pytest.mark.asyncio
async def test_pause_stops_worker_before_return_and_resume_starts_only_one(tmp_path):
    service = service_at(tmp_path)
    entered, stopped, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    calls = 0

    async def research(*args, **kwargs):
        nonlocal calls
        calls += 1
        entered.set()
        try:
            await release.wait()
            return {"ok": True, "items": [{"url": "https://example.org/source"}]}
        finally:
            stopped.set()

    service.deep_research = research
    try:
        job = await service.research_job("create", "planner", question="find sources")
        await entered.wait()
        paused = await service.research_job("pause", "planner", job_id=job["job_id"])
        assert paused["state"] == "paused"
        assert stopped.is_set(), "pause returned while the worker was still running"
        assert job["job_id"] not in service._job_tasks
        entered.clear()
        await service.research_job("resume", "planner", job_id=job["job_id"])
        await entered.wait()
        with pytest.raises(ValueError, match="JOB_STATE_CONFLICT"):
            await service.research_job("resume", "planner", job_id=job["job_id"])
        assert calls == 2
        worker = service._job_tasks[job["job_id"]]
        release.set()
        await worker
        assert service.jobs.status(job["job_id"], "planner")["state"] == "complete"
    finally:
        release.set()
        await service.close()


@pytest.mark.asyncio
async def test_failed_research_envelope_marks_job_failed_not_complete(tmp_path):
    service = service_at(tmp_path)

    async def research(*args, **kwargs):
        return {"ok": False, "error": {"code": "UPSTREAM_UNAVAILABLE"}, "items": []}

    service.deep_research = research
    try:
        job = await service.research_job("create", "planner", question="find sources")
        await service._job_tasks[job["job_id"]]
        status = service.jobs.status(job["job_id"], "planner")
        assert status["state"] == "failed"
        assert status["error_code"] == "UPSTREAM_UNAVAILABLE"
        assert status["progress"]["result"]["ok"] is False
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_job_active_limit_rejects_without_creating_another_record(tmp_path):
    service = service_at(tmp_path)
    service.config.jobs.max_active = 1
    entered, release = asyncio.Event(), asyncio.Event()

    async def research(*args, **kwargs):
        entered.set()
        await release.wait()
        return {"ok": True}

    service.deep_research = research
    try:
        await service.research_job("create", "planner", question="first")
        await entered.wait()
        with pytest.raises(ValueError, match="JOB_CAPACITY_REACHED"):
            await service.research_job("create", "worker", question="second")
        assert len(service.jobs.list()) == 1
    finally:
        release.set()
        await service.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("limits", [{"max_sources": 0}, {"max_pages": -1}, {"timeout_seconds": 0}])
async def test_invalid_job_limits_are_rejected_before_record_creation(tmp_path, limits):
    service = service_at(tmp_path)
    try:
        with pytest.raises(ValueError, match="INVALID_JOB_LIMITS"):
            await service.research_job("create", "planner", question="find sources", limits=limits)
        assert service.jobs.list() == []
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_terminal_job_cannot_resume_and_late_finish_cannot_overwrite_pause(tmp_path):
    service = service_at(tmp_path)
    try:
        job = service.jobs.create("planner", "sources", {})
        service.jobs.start(job["job_id"], "planner", 30)
        service.jobs.transition(job["job_id"], "planner", "pause")
        late = service.jobs.finish(job["job_id"], "planner", {}, "JOB_TIMEOUT")
        assert late["state"] == "paused"
        service.jobs.transition(job["job_id"], "planner", "cancel")
        with pytest.raises(ValueError, match="JOB_STATE_CONFLICT"):
            service.jobs.transition(job["job_id"], "planner", "resume")
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_shutdown_leaves_interrupted_job_recoverable_immediately(tmp_path):
    service = service_at(tmp_path)
    entered = asyncio.Event()

    async def research(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    service.deep_research = research
    job = await service.research_job("create", "planner", question="find sources")
    await entered.wait()
    await service.close()
    status = service.jobs.status(job["job_id"], "planner")
    assert status["state"] == "paused_recoverable"
    assert status["lease_until"] is None


@pytest.mark.asyncio
async def test_pause_cancels_real_deep_pipeline_and_http_operation(tmp_path):
    service = service_at(tmp_path)
    entered, stopped = asyncio.Event(), asyncio.Event()

    async def search(*args, **kwargs):
        return ProviderResult(
            "fixture", [EvidenceItem(url="https://example.org/source", retrieved_at="2026-09-02T00:00:00Z")]
        )

    async def fetch(*args, **kwargs):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    service.ddgs.search = search
    service.http.fetch = fetch
    try:
        job = await service.research_job("create", "planner", question="find sources")
        await asyncio.wait_for(entered.wait(), 3)
        await service.research_job("pause", "planner", job_id=job["job_id"])
        assert stopped.is_set()
        assert service.coordinator.stats()["deep"]["pending"] == 0
        assert service.coordinator.stats()["http"]["pending"] == 0
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_simultaneous_creates_obey_shared_job_capacity(tmp_path):
    service = service_at(tmp_path)
    service.config.jobs.max_active = 1
    release = asyncio.Event()

    async def research(*args, **kwargs):
        await release.wait()
        return {"ok": True}

    service.deep_research = research
    try:
        results = await asyncio.gather(
            service.research_job("create", "planner", question="first"),
            service.research_job("create", "worker", question="second"),
            return_exceptions=True,
        )
        assert sum(isinstance(result, dict) for result in results) == 1
        assert sum(isinstance(result, ValueError) for result in results) == 1
        assert len(service.jobs.list()) == 1
    finally:
        release.set()
        await service.close()


@pytest.mark.asyncio
async def test_pause_before_worker_starts_remains_paused_and_terminal_stays_terminal(tmp_path):
    service = service_at(tmp_path)
    try:
        job = await service.research_job("create", "planner", question="find sources")
        await service.research_job("pause", "planner", job_id=job["job_id"])
        assert service.jobs.status(job["job_id"], "planner")["state"] == "paused"
        await service.research_job("cancel", "planner", job_id=job["job_id"])
        with pytest.raises(ValueError, match="JOB_STATE_CONFLICT"):
            await service.research_job("resume", "planner", job_id=job["job_id"])
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_empty_research_is_failed_and_partial_evidence_remains_marked(tmp_path):
    service = service_at(tmp_path)
    outcome = {"ok": True, "items": [], "warnings": ["SEARCH_UNAVAILABLE"]}

    async def research(*args, **kwargs):
        return outcome

    service.deep_research = research
    try:
        empty = await service.research_job("create", "planner", question="no sources")
        await service._job_tasks[empty["job_id"]]
        status = service.jobs.status(empty["job_id"], "planner")
        assert status["state"] == "failed"
        assert status["error_code"] == "NO_RESEARCH_EVIDENCE"
        outcome["items"] = [{"url": "https://example.org/source", "content": "Some evidence"}]
        partial = await service.research_job("create", "planner", question="some sources")
        await service._job_tasks[partial["job_id"]]
        status = service.jobs.status(partial["job_id"], "planner")
        assert status["state"] == "complete"
        assert status["progress"]["partial"] is True
        assert status["progress"]["result"]["warnings"] == ["SEARCH_UNAVAILABLE"]
    finally:
        await service.close()
