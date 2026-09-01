"""Operator-owned connection metadata backed by the DPAPI vault."""

from __future__ import annotations

import json
import sqlite3
import uuid
from pathlib import Path

from ..clock import SystemClock, rfc3339
from .vault import Vault


class ConnectionStore:
    TYPES = {"api_key", "token", "password", "oauth"}

    def __init__(self, db_path: str, vault_root: str | Path, clock=None) -> None:
        self.db_path = db_path
        self.vault = Vault(vault_root)
        self.clock = clock or SystemClock()

    def create(self, provider: str, label: str, connection_type: str, secret: dict[str, str], scopes=None) -> dict:
        if connection_type not in self.TYPES or not provider.strip() or not label.strip() or not secret:
            raise ValueError("INVALID_CONNECTION")
        connection_id = str(uuid.uuid4())
        vault_ref = self.vault.put({str(k): str(v) for k, v in secret.items()})
        capability = {"type": connection_type, "scopes": sorted(set(scopes or []))}
        now = rfc3339(self.clock.utcnow())
        try:
            with sqlite3.connect(self.db_path) as db:
                db.execute(
                    "INSERT INTO connections VALUES (?,?,?,?,?,?,?,NULL)",
                    (connection_id, provider.strip(), label.strip(), json.dumps(capability), vault_ref, now, now),
                )
        except Exception:
            self.vault.delete(vault_ref)
            raise
        return self.get(connection_id)

    def list(self) -> list[dict]:
        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT connection_id,provider,account_label,capability_json,created_at,verified_at,revoked_at "
                "FROM connections ORDER BY created_at DESC"
            ).fetchall()
        return [self._public(row) for row in rows]

    def get(self, connection_id: str) -> dict:
        with sqlite3.connect(self.db_path) as db:
            row = db.execute(
                "SELECT connection_id,provider,account_label,capability_json,created_at,verified_at,revoked_at "
                "FROM connections WHERE connection_id=?",
                (connection_id,),
            ).fetchone()
        if row is None:
            raise KeyError("CONNECTION_NOT_FOUND")
        return self._public(row)

    def secret(self, connection_id: str) -> dict[str, str]:
        with sqlite3.connect(self.db_path) as db:
            row = db.execute(
                "SELECT vault_ref,revoked_at FROM connections WHERE connection_id=?", (connection_id,)
            ).fetchone()
        if row is None:
            raise KeyError("CONNECTION_NOT_FOUND")
        if row[1] is not None:
            raise PermissionError("CONNECTION_REVOKED")
        return self.vault.get(row[0])

    def revoke(self, connection_id: str) -> dict:
        now = rfc3339(self.clock.utcnow())
        with sqlite3.connect(self.db_path) as db:
            changed = db.execute(
                "UPDATE connections SET revoked_at=? WHERE connection_id=? AND revoked_at IS NULL",
                (now, connection_id),
            ).rowcount
        if not changed:
            raise KeyError("CONNECTION_NOT_FOUND_OR_REVOKED")
        return self.get(connection_id)

    @staticmethod
    def _public(row) -> dict:
        capability = json.loads(row[3])
        return {
            "connection_id": row[0],
            "provider": row[1],
            "label": row[2],
            "type": capability["type"],
            "scopes": capability.get("scopes", []),
            "created_at": row[4],
            "verified_at": row[5],
            "status": "revoked" if row[6] else "ready",
        }
