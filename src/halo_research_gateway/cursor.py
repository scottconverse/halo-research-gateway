"""Short-lived, tamper-evident pagination cursors."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path


class CursorError(ValueError):
    code = "CURSOR_INVALID"


class CursorExpired(CursorError):
    code = "CURSOR_EXPIRED"


class CursorCodec:
    def __init__(self, key_path: str | Path, ttl_seconds: int, clock=None) -> None:
        self.key_path = Path(key_path)
        self.ttl_seconds = ttl_seconds
        self.clock = clock or time.time
        self.key = self._load_or_create_key()

    def _load_or_create_key(self) -> bytes:
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if self.key_path.exists():
            key = self.key_path.read_bytes()
            if len(key) != 32:
                raise CursorError("cursor key has invalid length")
            return key
        key = secrets.token_bytes(32)
        temporary = self.key_path.with_suffix(".tmp")
        temporary.write_bytes(key)
        os.replace(temporary, self.key_path)
        return key

    def encode(self, payload: dict) -> str:
        value = dict(payload)
        value["exp"] = int(self.clock()) + self.ttl_seconds
        body = json.dumps(value, separators=(",", ":"), sort_keys=True).encode()
        signature = hmac.new(self.key, body, hashlib.sha256).digest()
        return base64.urlsafe_b64encode(body + signature).decode().rstrip("=")

    def decode(self, token: str) -> dict:
        try:
            raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
            canonical = base64.urlsafe_b64encode(raw).decode().rstrip("=")
            if not hmac.compare_digest(token, canonical):
                raise CursorError("cursor encoding is non-canonical")
            if len(raw) <= 32:
                raise CursorError("cursor is incomplete")
            body, signature = raw[:-32], raw[-32:]
            expected = hmac.new(self.key, body, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                raise CursorError("cursor signature is invalid")
            value = json.loads(body)
            if int(value["exp"]) < int(self.clock()):
                raise CursorExpired("cursor expired")
            return value
        except CursorError:
            raise
        except Exception as exc:
            raise CursorError("cursor is malformed") from exc
