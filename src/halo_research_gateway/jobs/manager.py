"""Durable job lifecycle with explicit finite limits and paused crash recovery."""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import timedelta

from ..clock import SystemClock, rfc3339


class JobManager:
    def __init__(self, db_path: str, clock=None) -> None:
        self.db_path = db_path
        self.clock = clock or SystemClock()

    def create(self, owner: str, question: str, limits: dict) -> dict:
        if not question.strip():
            raise ValueError("INVALID_ARGUMENT")
        job_id = str(uuid.uuid4())
        now = rfc3339(self.clock.utcnow())
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "INSERT INTO jobs VALUES (?,?,?,?,?,?,?,?,?,?)",
                (
                    job_id,
                    owner,
                    json.dumps({"question": question}),
                    json.dumps(limits),
                    "queued",
                    "{}",
                    now,
                    now,
                    None,
                    None,
                ),
            )
        return self.status(job_id, owner)

    def status(self, job_id: str, owner: str) -> dict:
        with sqlite3.connect(self.db_path) as db:
            row = db.execute("SELECT * FROM jobs WHERE job_id=?", (job_id,)).fetchone()
        if row is None:
            raise KeyError("JOB_NOT_FOUND")
        if row[1] != owner:
            raise PermissionError("JOB_NOT_OWNED")
        return {
            "job_id": row[0],
            "owner": row[1],
            "request": json.loads(row[2]),
            "limits": json.loads(row[3]),
            "state": row[4],
            "progress": json.loads(row[5]),
            "created_at": row[6],
            "updated_at": row[7],
            "lease_until": row[8],
            "error_code": row[9],
        }

    def transition(self, job_id: str, owner: str, operation: str) -> dict:
        self.status(job_id, owner)
        target = {"pause": "paused", "resume": "queued", "cancel": "cancelled"}.get(operation)
        if target is None:
            raise ValueError("INVALID_ARGUMENT")
        now = rfc3339(self.clock.utcnow())
        with sqlite3.connect(self.db_path) as db:
            allowed = {
                "pause": ("queued", "running", "paused", "paused_recoverable"),
                "resume": ("paused", "paused_recoverable"),
                "cancel": ("queued", "running", "paused", "paused_recoverable", "cancelled"),
            }[operation]
            placeholders = ",".join("?" for _ in allowed)
            changed = db.execute(
                "UPDATE jobs SET state=?,updated_at=?,lease_until=NULL,error_code=NULL "
                f"WHERE job_id=? AND owner_profile=? AND state IN ({placeholders})",
                (target, now, job_id, owner, *allowed),
            )
            if changed.rowcount != 1:
                raise ValueError("JOB_STATE_CONFLICT")
        return self.status(job_id, owner)

    def start(self, job_id: str, owner: str, lease_seconds: int) -> dict:
        current = self.status(job_id, owner)
        if current["state"] not in {"queued", "paused_recoverable"}:
            return current
        now = self.clock.utcnow()
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "UPDATE jobs SET state='running',updated_at=?,lease_until=? WHERE job_id=? "
                "AND state IN ('queued','paused_recoverable')",
                (rfc3339(now), rfc3339(now + timedelta(seconds=lease_seconds)), job_id),
            )
        return self.status(job_id, owner)

    def finish(self, job_id: str, owner: str, progress: dict, error_code: str | None = None) -> dict:
        self.status(job_id, owner)
        state = "failed" if error_code else "complete"
        now = rfc3339(self.clock.utcnow())
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "UPDATE jobs SET state=?,progress_json=?,updated_at=?,lease_until=NULL,error_code=? WHERE job_id=? "
                "AND state='running'",
                (state, json.dumps(progress), now, error_code, job_id),
            )
        return self.status(job_id, owner)

    def interrupt(self, job_id: str, owner: str) -> dict:
        """Record an interrupted worker without overriding an operator's pause/cancel."""
        self.status(job_id, owner)
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "UPDATE jobs SET state='paused_recoverable',updated_at=?,lease_until=NULL "
                "WHERE job_id=? AND state IN ('queued','running')",
                (rfc3339(self.clock.utcnow()), job_id),
            )
        return self.status(job_id, owner)

    def recover_expired(self) -> int:
        now = rfc3339(self.clock.utcnow())
        with sqlite3.connect(self.db_path) as db:
            result = db.execute(
                "UPDATE jobs SET state='paused_recoverable', updated_at=? WHERE state='running' AND lease_until < ?",
                (now, now),
            )
            return result.rowcount

    def list(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as db:
            ids = [
                row[0:2]
                for row in db.execute(
                    "SELECT job_id,owner_profile FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
                )
            ]
        return [self.status(job_id, owner) for job_id, owner in ids]
