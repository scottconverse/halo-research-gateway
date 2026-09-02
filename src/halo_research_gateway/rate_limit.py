"""Durable provider budgets and circuit state shared by every client."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta

from .clock import SystemClock, rfc3339


class ProviderBudgetExhausted(RuntimeError):
    code = "RATE_LIMITED"


class ProviderCircuitOpen(RuntimeError):
    code = "PROVIDER_CIRCUIT_OPEN"

    def __init__(self, message: str, retry_after_seconds: float | None = None):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds


class ProviderRateLimited(RuntimeError):
    code = "RATE_LIMITED"

    def __init__(self, retry_after_seconds: float):
        super().__init__("Provider requested a delay before another request")
        self.retry_after_seconds = retry_after_seconds


class RateLedger:
    def __init__(self, db_path: str, clock=None) -> None:
        self.db_path = db_path
        self.clock = clock or SystemClock()

    def admit(self, bucket: str, daily_limit: int | None = None) -> int:
        now = self.clock.utcnow()
        day = now.date().isoformat()
        with sqlite3.connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT window_started_at,request_count,circuit_state,circuit_until FROM rate_state WHERE bucket_key=?",
                (bucket,),
            ).fetchone()
            count = 0
            if row:
                count = row[1] if row[0] == day else 0
                if row[2] == "open" and row[3] and datetime.fromisoformat(row[3]) > now:
                    raise ProviderCircuitOpen(
                        f"{bucket} circuit is open", (datetime.fromisoformat(row[3]) - now).total_seconds()
                    )
            if daily_limit is not None and count >= daily_limit:
                raise ProviderBudgetExhausted(f"{bucket} daily budget is exhausted")
            count += 1
            db.execute(
                "INSERT INTO rate_state(bucket_key,last_started_at,window_started_at,request_count) VALUES(?,?,?,?) "
                "ON CONFLICT(bucket_key) DO UPDATE SET last_started_at=excluded.last_started_at,"
                "window_started_at=excluded.window_started_at,request_count=excluded.request_count,"
                "circuit_state=CASE WHEN circuit_until IS NULL OR circuit_until <= excluded.last_started_at THEN 'closed' ELSE circuit_state END",
                (bucket, rfc3339(now), day, count),
            )
        return count

    def success(self, bucket: str) -> None:
        with sqlite3.connect(self.db_path) as db:
            db.execute(
                "UPDATE rate_state SET consecutive_429=0,circuit_state='closed',circuit_until=NULL WHERE bucket_key=?",
                (bucket,),
            )

    def rate_limited(self, bucket: str, threshold: int, cooldown_seconds: int, backoff_seconds: int = 0) -> None:
        now = self.clock.utcnow()
        with sqlite3.connect(self.db_path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT consecutive_429 FROM rate_state WHERE bucket_key=?", (bucket,)).fetchone()
            failures = (row[0] if row else 0) + 1
            delay = max(cooldown_seconds, backoff_seconds) if failures >= threshold else backoff_seconds
            state = "open" if delay > 0 else "closed"
            until = rfc3339(now + timedelta(seconds=delay)) if state == "open" else None
            db.execute(
                "INSERT INTO rate_state(bucket_key,last_started_at,window_started_at,request_count,consecutive_429,circuit_state,circuit_until) "
                "VALUES(?,?,?,?,?,?,?) ON CONFLICT(bucket_key) DO UPDATE SET consecutive_429=excluded.consecutive_429,"
                "circuit_state=excluded.circuit_state,circuit_until=excluded.circuit_until",
                (bucket, rfc3339(now), now.date().isoformat(), 0, failures, state, until),
            )

    def status(self) -> dict[str, dict]:
        now = self.clock.utcnow()
        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT bucket_key,window_started_at,request_count,consecutive_429,circuit_state,circuit_until FROM rate_state"
            ).fetchall()
        return {
            row[0]: {
                "window": row[1],
                "requests": row[2],
                "consecutive_429": row[3],
                "circuit": "closed"
                if row[4] == "open" and row[5] and datetime.fromisoformat(row[5]) <= now
                else row[4],
                "circuit_until": row[5],
            }
            for row in rows
        }
