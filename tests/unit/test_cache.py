# Gate-authored acceptance tests (frozen). The worker implements src/ to make
# these pass and may not modify this file. Authored by the conductor 2026-08-25.
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta, timezone

import pytest

from halo_research_gateway.cache import Cache
from halo_research_gateway.cache_errors import EntryTooLargeError
from halo_research_gateway.migrations import migrate


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc)

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)

    def __call__(self):
        return self.now


def make_cache(tmp_path, max_bytes=1_000_000, entry_max_bytes=100_000):
    db = tmp_path / "gateway.db"
    migrate(str(db), str(tmp_path / "backups"))  # Cache never auto-migrates
    clock = FakeClock()
    cache = Cache(str(db), max_bytes=max_bytes, entry_max_bytes=entry_max_bytes, clock=clock)
    return cache, clock, db


def test_cache_requires_migrated_database(tmp_path):
    cache, clock, db = make_cache(tmp_path)
    cache.put("k", b"v", ttl_seconds=60)
    assert cache.get("k") == b"v"


def test_put_get_roundtrip(tmp_path):
    cache, clock, _ = make_cache(tmp_path)
    text = ("compressible " * 1000).encode()
    rand = os.urandom(2048)
    cache.put("text", text, ttl_seconds=3600)
    cache.put("rand", rand, ttl_seconds=3600)
    assert cache.get("text") == text
    assert cache.get("rand") == rand


def test_expiry_ttl(tmp_path):
    cache, clock, _ = make_cache(tmp_path)
    cache.put("k", b"v", ttl_seconds=60)
    clock.advance(61)
    assert cache.get("k") is None


def test_max_age_stricter_than_ttl(tmp_path):
    cache, clock, _ = make_cache(tmp_path)
    cache.put("k", b"v", ttl_seconds=3600)
    clock.advance(120)
    assert cache.get("k", max_age_seconds=60) is None   # too old for the caller
    assert cache.get("k", max_age_seconds=300) == b"v"  # a max_age miss must not delete


def test_oversize_entry_rejected(tmp_path):
    cache, clock, _ = make_cache(tmp_path, entry_max_bytes=100)
    with pytest.raises(EntryTooLargeError):
        cache.put("big", os.urandom(10_000), ttl_seconds=60)


def test_lru_eviction_order(tmp_path):
    cache, clock, _ = make_cache(tmp_path, max_bytes=9000)
    a, b, c = os.urandom(4096), os.urandom(4096), os.urandom(4096)
    cache.put("a", a, ttl_seconds=3600)
    clock.advance(10)
    cache.put("b", b, ttl_seconds=3600)
    clock.advance(10)
    cache.put("c", c, ttl_seconds=3600)
    clock.advance(10)
    assert cache.get("a") == a  # refreshes a's last_accessed_at
    clock.advance(10)
    cache.evict()               # ~12.3KB stored, limit 9000 -> exactly one must go
    assert cache.get("b") is None  # least recently accessed
    assert cache.get("a") == a
    assert cache.get("c") == c


def test_evict_preserves_rate_state(tmp_path):
    cache, clock, db = make_cache(tmp_path, max_bytes=100)
    with closing(sqlite3.connect(db)) as conn:
        conn.execute("INSERT INTO rate_state (bucket_key) VALUES ('reddit')")
        conn.commit()
    cache.put("k", os.urandom(300), ttl_seconds=3600)  # incompressible, over max_bytes
    cache.evict()
    assert cache.get("k") is None
    with closing(sqlite3.connect(db)) as conn:
        assert conn.execute("SELECT COUNT(*) FROM rate_state").fetchone()[0] == 1


def test_stats_counts_and_bytes(tmp_path):
    cache, clock, _ = make_cache(tmp_path)
    cache.put("a", b"x" * 1000, ttl_seconds=3600)
    cache.put("b", os.urandom(500), ttl_seconds=3600)
    s = cache.stats()
    assert s["entries"] == 2
    assert s["total_compressed_bytes"] > 0
