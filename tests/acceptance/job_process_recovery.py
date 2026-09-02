"""Crash/restart a disposable research worker; never operate on the live Gateway.

Uses isolated storage and deterministic public-source fixtures. This proves native
process/SQLite continuation, not upstream availability or DSH integration.
"""

import asyncio
import json
import multiprocessing
import sqlite3
import tempfile
import time
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.service import HaloService

FIRST = "https://example.org/task-groups"
SECOND = "https://example.org/cancellation"


def config_at(directory):
    root = Path(directory)
    config = GatewayConfig()
    config.storage.database = str(root / "state" / "gateway.db")
    config.storage.backup_directory = str(root / "backups")
    config.storage.content_directory = str(root / "content")
    config.crawl.base_directory = str(root / "browser")
    config.jobs.lease_seconds = 1
    return config


def item(url, content):
    return EvidenceItem(url=url, retrieved_at="2026-09-02T00:00:00Z", content=content)


def worker(directory, channel, job_id=None):
    async def run():
        service = HaloService(config_at(directory))
        entered = asyncio.Event()
        searches, fetches = [], []

        async def search(*args, **kwargs):
            searches.append("search")
            return ProviderResult("fixture", [item(FIRST, ""), item(SECOND, "")])

        async def fetch(url):
            fetches.append(url)
            if url == FIRST:
                return ProviderResult("fixture", [item(url, "A task group cancels siblings after a child fails.")])
            if job_id is None:
                entered.set()
                await asyncio.Event().wait()
            return ProviderResult(
                "fixture", [item(url, "CancelledError should normally be raised again after cleanup.")]
            )

        service.ddgs.search, service.http.fetch = search, fetch
        if job_id is None:
            created = await service.research_job(
                "create",
                "fixture",
                question="task group cancellation",
                limits={"max_sources": 2, "max_pages": 3, "timeout_seconds": 30},
            )
            await asyncio.wait_for(entered.wait(), 5)
            channel.put({"ready_to_interrupt": True, "job_id": created["job_id"], "fetches": fetches})
            await asyncio.Event().wait()
        else:
            before = service.jobs.status(job_id, "fixture")
            await service.research_job("resume", "fixture", job_id=job_id)
            await asyncio.wait_for(service._job_tasks[job_id], 5)
            channel.put(
                {
                    "before": before["state"],
                    "after": service.jobs.status(job_id, "fixture"),
                    "searches": searches,
                    "fetches": fetches,
                }
            )
            await service.close()

    asyncio.run(run())


def main():
    context = multiprocessing.get_context("spawn")
    with tempfile.TemporaryDirectory(prefix="halo-job-recovery-") as directory:
        channel = context.Queue()
        processes = []
        try:
            first = context.Process(target=worker, args=(directory, channel))
            processes.append(first)
            first.start()
            ready = channel.get(timeout=15)
            assert ready["ready_to_interrupt"] and ready["fetches"] == [FIRST, SECOND], ready
            first.terminate()  # Only the Process object created by this fixture.
            first.join(timeout=5)
            assert not first.is_alive(), "owned fixture process did not stop"
            database = config_at(directory).storage.database
            with closing(sqlite3.connect(database)) as db, db:
                state, payload, lease = db.execute(
                    "SELECT state,progress_json,lease_until FROM jobs WHERE job_id=?", (ready["job_id"],)
                ).fetchone()
                assert state == "running", "fixture did not simulate an ungraceful interruption"
                checkpoint = json.loads(payload)["checkpoint"]
                assert [entry["url"] for entry in checkpoint["items"]] == [FIRST]
                assert checkpoint["attempted"] == 2
                db.execute("DELETE FROM cache_entries")  # Disposable fixture storage only.
            delay = max(0, (datetime.fromisoformat(lease) - datetime.now(UTC)).total_seconds())
            time.sleep(min(delay + 0.1, 2))
            second = context.Process(target=worker, args=(directory, channel, ready["job_id"]))
            processes.append(second)
            second.start()
            completed = channel.get(timeout=15)
            second.join(timeout=5)
            assert second.exitcode == 0, second.exitcode
            assert completed["before"] == "paused_recoverable", completed
            assert completed["after"]["state"] == "complete", completed
            assert completed["searches"] == [] and completed["fetches"] == [SECOND], completed
            sources = [entry["url"] for entry in completed["after"]["progress"]["result"]["items"]]
            assert sources == [FIRST, SECOND], sources
            assert completed["after"]["progress"]["checkpoint"]["attempted"] == 3
            verdict = {
                "passed": True,
                "native_process_crash_recovered": True,
                "search_repeated": False,
                "completed_source_refetched": False,
                "attempts": 3,
                "sources": sources,
                "fixture_only": True,
            }
        finally:
            for process in processes:
                if process.is_alive():
                    process.terminate()
                process.join(timeout=5)
            channel.close()
            channel.join_thread()
    print(json.dumps(verdict))


if __name__ == "__main__":
    main()
