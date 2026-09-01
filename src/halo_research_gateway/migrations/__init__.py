"""Database migrations for Halo Research Gateway."""

import os
import sqlite3
import time
from contextlib import closing

from halo_research_gateway.cache_errors import SchemaTooNewError

SCHEMA_VERSION = 2


def migrate(db_path: str, backup_dir: str) -> None:
    """Apply all pending migrations to the database at db_path.

    Args:
        db_path: Path to the SQLite database file
        backup_dir: Directory where backups will be stored

    Raises:
        SchemaTooNewError: If the existing database schema version is newer
                          than what this code understands
    """
    # Open connection to get current user_version FIRST (no writes before check)
    with closing(sqlite3.connect(db_path)) as conn:
        cursor = conn.execute("PRAGMA user_version")
        current_version = cursor.fetchone()[0]

        # If schema is newer than what we support, raise error BEFORE any changes
        if current_version > SCHEMA_VERSION:
            raise SchemaTooNewError(
                f"Database schema version {current_version} is newer than supported version {SCHEMA_VERSION}"
            )

    # Ensure backup directory exists AFTER the version check but before any writes
    os.makedirs(backup_dir, exist_ok=True)

    # Create backup of existing db (if it exists and has content or is an empty DB with version 0)
    if os.path.exists(db_path) and current_version >= 0:
        _create_backup(db_path, backup_dir)

    # Apply migrations as needed
    with closing(sqlite3.connect(db_path)) as conn:
        if current_version < 1:
            _migrate_to_v1(conn)
        if current_version < 2:
            _migrate_to_v2(conn)


def _create_backup(db_path: str, backup_dir: str) -> None:
    """Create a backup of the database using SQLite's backup API."""

    # Create new backup file name with timestamp following test expectation format
    stamp = int(time.time())
    backup_filename = f"gateway-{stamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)

    # Use SQLite's backup API to create the backup (this is what the tests expect)
    with closing(sqlite3.connect(db_path)) as source_conn:
        with closing(sqlite3.connect(backup_path)) as dest_conn:
            source_conn.backup(dest_conn)

    # Prune backups - list all .db files, sort by modification time, delete oldest ones
    try:
        db_files = []
        for filename in os.listdir(backup_dir):
            if filename.endswith(".db"):
                fullpath = os.path.join(backup_dir, filename)
                mtime = os.path.getmtime(fullpath)
                # Only consider gateway- prefixed files (new backups) and legacy ones
                db_files.append((filename, mtime))

        # Sort by modification time (newest first)
        db_files.sort(key=lambda x: x[1], reverse=True)

        # Remove oldest ones if we have more than 3
        if len(db_files) > 3:
            for filename, _ in db_files[3:]:
                try:
                    os.remove(os.path.join(backup_dir, filename))
                except OSError:
                    pass

    except OSError:
        pass


def _migrate_to_v1(conn: sqlite3.Connection) -> None:
    """Migrate database to version 1."""

    # Create schema_meta table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_meta (
            component TEXT PRIMARY KEY,
            version INTEGER NOT NULL, 
            updated_at TEXT NOT NULL
        )
    """)

    # Create cache_entries table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache_entries (
            cache_key TEXT PRIMARY KEY,
            payload BLOB NOT NULL,
            compressed_bytes INTEGER NOT NULL,
            uncompressed_bytes INTEGER NOT NULL,
            expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_accessed_at TEXT NOT NULL
        )
    """)

    # Create rate_state table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS rate_state (
            bucket_key TEXT PRIMARY KEY,
            last_started_at TEXT,
            window_started_at TEXT,
            request_count INTEGER NOT NULL DEFAULT 0,
            consecutive_429 INTEGER NOT NULL DEFAULT 0,
            circuit_state TEXT NOT NULL DEFAULT 'closed',
            circuit_until TEXT
        )
    """)

    # Create request_log table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS request_log (
            request_id TEXT PRIMARY KEY,
            tool TEXT NOT NULL,
            provider TEXT NOT NULL,
            cache_key TEXT,
            started_at TEXT NOT NULL,
            completed_at TEXT,
            outcome TEXT,
            upstream_status INTEGER,
            duration_ms INTEGER,
            cache_hit INTEGER NOT NULL DEFAULT 0,
            warning_codes TEXT
        )
    """)

    # Update schema version
    conn.execute("PRAGMA user_version = 1")

    # Insert initial schema_meta entry
    conn.execute("""
        INSERT OR REPLACE INTO schema_meta (component, version, updated_at) 
        VALUES ('cache', 1, datetime('now'))
    """)


def _migrate_to_v2(conn: sqlite3.Connection) -> None:
    """Add durable v1.5 connections, targets, jobs, actions, and receipts."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS connections (
            connection_id TEXT PRIMARY KEY,
            provider TEXT NOT NULL,
            account_label TEXT NOT NULL,
            capability_json TEXT NOT NULL,
            vault_ref TEXT NOT NULL,
            created_at TEXT NOT NULL,
            verified_at TEXT,
            revoked_at TEXT
        );
        CREATE TABLE IF NOT EXISTS local_targets (
            target_id TEXT PRIMARY KEY,
            policy_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            revoked_at TEXT
        );
        CREATE TABLE IF NOT EXISTS jobs (
            job_id TEXT PRIMARY KEY,
            owner_profile TEXT NOT NULL,
            request_json TEXT NOT NULL,
            limits_json TEXT NOT NULL,
            state TEXT NOT NULL,
            progress_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            lease_until TEXT,
            error_code TEXT
        );
        CREATE TABLE IF NOT EXISTS action_plans (
            plan_id TEXT PRIMARY KEY,
            plan_hash TEXT NOT NULL,
            plan_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            approval_digest TEXT,
            approval_expires_at TEXT,
            consumed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS action_receipts (
            receipt_id TEXT PRIMARY KEY,
            plan_id TEXT NOT NULL,
            idempotency_key TEXT NOT NULL UNIQUE,
            outcome TEXT NOT NULL,
            receipt_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(plan_id) REFERENCES action_plans(plan_id)
        );
        CREATE INDEX IF NOT EXISTS jobs_state_idx ON jobs(state);
        CREATE INDEX IF NOT EXISTS actions_hash_idx ON action_plans(plan_hash);
    """)
    conn.execute("PRAGMA user_version = 2")
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta(component, version, updated_at) VALUES ('gateway', 2, datetime('now'))"
    )
    conn.commit()
