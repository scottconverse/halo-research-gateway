"""Current-user DPAPI vault. Raw secret values never cross into MCP results."""

from __future__ import annotations

import ctypes
import json
import uuid
from ctypes import wintypes
from pathlib import Path


class DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_byte))]


def _blob(data: bytes):
    buffer = ctypes.create_string_buffer(data)
    return DATA_BLOB(len(data), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_byte))), buffer


def protect(data: bytes) -> bytes:
    source, keepalive = _blob(data)
    output = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptProtectData(
        ctypes.byref(source), "Halo Research Gateway", None, None, None, 0, ctypes.byref(output)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)


def unprotect(data: bytes) -> bytes:
    source, keepalive = _blob(data)
    output = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(
        ctypes.byref(source), None, None, None, None, 0, ctypes.byref(output)
    ):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output.pbData, output.cbData)
    finally:
        ctypes.windll.kernel32.LocalFree(output.pbData)


class Vault:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, values: dict[str, str]) -> str:
        reference = str(uuid.uuid4())
        payload = json.dumps(values, separators=(",", ":")).encode()
        path = self.root / f"{reference}.dpapi"
        temp = path.with_suffix(".tmp")
        temp.write_bytes(protect(payload))
        temp.replace(path)
        return reference

    def get(self, reference: str) -> dict[str, str]:
        uuid.UUID(reference)
        return json.loads(unprotect((self.root / f"{reference}.dpapi").read_bytes()))

    def delete(self, reference: str) -> None:
        (self.root / f"{reference}.dpapi").unlink(missing_ok=True)
