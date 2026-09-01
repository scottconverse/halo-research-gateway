"""Immutable plans, operator approvals, and durable idempotent receipts."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import secrets
import sqlite3
import uuid
from datetime import timedelta
from weakref import WeakValueDictionary

from ..clock import SystemClock, rfc3339


class ActionStore:
    def __init__(self, db_path: str, approval_ttl: int = 300, clock=None) -> None:
        self.db_path = db_path
        self.approval_ttl = approval_ttl
        self.clock = clock or SystemClock()
        self._plan_locks: WeakValueDictionary[str, asyncio.Lock] = WeakValueDictionary()

    @staticmethod
    def _canonical(value: dict) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def prepare(self, plan: dict) -> dict:
        normalized = self._canonical(plan)
        plan_hash = hashlib.sha256(normalized.encode()).hexdigest()
        plan_id = str(uuid.uuid4())
        now = self.clock.utcnow()
        expires = now + timedelta(minutes=30)
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "INSERT INTO action_plans(plan_id,plan_hash,plan_json,created_at,expires_at) VALUES (?,?,?,?,?)",
                (plan_id, plan_hash, normalized, rfc3339(now), rfc3339(expires)),
            )
        return {
            "plan_id": plan_id,
            "plan_hash": plan_hash,
            "preview": plan,
            "expires_at": rfc3339(expires),
            "approval_required": True,
        }

    def approve(self, plan_id: str) -> str:
        token = secrets.token_urlsafe(32)
        digest = hashlib.sha256(token.encode()).hexdigest()
        expires = self.clock.utcnow() + timedelta(seconds=self.approval_ttl)
        with sqlite3.connect(self.db_path) as db:
            found = db.execute(
                "UPDATE action_plans SET approval_digest=?, approval_expires_at=? WHERE plan_id=? AND consumed_at IS NULL",
                (digest, rfc3339(expires), plan_id),
            ).rowcount
        if not found:
            raise KeyError("ACTION_PLAN_CHANGED")
        return token

    async def execute(self, plan_id: str, token: str, idempotency_key: str, executor) -> dict:
        lock = self._plan_locks.setdefault(plan_id, asyncio.Lock())
        async with lock:
            reserved_at = rfc3339(self.clock.utcnow())
            with sqlite3.connect(self.db_path) as db:
                db.execute("BEGIN IMMEDIATE")
                existing = db.execute(
                    "SELECT receipt_json FROM action_receipts WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if existing:
                    return json.loads(existing[0])
                row = db.execute(
                    "SELECT plan_hash,plan_json,approval_digest,approval_expires_at,consumed_at "
                    "FROM action_plans WHERE plan_id=?",
                    (plan_id,),
                ).fetchone()
                if row is None or row[4] is not None:
                    raise PermissionError("ACTION_ALREADY_EXECUTED")
                if not row[2] or not hmac.compare_digest(row[2], hashlib.sha256(token.encode()).hexdigest()):
                    raise PermissionError("ACTION_APPROVAL_REQUIRED")
                if row[3] < rfc3339(self.clock.utcnow()):
                    raise PermissionError("ACTION_APPROVAL_EXPIRED")
                if (
                    db.execute(
                        "UPDATE action_plans SET consumed_at=? WHERE plan_id=? AND consumed_at IS NULL",
                        (reserved_at, plan_id),
                    ).rowcount
                    != 1
                ):
                    raise PermissionError("ACTION_ALREADY_EXECUTED")

            plan = json.loads(row[1])
            receipt_outcome = "complete"
            cancellation = None
            try:
                outcome = await executor(plan)
            except asyncio.CancelledError as exc:
                cancellation = exc
                receipt_outcome = "ambiguous"
                outcome = {"status": "ambiguous", "error_code": "ACTION_EXECUTION_AMBIGUOUS"}
            except Exception:
                receipt_outcome = "ambiguous"
                outcome = {"status": "ambiguous", "error_code": "ACTION_EXECUTION_AMBIGUOUS"}
            receipt = {
                "receipt_id": str(uuid.uuid4()),
                "plan_id": plan_id,
                "plan_hash": row[0],
                "outcome": outcome,
                "created_at": rfc3339(self.clock.utcnow()),
            }
            encoded = self._canonical(receipt)
            with sqlite3.connect(self.db_path) as db:
                db.execute(
                    "INSERT INTO action_receipts VALUES (?,?,?,?,?,?)",
                    (
                        receipt["receipt_id"],
                        plan_id,
                        idempotency_key,
                        receipt_outcome,
                        encoded,
                        receipt["created_at"],
                    ),
                )
            if cancellation is not None:
                raise cancellation
            return receipt

    def list_plans(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT plan_id,plan_hash,plan_json,created_at,expires_at,approval_expires_at,consumed_at "
                "FROM action_plans ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "plan_id": row[0],
                "plan_hash": row[1],
                "preview": json.loads(row[2]),
                "created_at": row[3],
                "expires_at": row[4],
                "approved_until": row[5],
                "status": "executed" if row[6] else "approved" if row[5] else "awaiting_approval",
            }
            for row in rows
        ]

    def list_receipts(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT receipt_json FROM action_receipts ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
        return [json.loads(row[0]) for row in rows]
