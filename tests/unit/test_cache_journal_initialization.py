"""Cache requests must not compete to change a live database's journal mode."""

import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier, Event

import pytest

from halo_research_gateway.cache import Cache
from halo_research_gateway.migrations import migrate


def test_cache_is_ready_before_another_connection_starts_reading(tmp_path):
    db = str(tmp_path / "gateway.db")
    migrate(db, str(tmp_path / "backups"))
    cache = Cache(db, 10000, 10000, enforce_limits=True)
    error = None
    with closing(sqlite3.connect(db)) as reader:
        reader.execute("BEGIN")
        reader.execute("SELECT COUNT(*) FROM cache_entries").fetchone()
        try:
            assert cache.stats()["entries"] == 0
            cache.put("source", b"readable evidence", 60)
            assert cache.get("source") == b"readable evidence"
            cache.evict()
            # A concurrent reader keeps its original snapshot until it commits.
            assert reader.execute("SELECT COUNT(*) FROM cache_entries").fetchone()[0] == 0
        except sqlite3.OperationalError as exc:
            error = str(exc)
        finally:
            reader.rollback()
    assert error is None, f"Ordinary cache request tried to reconfigure a live database: {error}"
    assert cache.get("source") == b"readable evidence"


def test_simultaneous_first_cache_owners_preserve_all_committed_results(tmp_path):
    db = str(tmp_path / "gateway.db")
    migrate(db, str(tmp_path / "backups"))
    start = Barrier(8)

    def owner(number):
        start.wait(timeout=5)
        cache = Cache(db, 10000, 10000, enforce_limits=True)
        cache.put(str(number), str(number).encode(), 60)
        return cache.get(str(number))

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(owner, number) for number in range(8)]
        assert [future.result(timeout=10) for future in futures] == [str(i).encode() for i in range(8)]
    assert Cache(db, 10000, 10000).stats()["entries"] == 8


def test_initialization_waits_for_a_short_existing_transaction(tmp_path):
    db = str(tmp_path / "gateway.db")
    migrate(db, str(tmp_path / "backups"))
    entered = Event()

    def owner():
        entered.set()
        cache = Cache(db, 10000, 10000, enforce_limits=True)
        cache.put("source", b"evidence", 60)
        return cache.get("source")

    with closing(sqlite3.connect(db)) as writer, ThreadPoolExecutor(max_workers=1) as pool:
        writer.execute("BEGIN IMMEDIATE")
        future = pool.submit(owner)
        try:
            assert entered.wait(5)
            # SQLite keeps a write lock until rollback; release it while the
            # other owner is starting, not after its connection times out.
        finally:
            writer.rollback()
        assert future.result(timeout=10) == b"evidence"


def test_initialization_contention_has_a_deadline(tmp_path, monkeypatch):
    db = str(tmp_path / "gateway.db")
    migrate(db, str(tmp_path / "backups"))
    monkeypatch.setattr(Cache, "journal_timeout_seconds", 0.05, raising=False)
    with closing(sqlite3.connect(db)) as reader:
        reader.execute("BEGIN")
        reader.execute("SELECT COUNT(*) FROM cache_entries").fetchone()
        started = time.monotonic()
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            Cache(db, 10000, 10000)
        assert time.monotonic() - started < 1, "Journal initialization exceeded its bounded wait"
        reader.rollback()
