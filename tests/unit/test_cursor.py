from pathlib import Path

import pytest

from halo_research_gateway.cursor import CursorCodec, CursorError, CursorExpired


def test_cursor_is_signed_and_tampering_fails(tmp_path: Path):
    codec = CursorCodec(tmp_path / "key", 60, clock=lambda: 100)
    token = codec.encode({"tool": "web_fetch", "i": 1})
    assert codec.decode(token)["tool"] == "web_fetch"
    replacement = "A" if token[-1] != "A" else "B"
    with pytest.raises(CursorError):
        codec.decode(token[:-1] + replacement)


def test_cursor_expires(tmp_path: Path):
    now = [100]
    codec = CursorCodec(tmp_path / "key", 60, clock=lambda: now[0])
    token = codec.encode({"tool": "web_fetch"})
    now[0] = 161
    with pytest.raises(CursorExpired):
        codec.decode(token)
