"""SQLite-backed cache for Halo Research Gateway."""

import gzip
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta

from halo_research_gateway.cache_errors import EntryTooLargeError


class Cache:
    """SQLite-backed cache with TTL and LRU eviction."""

    def __init__(self, db_path: str, max_bytes: int, entry_max_bytes: int, clock=None):
        """
        Initialize the cache.

        Args:
            db_path: Path to SQLite database file
            max_bytes: Maximum total bytes to use for cached entries
            entry_max_bytes: Maximum size (in bytes) for a single cache entry
            clock: Callable returning UTC datetime (defaults to datetime.utcnow)
        """
        self.db_path = db_path
        self.max_bytes = max_bytes
        self.entry_max_bytes = entry_max_bytes
        self.clock = clock or (lambda: datetime.now(UTC))

    def put(self, key: str, value: bytes, ttl_seconds: int) -> None:
        """
        Store a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to store (bytes)
            ttl_seconds: Time-to-live in seconds

        Raises:
            EntryTooLargeError: If the compressed entry exceeds entry_max_bytes
        """
        # Compress the value
        try:
            compressed_value = gzip.compress(value)
        except Exception as e:
            raise EntryTooLargeError(f"Failed to compress entry: {str(e)}") from e

        if len(compressed_value) > self.entry_max_bytes:
            raise EntryTooLargeError(
                f"Entry size {len(compressed_value)} exceeds maximum allowed {self.entry_max_bytes} bytes"
            )

        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")

            # Calculate expiry time
            now = self.clock()
            expires_at = (now + timedelta(seconds=ttl_seconds)).isoformat()
            created_at = now.isoformat()
            last_accessed_at = created_at

            # Store the entry with inline storage
            conn.execute(
                """
                INSERT OR REPLACE INTO cache_entries (
                    cache_key, 
                    payload,
                    compressed_bytes,
                    uncompressed_bytes,
                    expires_at,
                    created_at,
                    last_accessed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    key,  # cache_key
                    compressed_value,  # payload (inline_payload)
                    len(compressed_value),  # compressed_bytes
                    len(value),  # uncompressed_bytes
                    expires_at,
                    created_at,
                    last_accessed_at,
                ),
            )

            conn.commit()

    def get(self, key: str, max_age_seconds: int | None = None) -> bytes | None:
        entry = self.get_with_age(key, max_age_seconds)
        return entry[0] if entry is not None else None

    def get_with_age(self, key: str, max_age_seconds: int | None = None) -> tuple[bytes, int] | None:
        """
        Retrieve a value from cache.

        Args:
            key: Cache key
            max_age_seconds: If specified, return None if entry is older than this

        Returns:
            The original bytes if found and not expired, otherwise None
        """
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")

            # Get the cache entry
            cursor = conn.execute(
                """
                SELECT payload, uncompressed_bytes, expires_at,
                       created_at FROM cache_entries WHERE cache_key = ?
            """,
                (key,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            compressed_value, uncompressed_size, expires_at_str, created_at_str = row

            # Check expiration
            now = self.clock()
            expires_at = datetime.fromisoformat(expires_at_str)

            if now > expires_at:
                return None

            # If max_age_seconds is specified and entry is too old, return None
            if max_age_seconds is not None:
                created_at = datetime.fromisoformat(created_at_str)
                age_seconds = (now - created_at).total_seconds()
                if age_seconds > max_age_seconds:
                    return None

            # Update last accessed time
            conn.execute(
                """
                UPDATE cache_entries SET last_accessed_at = ?
                WHERE cache_key = ?
            """,
                (now.isoformat(), key),
            )
            conn.commit()

            # Decompress and return value
            created_at = datetime.fromisoformat(created_at_str)
            age_seconds = max(0, int((now - created_at).total_seconds()))
            return gzip.decompress(compressed_value), age_seconds

    def evict(self) -> None:
        now = self.clock().isoformat()
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            # 1. expired entries first
            conn.execute("DELETE FROM cache_entries WHERE expires_at <= ?", (now,))
            conn.commit()
            # 2. then least-recently-accessed until the total fits
            while True:
                total = conn.execute("SELECT COALESCE(SUM(compressed_bytes), 0) FROM cache_entries").fetchone()[0]
                if total <= self.max_bytes:
                    break
                row = conn.execute(
                    "SELECT cache_key FROM cache_entries ORDER BY last_accessed_at ASC, rowid ASC LIMIT 1"
                ).fetchone()
                if row is None:
                    break  # nothing left to remove
                conn.execute("DELETE FROM cache_entries WHERE cache_key = ?", (row[0],))
                conn.commit()

    def delete(self, key: str) -> None:
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("DELETE FROM cache_entries WHERE cache_key = ?", (key,))
            conn.commit()

    def stats(self) -> dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dict with "entries" and "total_compressed_bytes"
        """
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("PRAGMA journal_mode=WAL")

            cursor = conn.execute("""
                SELECT COUNT(*), SUM(compressed_bytes) FROM cache_entries
            """)
            count, size = cursor.fetchone()

            return {"entries": count or 0, "total_compressed_bytes": size or 0}
