"""Operator review of cookie-only research-session imports.

The legacy database tables are retained to preserve historical receipts. They
do not confer authority: only current cookie-import plans can be approved/run.
"""

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


class ImportReviewStore:
    def __init__(self, db_path: str, approval_ttl: int = 300, clock=None) -> None:
        self.db_path = db_path
        self.approval_ttl = approval_ttl
        self.clock = clock or SystemClock()
        self._plan_locks: WeakValueDictionary[str, asyncio.Lock] = WeakValueDictionary()

    @staticmethod
    def _canonical(value: dict) -> str:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def prepare(self, plan: dict) -> dict:
        self._validate(plan)
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
            self._read_plan(db, plan_id)
            found = db.execute(
                "UPDATE action_plans SET approval_digest=?, approval_expires_at=? WHERE plan_id=? AND consumed_at IS NULL",
                (digest, rfc3339(expires), plan_id),
            ).rowcount
        if not found:
            raise KeyError("IMPORT_PLAN_CHANGED")
        return token

    async def execute(self, plan_id: str, token: str, idempotency_key: str, executor) -> dict:
        lock = self._plan_locks.setdefault(plan_id, asyncio.Lock())
        async with lock:
            reserved_at = rfc3339(self.clock.utcnow())
            with sqlite3.connect(self.db_path) as db:
                db.execute("BEGIN IMMEDIATE")
                self._read_plan(db, plan_id)
                existing = db.execute(
                    "SELECT receipt_json FROM action_receipts WHERE idempotency_key=?", (idempotency_key,)
                ).fetchone()
                if existing:
                    receipt = json.loads(existing[0])
                    if receipt["plan_id"] != plan_id:
                        raise PermissionError("IMPORT_IDEMPOTENCY_CONFLICT")
                    return receipt
                row = db.execute(
                    "SELECT plan_hash,plan_json,approval_digest,approval_expires_at,consumed_at "
                    "FROM action_plans WHERE plan_id=?",
                    (plan_id,),
                ).fetchone()
                if row is None or row[4] is not None:
                    raise PermissionError("IMPORT_ALREADY_EXECUTED")
                if not row[2] or not hmac.compare_digest(row[2], hashlib.sha256(token.encode()).hexdigest()):
                    raise PermissionError("IMPORT_APPROVAL_REQUIRED")
                if row[3] < rfc3339(self.clock.utcnow()):
                    raise PermissionError("IMPORT_APPROVAL_EXPIRED")
                if (
                    db.execute(
                        "UPDATE action_plans SET consumed_at=? WHERE plan_id=? AND consumed_at IS NULL",
                        (reserved_at, plan_id),
                    ).rowcount
                    != 1
                ):
                    raise PermissionError("IMPORT_ALREADY_EXECUTED")

            plan = json.loads(row[1])
            receipt_outcome = "complete"
            cancellation = None
            try:
                outcome = await executor(plan)
            except asyncio.CancelledError as exc:
                cancellation = exc
                receipt_outcome = "ambiguous"
                outcome = {"status": "ambiguous", "error_code": "IMPORT_EXECUTION_AMBIGUOUS"}
            except Exception:
                receipt_outcome = "ambiguous"
                outcome = {"status": "ambiguous", "error_code": "IMPORT_EXECUTION_AMBIGUOUS"}
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
            if self._is_import(json.loads(row[2]))
        ]

    def list_receipts(self, limit: int = 50) -> list[dict]:
        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT r.receipt_json FROM action_receipts r JOIN action_plans p USING(plan_id) "
                "WHERE json_extract(p.plan_json, '$.action')='chrome_import' "
                "AND json_extract(p.plan_json, '$.import.categories')='[\"cookies\"]' "
                "ORDER BY r.created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [json.loads(row[0]) for row in rows]

    @staticmethod
    def _is_import(plan: dict) -> bool:
        return (
            set(plan) == {"action", "import"}
            and plan.get("action") == "chrome_import"
            and isinstance(plan.get("import"), dict)
            and plan["import"].get("categories") == ["cookies"]
        )

    @classmethod
    def _validate(cls, plan: dict) -> None:
        if not cls._is_import(plan):
            raise ValueError("RESEARCH_SESSION_IMPORT_REQUIRED")

    def _read_plan(self, db, plan_id):
        row = db.execute("SELECT plan_json,plan_hash FROM action_plans WHERE plan_id=?", (plan_id,)).fetchone()
        if row is None:
            raise KeyError("IMPORT_PLAN_UNAVAILABLE")
        plan = json.loads(row[0])
        self._validate(plan)
        if hashlib.sha256(self._canonical(plan).encode()).hexdigest() != row[1]:
            raise PermissionError("IMPORT_PLAN_CHANGED")
        return plan
