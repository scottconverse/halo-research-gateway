"""Debug script for cache issues"""

import tempfile
import os
from datetime import datetime, timedelta, timezone

# Import Cache 
import sys
sys.path.insert(0, '.')

from halo_research_gateway.cache import Cache
from halo_research_gateway.migrations import migrate


class FakeClock:
    def __init__(self):
        self.now = datetime(2026, 8, 25, 12, 0, 0, tzinfo=timezone.utc)

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)

    def __call__(self):
        return self.now


def test_lru_eviction():
    """Test LRU eviction order"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        migrate(db_path, os.path.join(tmpdir, "backups"))
        
        clock = FakeClock()
        cache = Cache(db_path, max_bytes=9000, entry_max_bytes=100_000, clock=clock)
        
        # Put three entries of ~4KB each
        a, b, c = os.urandom(4096), os.urandom(4096), os.urandom(4096)
        cache.put("a", a, ttl_seconds=3600)
        clock.advance(10)
        cache.put("b", b, ttl_seconds=3600)
        clock.advance(10)
        cache.put("c", c, ttl_seconds=3600)
        clock.advance(10)
        
        # Access "a" so it becomes MRU
        result = cache.get("a")
        assert result == a
        
        print(f"Before eviction: {cache.stats()}")
        cache.evict()
        print(f"After eviction: {cache.stats()}")
        
        # Check what's left
        print(f"'a' in cache: {cache.get('a') is not None}")
        print(f"'b' in cache: {cache.get('b') is not None}") 
        print(f"'c' in cache: {cache.get('c') is not None}")


if __name__ == "__main__":
    test_lru_eviction()
