"""Paused jobs must resume persisted evidence, not repeat a fresh research run."""

import asyncio
import json
import sqlite3
from datetime import timedelta

import pytest
from test_job_lifecycle import service_at
from test_v15_state import FakeClock

from halo_research_gateway.models import EvidenceItem, ProviderResult


def evidence(url, content):
    return EvidenceItem(url=url, retrieved_at="2026-09-02T00:00:00Z", content=content)


@pytest.mark.asyncio
@pytest.mark.parametrize("page_budget", [2, 3])
async def test_restart_keeps_completed_sources_frontier_and_total_page_budget(tmp_path, page_budget):
    first = service_at(tmp_path)
    entered = asyncio.Event()
    first_url, second_url = "https://example.org/first", "https://example.org/second"
    searches = 0

    async def search(*args, **kwargs):
        nonlocal searches
        searches += 1
        return ProviderResult("fixture", [evidence(first_url, ""), evidence(second_url, "")])

    async def initial_fetch(url):
        if url == first_url:
            return ProviderResult("fixture", [evidence(url, "First source says cancelled tasks must clean up.")])
        entered.set()
        await asyncio.Event().wait()

    first.ddgs.search, first.http.fetch = search, initial_fetch
    resumed = None
    try:
        job = await first.research_job(
            "create", "planner", question="task cancellation", limits={"max_sources": 2, "max_pages": page_budget}
        )
        await asyncio.wait_for(entered.wait(), 3)
        await first.research_job("pause", "planner", job_id=job["job_id"])
        paused = first.jobs.status(job["job_id"], "planner")
        saved = paused["progress"].get("checkpoint", {})
        assert [item["url"] for item in saved.get("items", [])] == [first_url]
        assert saved["position"] == 1
        assert saved["attempted"] == 2
        await first.close()
        # This is an isolated fixture DB: remove cache so it cannot disguise re-fetching.
        with sqlite3.connect(first.config.storage.database) as db:
            db.execute("DELETE FROM cache_entries")
        resumed = service_at(tmp_path)
        fetched = []

        async def resumed_fetch(url):
            fetched.append(url)
            return ProviderResult(
                "fixture", [evidence(url, "Second source explains sibling cancellation in a task group.")]
            )

        resumed.ddgs.search, resumed.http.fetch = search, resumed_fetch
        await resumed.research_job("resume", "planner", job_id=job["job_id"])
        await asyncio.wait_for(resumed._job_tasks[job["job_id"]], 3)
        status = resumed.jobs.status(job["job_id"], "planner")
        assert status["state"] == "complete"
        assert searches == 1, "resume repeated source discovery"
        assert fetched == ([second_url] if page_budget == 3 else [])
        result = status["progress"]["result"]
        assert first_url in [item["url"] for item in result["items"]]
        if page_budget == 2:
            assert "PAGE_LIMIT_REACHED" in result["warnings"]
            assert status["progress"]["partial"] is True
        else:
            assert second_url in [item["url"] for item in result["items"]]
    finally:
        await first.close()
        if resumed:
            await resumed.close()


@pytest.mark.asyncio
async def test_resume_cannot_reset_an_exhausted_total_time_budget(tmp_path):
    service = service_at(tmp_path)
    calls = []

    async def research(*args, **kwargs):
        calls.append("started")
        return {"ok": True, "items": [{"url": "https://example.org/source"}]}

    service.deep_research = research
    try:
        job = service.jobs.create("planner", "sources", {"max_sources": 2, "max_pages": 3, "timeout_seconds": 1})
        service.jobs.transition(job["job_id"], "planner", "pause")
        with sqlite3.connect(service.config.storage.database) as db:
            db.execute(
                "UPDATE jobs SET progress_json=? WHERE job_id=?",
                (json.dumps({"checkpoint": {"elapsed_seconds": 1.0}}), job["job_id"]),
            )
        await service.research_job("resume", "planner", job_id=job["job_id"])
        await service._job_tasks[job["job_id"]]
        status = service.jobs.status(job["job_id"], "planner")
        assert calls == [], "resuming reset the consumed time budget"
        assert status["state"] == "failed"
        assert status["error_code"] == "JOB_TIMEOUT"
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_live_worker_renews_lease_and_pause_stops_renewal(tmp_path):
    service = service_at(tmp_path)
    service.config.jobs.lease_seconds = 1
    entered = asyncio.Event()

    async def research(*args, **kwargs):
        entered.set()
        await asyncio.Event().wait()

    service.deep_research = research
    try:
        job = await service.research_job("create", "planner", question="sources")
        await entered.wait()
        original_lease = service.jobs.status(job["job_id"], "planner")["lease_until"]
        for _ in range(20):
            await asyncio.sleep(0.1)
            current = service.jobs.status(job["job_id"], "planner")
            if current["lease_until"] != original_lease:
                break
        assert current["lease_until"] > original_lease
        assert service.jobs.recover_expired() == 0
        await service.research_job("pause", "planner", job_id=job["job_id"])
        paused = service.jobs.status(job["job_id"], "planner")
        assert paused["progress"]["checkpoint"]["elapsed_seconds"] > 0
        await asyncio.sleep(0.4)
        assert service.jobs.status(job["job_id"], "planner") == paused
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_distinct_jobs_still_share_the_deep_provider_limit(tmp_path):
    service = service_at(tmp_path)
    entered = asyncio.Event()
    calls = 0

    async def search(*args, **kwargs):
        nonlocal calls
        calls += 1
        entered.set()
        await asyncio.Event().wait()

    service.ddgs.search = search
    try:
        await service.research_job("create", "planner", question="first")
        await service.research_job("create", "worker", question="second")
        await entered.wait()
        for _ in range(10):
            await asyncio.sleep(0)
        assert calls == 1, "durable jobs bypassed the existing shared deep-research limit"
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_expired_crash_lease_is_recoverable_on_status_and_charges_uncertain_time(tmp_path):
    service = service_at(tmp_path)
    clock = FakeClock()
    service.jobs.clock = clock
    try:
        job = service.jobs.create("planner", "sources", {"timeout_seconds": 10})
        service.jobs.start(job["job_id"], "planner", 3)
        service.jobs.heartbeat(job["job_id"], "planner", 2, 3)
        clock.now += timedelta(seconds=4)
        status = await service.research_job("status", "planner", job_id=job["job_id"])
        assert status["state"] == "paused_recoverable"
        assert status["lease_until"] is None
        assert status["progress"]["checkpoint"]["elapsed_seconds"] == 5
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_checkpoint_bound_keeps_prior_evidence_and_fails_honestly(tmp_path):
    service = service_at(tmp_path)
    service.config.storage.entry_max_bytes = 4096

    async def search(*args, **kwargs):
        return ProviderResult("fixture", [evidence("https://example.org/large", "")])

    async def fetch(url):
        return ProviderResult("fixture", [evidence(url, "evidence " * 10000)])

    service.ddgs.search, service.http.fetch = search, fetch
    try:
        job = await service.research_job("create", "planner", question="sources")
        await service._job_tasks[job["job_id"]]
        status = service.jobs.status(job["job_id"], "planner")
        assert status["state"] == "failed"
        assert status["error_code"] == "JOB_CHECKPOINT_TOO_LARGE"
        assert len(json.dumps(status["progress"]["checkpoint"]).encode()) <= 4096
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_known_sensitive_source_and_link_urls_are_not_persisted_in_jobs(tmp_path):
    service = service_at(tmp_path)
    safe = "https://example.org/source"
    sensitive = "https://example.org/export?token=fixture-secret-value"
    fetched = []

    async def search(*args, **kwargs):
        return ProviderResult("fixture", [evidence(sensitive, ""), evidence(safe, "")])

    async def fetch(url):
        fetched.append(url)
        page = evidence(url, "Public source evidence")
        page.metadata = {"links": [("private export", sensitive)]}
        return ProviderResult("fixture", [page])

    service.ddgs.search, service.http.fetch = search, fetch
    try:
        job = await service.research_job("create", "planner", question="public evidence")
        await service._job_tasks[job["job_id"]]
        status = service.jobs.status(job["job_id"], "planner")
        assert sensitive not in fetched
        assert "fixture-secret-value" not in json.dumps(status)
        assert "SENSITIVE_SOURCE_NOT_PERSISTED" in status["progress"]["result"]["warnings"]
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_startup_recovers_a_job_persisted_before_worker_start(tmp_path):
    first = service_at(tmp_path)
    job = first.jobs.create("planner", "queued before interruption", {"timeout_seconds": 10})
    await first.close()
    restarted = service_at(tmp_path)
    try:
        status = restarted.jobs.status(job["job_id"], "planner")
        assert status["state"] == "paused_recoverable"
        assert status["lease_until"] is None
        assert status["progress"]["checkpoint"].get("elapsed_seconds", 0) == 0
    finally:
        await restarted.close()


@pytest.mark.asyncio
async def test_public_job_status_is_bounded_and_retained_evidence_is_pageable(tmp_path):
    service = service_at(tmp_path)
    source = "https://example.org/retained"
    try:
        job = service.jobs.create("planner", "bounded status", {"timeout_seconds": 30})
        service.jobs.start(job["job_id"], "planner", 30)
        service.jobs.checkpoint(
            job["job_id"],
            "planner",
            {
                "items": [evidence(source, "Evidence with citation. " * 4000).as_dict()],
                "frontier": [[source, 0, "example.org"]],
                "position": 1,
                "attempted": 1,
                "elapsed_seconds": 0.5,
                "search_complete": True,
                "warnings": [],
            },
            service.config.storage.entry_max_bytes,
        )
        status = await service.research_job("status", "planner", job_id=job["job_id"])
        assert len(json.dumps(status, indent=2)) <= 6000
        assert "items" not in status["progress"]["checkpoint"]
        result = status["progress"]["result"]
        assert result["items"][0]["url"] == source
        assert result["page"]["next_cursor"]
        continuation = await service.deep_research("", cursor=result["page"]["next_cursor"], max_chars=4000)
        assert continuation["ok"] and continuation["items"][0]["url"] == source
        await service.close()
        restarted = service_at(tmp_path)
        try:
            continued_after_restart = await restarted.deep_research(
                "",
                cursor=result["page"]["next_cursor"],
                max_chars=4000,
            )
            assert continued_after_restart["ok"]
            assert continued_after_restart["items"][0]["url"] == source
        finally:
            await restarted.close()
    finally:
        await service.close()
