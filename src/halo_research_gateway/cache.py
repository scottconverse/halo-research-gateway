"""SQLite-backed cache for Halo Research Gateway."""

import gzip
import sqlite3
import time
from contextlib import closing
from datetime import UTC, datetime, timedelta

from halo_research_gateway.cache_errors import EntryTooLargeError


class Cache:
    """SQLite-backed cache with TTL and LRU eviction."""

    journal_timeout_seconds = 5.0

    def __init__(self, db_path: str, max_bytes: int, entry_max_bytes: int, clock=None, *, enforce_limits: bool = False):
        """
        Initialize the cache.

        Args:
            db_path: Path to SQLite database file
            max_bytes: Maximum total bytes to use for cached entries
            entry_max_bytes: Maximum size (in bytes) for a single cache entry
            clock: Callable returning UTC datetime (defaults to datetime.utcnow)
            enforce_limits: Atomically bound every write. HaloService always
                enables this; the low-level manual-eviction API stays compatible.
        """
        self.db_path = db_path
        self.max_bytes = max_bytes
        self.entry_max_bytes = entry_max_bytes
        self.clock = clock or (lambda: datetime.now(UTC))
        self.enforce_limits = enforce_limits
        self._initialize_journal()

    def _initialize_journal(self) -> None:
        """Prepare persistent WAL before requests, with bounded startup contention.

        Simultaneous first owners can lose SQLite's read-to-exclusive journal
        transition immediately, even with a busy timeout. Retry only SQLITE_BUSY
        on a fresh connection; never reconfigure the journal in the request path.
        """
        deadline = time.monotonic() + self.journal_timeout_seconds
        while True:
            try:
                with closing(sqlite3.connect(self.db_path, timeout=max(0, deadline - time.monotonic()))) as conn:
                    if conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal":
                        return
                    if conn.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() != "wal":
                        raise sqlite3.OperationalError("Cache database does not support WAL journal mode")
                    return
            except sqlite3.OperationalError as exc:
                remaining = deadline - time.monotonic()
                if getattr(exc, "sqlite_errorcode", 0) & 0xFF != sqlite3.SQLITE_BUSY or remaining <= 0:
                    raise
                time.sleep(min(0.01, remaining))

    def put(self, key: str, value: bytes, ttl_seconds: int) -> None:
        """
        Store a value in cache with TTL.

        Args:
            key: Cache key
            value: Value to store (bytes)
            ttl_seconds: Time-to-live in seconds

        Raises:
            EntryTooLargeError: If the compressed entry exceeds an admission limit
        """
        # Compress the value
        try:
            compressed_value = gzip.compress(value)
        except Exception as e:
            raise EntryTooLargeError(f"Failed to compress entry: {str(e)}") from e

        limit = min(self.entry_max_bytes, self.max_bytes) if self.enforce_limits else self.entry_max_bytes
        if len(compressed_value) > limit:
            raise EntryTooLargeError(f"Entry size {len(compressed_value)} exceeds maximum allowed {limit} bytes")

        with closing(sqlite3.connect(self.db_path)) as conn:
            if self.enforce_limits:
                conn.execute("BEGIN IMMEDIATE")

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

            if self.enforce_limits:
                self._evict_in_transaction(conn, now.isoformat())
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
            conn.execute("BEGIN IMMEDIATE")

            # Get the cache entry
            cursor = conn.execute(
                """
                SELECT payload, uncompressed_bytes, expires_at,
                       created_at FROM cache_entries WHERE cache_key = ?
            """,
                (key,),
            )

            row = cursor.fetchone()
            now = self.clock()
            usable = False
            if row:
                compressed_value, _, expires_at_str, created_at_str = row
                age_seconds = max(0, (now - datetime.fromisoformat(created_at_str)).total_seconds())
                usable = (
                    len(compressed_value) <= min(self.entry_max_bytes, self.max_bytes)
                    and now < datetime.fromisoformat(expires_at_str)
                    and (max_age_seconds is None or age_seconds <= max_age_seconds)
                )
                if usable:
                    # Touch before pruning so an accessed pre-upgrade entry is
                    # considered recent. A max-age miss alone never deletes it.
                    conn.execute(
                        "UPDATE cache_entries SET last_accessed_at = ? WHERE cache_key = ?", (now.isoformat(), key)
                    )
            self._evict_in_transaction(conn, now.isoformat())
            conn.commit()
            if usable:
                return gzip.decompress(compressed_value), int(age_seconds)
            return None

    def _evict_in_transaction(self, conn, now: str) -> None:
        """Prune only cache rows, inside the caller's serialized transaction."""
        conn.execute(
            "DELETE FROM cache_entries WHERE expires_at <= ? OR compressed_bytes > ?",
            (now, min(self.entry_max_bytes, self.max_bytes)),
        )
        conn.execute(
            """
            WITH newest_first AS (
                SELECT cache_key, SUM(compressed_bytes) OVER (
                    ORDER BY last_accessed_at DESC, rowid DESC
                ) AS retained_bytes
                FROM cache_entries
            )
            DELETE FROM cache_entries WHERE cache_key IN (
                SELECT cache_key FROM newest_first WHERE retained_bytes > ?
            )
            """,
            (self.max_bytes,),
        )

    def evict(self) -> None:
        now = self.clock().isoformat()
        with closing(sqlite3.connect(self.db_path)) as conn:
            conn.execute("BEGIN IMMEDIATE")
            self._evict_in_transaction(conn, now)
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
            cursor = conn.execute("""
                SELECT COUNT(*), SUM(compressed_bytes) FROM cache_entries
            """)
            count, size = cursor.fetchone()

            return {
                "entries": count or 0,
                "total_compressed_bytes": size or 0,
                "max_bytes": self.max_bytes,
                "entry_max_bytes": self.entry_max_bytes,
            }
