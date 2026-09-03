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

    def compact(self, signed_state: str) -> str:
        """Reference authenticated state without exposing its fields to the model."""
        expires = int(self.decode(signed_state)["exp"]).to_bytes(8, "big")
        identity = hmac.digest(self.key, b"cursor-state-v1\0" + signed_state.encode(), "sha256")[:12]
        body = expires + identity
        signature = hmac.digest(self.key, b"cursor-handle-v1\0" + body, "sha256")[:16]
        return "h1_" + base64.urlsafe_b64encode(body + signature).decode().rstrip("=")

    def validate_handle(self, token: str, signed_state: str | None = None) -> None:
        """Authenticate and check expiry before lookup; bind retrieved state after it."""
        try:
            if not token.startswith("h1_") or len(token) != 51:
                raise CursorError("cursor handle is malformed")
            raw = base64.urlsafe_b64decode(token[3:])
            if base64.urlsafe_b64encode(raw).decode().rstrip("=") != token[3:]:
                raise CursorError("cursor encoding is non-canonical")
            body, signature = raw[:20], raw[20:]
            expected = hmac.digest(self.key, b"cursor-handle-v1\0" + body, "sha256")[:16]
            if not hmac.compare_digest(signature, expected):
                raise CursorError("cursor signature is invalid")
            if int.from_bytes(body[:8], "big") < int(self.clock()):
                raise CursorExpired("cursor expired")
            if signed_state is not None and not hmac.compare_digest(token, self.compact(signed_state)):
                raise CursorError("cursor state does not match handle")
        except CursorError:
            raise
        except Exception as exc:
            raise CursorError("cursor handle is malformed") from exc

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
