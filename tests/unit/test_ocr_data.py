import hashlib
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from halo_research_gateway.ocr_data import install_asset

PAYLOAD = b"deterministic OCR data fixture"
DIGEST = hashlib.sha256(PAYLOAD).hexdigest()
URL = "https://example.org/pinned/eng.traineddata"


def test_installs_only_verified_bytes_and_reuses_existing_file(tmp_path):
    calls = []

    def fetch(url, max_bytes):
        calls.append((url, max_bytes))
        return PAYLOAD

    destination = tmp_path / "tessdata" / "eng.traineddata"
    install_asset(destination, URL, DIGEST, len(PAYLOAD), fetch)
    assert destination.exists(), "verified OCR data was not installed"
    assert destination.read_bytes() == PAYLOAD
    install_asset(destination, URL, DIGEST, len(PAYLOAD), fetch)
    assert len(calls) == 1, "already-verified data was downloaded again"


@pytest.mark.parametrize("payload", [b"wrong", PAYLOAD + b"oversize"])
def test_rejects_download_hash_or_size_mismatch(tmp_path, payload):
    destination = tmp_path / "eng.traineddata"
    with pytest.raises(RuntimeError, match="OCR_DATA_INTEGRITY_ERROR"):
        install_asset(destination, URL, DIGEST, len(PAYLOAD), lambda *args: payload)
    assert not destination.exists()


def test_preserves_unrecognized_existing_language_data(tmp_path):
    destination = tmp_path / "eng.traineddata"
    destination.write_bytes(b"operator-owned alternate OCR model")
    with pytest.raises(RuntimeError, match="OCR_DATA_EXISTS_WITH_DIFFERENT_HASH"):
        install_asset(destination, URL, DIGEST, len(PAYLOAD), lambda *args: PAYLOAD)
    assert destination.read_bytes() == b"operator-owned alternate OCR model"


@pytest.mark.skipif(os.name != "nt", reason="Windows installer")
def test_full_installer_invokes_local_ocr_setup(tmp_path):
    root = tmp_path / "fixture-repo"
    (root / "scripts").mkdir(parents=True)
    (root / "config").mkdir()
    (root / "skills" / "halo-research").mkdir(parents=True)
    (root / "config" / "config.example.toml").write_text("[server]\nport = 8765\n", encoding="utf-8")
    (root / "skills" / "halo-research" / "SKILL.md").write_text("fixture", encoding="utf-8")
    (root / "scripts" / "Invoke-QualityGate.ps1").write_text("$global:LASTEXITCODE = 0\n", encoding="utf-8")
    source = Path(__file__).resolve().parents[2] / "scripts" / "Install-HaloResearch.ps1"
    shutil.copyfile(source, root / "scripts" / source.name)
    wrapper = tmp_path / "wrapper.ps1"
    wrapper.write_text(
        "$ErrorActionPreference = 'Stop'\n"
        "function global:uv { ($args -join ' ') | Add-Content -LiteralPath $env:HALO_OCR_INSTALL_TRACE; $global:LASTEXITCODE = 0 }\n"
        "function global:git { $global:LASTEXITCODE = 0 }\n"
        "& (Join-Path $env:HALO_OCR_INSTALL_REPO 'scripts\\Install-HaloResearch.ps1')\n",
        encoding="utf-8",
    )
    trace = tmp_path / "calls.txt"
    env = dict(
        os.environ,
        LOCALAPPDATA=str(tmp_path / "appdata"),
        USERPROFILE=str(tmp_path / "user"),
        HALO_OCR_INSTALL_TRACE=str(trace),
        HALO_OCR_INSTALL_REPO=str(root),
    )
    result = subprocess.run(
        ["pwsh", "-NoProfile", "-File", str(wrapper)], env=env, capture_output=True, text=True, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "run --locked python -m halo_research_gateway.ocr_data" in trace.read_text(encoding="utf-8-sig")


def test_write_failure_cleans_only_installer_temporary_file(tmp_path, monkeypatch):
    def failed_flush(descriptor):
        raise OSError("fixture disk error")

    monkeypatch.setattr(os, "fsync", failed_flush)
    with pytest.raises(OSError, match="fixture disk error"):
        install_asset(tmp_path / "eng.traineddata", URL, DIGEST, len(PAYLOAD), lambda *args: PAYLOAD)
    assert not list(tmp_path.glob(".ocr-*")), "failed write leaked an installer temporary file"
    assert not (tmp_path / "eng.traineddata").exists()


def test_file_created_during_download_is_not_overwritten(tmp_path):
    destination = tmp_path / "eng.traineddata"

    def concurrent_file(url, max_bytes):
        destination.write_bytes(b"operator file appeared during download")
        return PAYLOAD

    with pytest.raises(RuntimeError, match="OCR_DATA_EXISTS_WITH_DIFFERENT_HASH"):
        install_asset(destination, URL, DIGEST, len(PAYLOAD), concurrent_file)
    assert destination.read_bytes() == b"operator file appeared during download"
    assert not list(tmp_path.glob(".ocr-*"))
