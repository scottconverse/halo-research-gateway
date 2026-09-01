"""Immutable plans, operator approvals, and durable idempotent receipts."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
import uuid
from datetime import timedelta

from ..clock import SystemClock, rfc3339


class ActionStore:
    def __init__(self, db_path: str, approval_ttl: int = 300, clock=None) -> None:
        self.db_path = db_path
        self.approval_ttl = approval_ttl
        self.clock = clock or SystemClock()

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
        with sqlite3.connect(self.db_path) as db:
            existing = db.execute(
                "SELECT receipt_json FROM action_receipts WHERE idempotency_key=?", (idempotency_key,)
            ).fetchone()
            if existing:
                return json.loads(existing[0])
            row = db.execute(
                "SELECT plan_hash,plan_json,approval_digest,approval_expires_at,consumed_at FROM action_plans WHERE plan_id=?",
                (plan_id,),
            ).fetchone()
        if row is None or row[4] is not None:
            raise PermissionError("ACTION_ALREADY_EXECUTED")
        if not row[2] or not hmac.compare_digest(row[2], hashlib.sha256(token.encode()).hexdigest()):
            raise PermissionError("ACTION_APPROVAL_REQUIRED")
        if row[3] < rfc3339(self.clock.utcnow()):
            raise PermissionError("ACTION_APPROVAL_EXPIRED")
        plan = json.loads(row[1])
        outcome = await executor(plan)
        receipt = {
            "receipt_id": str(uuid.uuid4()),
            "plan_id": plan_id,
            "plan_hash": row[0],
            "outcome": outcome,
            "created_at": rfc3339(self.clock.utcnow()),
        }
        encoded = self._canonical(receipt)
        with sqlite3.connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            if (
                db.execute(
                    "UPDATE action_plans SET consumed_at=? WHERE plan_id=? AND consumed_at IS NULL",
                    (receipt["created_at"], plan_id),
                ).rowcount
                != 1
            ):
                raise PermissionError("ACTION_ALREADY_EXECUTED")
            db.execute(
                "INSERT INTO action_receipts VALUES (?,?,?,?,?,?)",
                (receipt["receipt_id"], plan_id, idempotency_key, "complete", encoded, receipt["created_at"]),
            )
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
