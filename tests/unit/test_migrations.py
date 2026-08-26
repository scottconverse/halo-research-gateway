# Gate-authored acceptance tests (frozen). The worker implements src/ to make
# these pass and may not modify this file. Authored by the conductor 2026-08-25.
import os
import sqlite3
from contextlib import closing

import pytest

from halo_research_gateway.cache_errors import SchemaTooNewError
from halo_research_gateway.migrations import migrate


def _tables(db):
    with closing(sqlite3.connect(db)) as c:
        rows = c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    return {r[0] for r in rows}


def test_migrate_creates_schema(tmp_path):
    db = tmp_path / "gateway.db"
    migrate(str(db), str(tmp_path / "backups"))
    assert {"schema_meta", "cache_entries", "rate_state", "request_log"} <= _tables(db)
    with closing(sqlite3.connect(db)) as c:
        assert c.execute("PRAGMA user_version").fetchone()[0] >= 1


def test_migrate_second_run_noop(tmp_path):
    db = tmp_path / "gateway.db"
    backups = tmp_path / "backups"
    migrate(str(db), str(backups))
    with closing(sqlite3.connect(db)) as c:
        v1 = c.execute("PRAGMA user_version").fetchone()[0]
    n1 = len(list(backups.glob("*.db"))) if backups.exists() else 0
    migrate(str(db), str(backups))
    with closing(sqlite3.connect(db)) as c:
        v2 = c.execute("PRAGMA user_version").fetchone()[0]
    n2 = len(list(backups.glob("*.db"))) if backups.exists() else 0
    assert v2 == v1
    assert n2 == n1  # nothing applied on the second run -> no new backup


def test_schema_too_new_error(tmp_path):
    db = tmp_path / "gateway.db"
    with closing(sqlite3.connect(db)) as c:
        c.execute("PRAGMA user_version = 999")
        c.commit()
    before = db.read_bytes()
    with pytest.raises(SchemaTooNewError):
        migrate(str(db), str(tmp_path / "backups"))
    assert db.read_bytes() == before  # refused BEFORE any backup or write
    bdir = tmp_path / "backups"
    assert (not bdir.exists()) or not any(bdir.iterdir())


def test_backup_created_and_capped(tmp_path):
    backups = tmp_path / "backups"
    backups.mkdir()
    for i, name in enumerate(["a.db", "b.db", "c.db"]):  # stale backups, a.db oldest
        p = backups / name
        p.write_bytes(b"old")
        os.utime(p, (1000 + i, 1000 + i))
    db = tmp_path / "gateway.db"
    with closing(sqlite3.connect(db)) as c:  # existing unmigrated db -> must be backed up
        c.execute("PRAGMA user_version = 0")
        c.commit()
    migrate(str(db), str(backups))
    remaining = sorted(f.name for f in backups.glob("*.db"))
    assert len(remaining) == 3      # 3 stale + 1 new, pruned to the 3 newest
    assert "a.db" not in remaining  # the oldest was pruned
