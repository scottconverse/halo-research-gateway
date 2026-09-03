"""Install pinned, local English OCR data used by the document reader."""

from __future__ import annotations

import hashlib
import os
import sys
import tempfile
from pathlib import Path
from urllib.request import urlopen

REVISION = "87416418657359cb625c412a48b6e1d6d41c29bd"
BASE_URL = f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{REVISION}/"
ASSETS = (
    (
        "eng.traineddata",
        "eng.traineddata",
        4_113_088,
        "7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2",
    ),
    ("TESSDATA-LICENSE.txt", "LICENSE", 11_358, "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"),
)


def _verified(path, digest, size):
    return path.is_file() and path.stat().st_size == size and hashlib.sha256(path.read_bytes()).hexdigest() == digest


def install_asset(destination, url, expected_sha256, expected_size, fetcher):
    destination = Path(destination)
    if destination.exists():
        if not _verified(destination, expected_sha256, expected_size):
            raise RuntimeError("OCR_DATA_EXISTS_WITH_DIFFERENT_HASH")
        return False
    payload = fetcher(url, expected_size)
    if len(payload) != expected_size or hashlib.sha256(payload).hexdigest() != expected_sha256:
        raise RuntimeError("OCR_DATA_INTEGRITY_ERROR")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".ocr-", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # Exclusive atomic publication: never replace an existing operator file,
        # including one that appeared while the download was running.
        try:
            os.link(temporary, destination)
        except FileExistsError:
            if not _verified(destination, expected_sha256, expected_size):
                raise RuntimeError("OCR_DATA_EXISTS_WITH_DIFFERENT_HASH") from None
            return False
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return True


def _download(url, size):
    with urlopen(url, timeout=30) as response:
        return response.read(size + 1)


def install_ocr_data(directory=None, fetcher=_download):
    directory = Path(directory) if directory is not None else Path(sys.prefix) / "share" / "tessdata"
    outcomes = {}
    for filename, remote_name, size, digest in ASSETS:
        changed = install_asset(directory / filename, BASE_URL + remote_name, digest, size, fetcher)
        outcomes[filename] = "installed" if changed else "verified-existing"
    return outcomes


if __name__ == "__main__":
    for name, outcome in install_ocr_data().items():
        print(f"OCR data: {name}: {outcome}")
