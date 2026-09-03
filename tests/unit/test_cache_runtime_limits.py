"""Regression checks for ordinary Gateway cache limits and non-cacheable evidence."""

import gzip
import hashlib
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from datetime import UTC, datetime, timedelta
from threading import Event

import pytest
from pydantic import ValidationError

from halo_research_gateway.cache import Cache
from halo_research_gateway.config import GatewayConfig, StorageConfig
from halo_research_gateway.migrations import migrate
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.service import HaloService


class Clock:
    def __init__(self):
        self.now = datetime(2026, 9, 3, 5, tzinfo=UTC)

    def __call__(self):
        return self.now

    def advance(self, seconds=1):
        self.now += timedelta(seconds=seconds)


def sample(name):
    body = "".join(hashlib.sha256(f"{name}-{i}".encode()).hexdigest() for i in range(40))
    return ProviderResult(
        "fixture",
        [
            EvidenceItem(
                url=f"https://example.org/{name}",
                retrieved_at="2026-09-03T05:00:00Z",
                content=body,
            )
        ],
    )


@pytest.fixture
async def service(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    instance = HaloService(config)
    instance.cache.clock = Clock()
    try:
        yield instance
    finally:
        await instance.close()


async def store_result(service, key, ttl=60):
    async def operation():
        return sample(key)

    return await service._cached_run("http", "fixture", key, ttl, operation)


async def test_ordinary_writes_enforce_total_limit_and_preserve_recent_reads(service):
    sizes = [len(gzip.compress(service._encode_result(sample(key)))) for key in ("a", "b", "c")]
    service.cache.max_bytes = max(sizes) * 2 + 10
    for key in ("a", "b"):
        await store_result(service, key)
        service.cache.clock.advance()
    assert service.cache.get("a")
    service.cache.clock.advance()
    await store_result(service, "c")
    assert service.cache.stats()["total_compressed_bytes"] <= service.cache.max_bytes, (
        "Ordinary writes bypass total cache cap"
    )
    assert service.cache.get("b") is None, "Least recently used research result survived eviction"
    assert service.cache.get("a") and service.cache.get("c")


@pytest.mark.parametrize("trigger", ["hit", "miss", "write"])
async def test_ordinary_traffic_removes_other_expired_results(service, trigger):
    await store_result(service, "expired", ttl=1)
    await store_result(service, "fresh", ttl=100)
    service.cache.clock.advance(2)
    if trigger == "write":
        await store_result(service, "new")
    else:
        service.cache.get("fresh" if trigger == "hit" else "missing")
    with closing(sqlite3.connect(service.cache.db_path)) as db:
        count = db.execute("SELECT COUNT(*) FROM cache_entries WHERE cache_key='expired'").fetchone()[0]
    assert count == 0, "Expired payload remains stored after ordinary cache traffic"


async def test_expiry_boundary_is_not_served_as_fresh(service):
    await store_result(service, "expired", ttl=1)
    service.cache.clock.advance(1)
    assert service.cache.get("expired") is None, "Entry at expires_at was still served"


async def test_read_reconciles_preexisting_over_limit_cache_without_touching_rate_state(service):
    service.cache.max_bytes = 2500
    with closing(sqlite3.connect(service.cache.db_path)) as db:
        db.execute("INSERT INTO rate_state(bucket_key) VALUES ('cache-bound-fixture')")
        db.commit()
    # Simulates pre-upgrade data through the existing low-level manual-eviction API.
    legacy = Cache(service.cache.db_path, 10000, 10000, service.cache.clock)
    for key in ("old-a", "old-b", "old-c"):
        legacy.put(key, service._encode_result(sample(key)), 60)
        service.cache.clock.advance()
    assert service.cache.stats()["total_compressed_bytes"] > service.cache.max_bytes
    service.cache.get("missing")
    assert service.cache.stats()["total_compressed_bytes"] <= service.cache.max_bytes, (
        "Old over-limit cache not reconciled"
    )
    with closing(sqlite3.connect(service.cache.db_path)) as db:
        assert db.execute("SELECT COUNT(*) FROM rate_state WHERE bucket_key='cache-bound-fixture'").fetchone()[0] == 1


@pytest.mark.parametrize("limit", ["entry", "total"])
async def test_oversized_cache_entry_does_not_hide_readable_evidence(service, limit):
    setattr(service.cache, "entry_max_bytes" if limit == "entry" else "max_bytes", 100)
    result = sample("large")

    async def fetch(url):
        return result

    service.http.fetch = fetch
    first = await service.web_fetch(result.items[0].url, max_chars=2000)
    assert first["ok"], f"Cache admission failure hid usable evidence: {first.get('error')}"
    assert first["cache"]["key"] == "", "Uncached response advertises a disk-recoverable key"
    assert "RESULT_NOT_CACHED_TOO_LARGE" in first["warnings"]
    content, page = "", first
    for _ in range(100):
        assert page["ok"] and len(json.dumps(page, indent=2, ensure_ascii=False)) <= 2000
        content += "".join(row.get("content") or "" for row in page["items"])
        cursor = page["page"]["next_cursor"]
        if not cursor:
            break
        page = await service.web_fetch(cursor=cursor)
    else:
        pytest.fail("Uncached evidence did not complete pagination")
    assert content == result.items[0].content
    assert service.cache.stats()["entries"] == 0
    config, cursor = service.config, first["page"]["next_cursor"]
    await service.close()
    restarted = HaloService(config)
    try:
        gone = await restarted.web_fetch(cursor=cursor)
        assert not gone["ok"] and gone["error"]["code"] == "CURSOR_EVICTED", "Uncached evidence was recovered from disk"
    finally:
        await restarted.close()


@pytest.mark.parametrize("limit", ["entry", "total"])
async def test_job_evidence_survives_cache_admission_rejection(service, limit):
    setattr(service.cache, "entry_max_bytes" if limit == "entry" else "max_bytes", 100)
    status = {
        "state": "complete",
        "error_code": None,
        "progress": {"checkpoint": {"items": [sample("job").items[0].as_dict()], "warnings": []}},
    }
    error = None
    try:
        view = service._job_status_view(status)
    except Exception as exc:
        view, error = None, str(exc)
    assert error is None, f"Completed job evidence hidden by cache capacity: {error}"
    assert view["progress"]["result"]["ok"]
    assert view["progress"]["result"]["cache"]["key"] == ""
    assert "RESULT_NOT_CACHED_TOO_LARGE" in view["progress"]["result"]["warnings"]


@pytest.mark.parametrize("field", ["cache_max_bytes", "entry_max_bytes"])
@pytest.mark.parametrize("value", [0, -1])
def test_storage_cache_limits_must_be_positive(field, value):
    rejected = False
    try:
        StorageConfig.model_validate({field: value})
    except ValidationError:
        rejected = True
    assert rejected, f"{field} accepted nonpositive capacity"


def test_max_age_miss_keeps_unexpired_evidence(tmp_path):
    db = tmp_path / "gateway.db"
    migrate(str(db), str(tmp_path / "backups"))
    clock = Clock()
    cache = Cache(str(db), 10000, 10000, clock)
    cache.put("fresh", b"evidence", 100)
    clock.advance(2)
    assert cache.get("fresh", max_age_seconds=1) is None
    assert cache.get("fresh", max_age_seconds=5) == b"evidence"


@pytest.mark.parametrize("trigger", ["hit", "miss", "write", "maintenance"])
async def test_lowered_entry_limit_removes_preexisting_oversized_rows(service, trigger):
    await store_result(service, "old")
    service.cache.entry_max_bytes = 100
    if trigger == "write":
        await store_result(service, "new")
    elif trigger == "maintenance":
        service.cache.evict()
    else:
        value = service.cache.get("old" if trigger == "hit" else "missing")
        assert value is None, "Old oversized cache entry was served after lowering the entry limit"
    assert service.cache.stats()["entries"] == 0, "Entry limit ignored for previously stored rows"


async def test_bounded_write_never_commits_a_transient_over_limit_state(service, monkeypatch):
    cache = service.cache
    cache.max_bytes = 3000
    cache.put("first", service._encode_result(sample("first")), 60)
    reached, release = Event(), Event()
    evict = cache._evict_in_transaction

    def hold_before_prune(conn, now):
        reached.set()
        assert release.wait(5), "Atomic cache probe was not released"
        evict(conn, now)

    monkeypatch.setattr(cache, "_evict_in_transaction", hold_before_prune)
    with ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(cache.put, "second", service._encode_result(sample("second")), 60)
        try:
            assert reached.wait(5), "Writer did not reach pre-prune point"
            assert cache.stats()["total_compressed_bytes"] <= cache.max_bytes, "Other connection saw unpruned write"
        finally:
            release.set()
        future.result(timeout=5)
    assert cache.stats()["total_compressed_bytes"] <= cache.max_bytes


async def test_failed_prune_rolls_back_the_insert(service, monkeypatch):
    cache = service.cache
    cache.put("first", b"retained", 60)

    def fail(conn, now):
        raise RuntimeError("fixture eviction failure")

    with monkeypatch.context() as scoped:
        scoped.setattr(cache, "_evict_in_transaction", fail)
        with pytest.raises(RuntimeError, match="fixture eviction failure"):
            cache.put("second", b"not committed", 60)
    assert cache.get("first") == b"retained"
    assert cache.get("second") is None


async def test_concurrent_bounded_writers_share_one_observable_limit(service):
    db = service.cache.db_path
    cap, samples = 5000, []

    def writer(number):
        cache = Cache(db, cap, 10000, enforce_limits=True)
        for index in range(12):
            value = service._encode_result(sample(f"{number}-{index}"))
            cache.put(f"{number}-{index}", value, 60)
            assert cache.stats()["total_compressed_bytes"] <= cap

    observer = Cache(db, cap, 10000)
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(writer, number) for number in range(6)]
        while not all(future.done() for future in futures):
            samples.append(observer.stats()["total_compressed_bytes"])
        for future in futures:
            future.result(timeout=5)
    assert samples and max(samples) <= cap, "Concurrent observers saw cache overshoot"
    assert 0 < observer.stats()["total_compressed_bytes"] <= cap


async def test_cache_stats_expose_the_enforced_limits(service):
    stats = service.cache.stats()
    assert stats.get("max_bytes") == service.cache.max_bytes, "Total cache cap is not visible"
    assert stats.get("entry_max_bytes") == service.cache.entry_max_bytes, "Entry cap is not visible"
