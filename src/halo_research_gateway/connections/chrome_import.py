"""Explicit cookie-only research-session import into a gateway-owned copy."""

from __future__ import annotations

import hashlib
import shutil
import uuid
from pathlib import Path


class ChromeImportError(ValueError):
    pass


CATEGORY_PATHS = {
    "cookies": ("Network/Cookies", "Cookies"),
}
EXCLUDED_NAMES = {"SingletonLock", "SingletonCookie", "SingletonSocket", "LOCK"}


class ChromeImporter:
    def __init__(self, destination_root: str | Path) -> None:
        self.destination_root = Path(destination_root).resolve()
        self.destination_root.mkdir(parents=True, exist_ok=True)

    def preview(
        self,
        source_profile: str | Path,
        destination_name: str,
        categories: list[str] | None = None,
        *,
        behavior: str = "replace",
    ) -> dict:
        source = Path(source_profile).resolve()
        if not source.is_dir():
            raise ChromeImportError("CHROME_SOURCE_NOT_FOUND")
        if Path(destination_name).name != destination_name or destination_name in {"", ".", ".."}:
            raise ChromeImportError("CHROME_DESTINATION_INVALID")
        if behavior not in {"replace", "merge"}:
            raise ChromeImportError("CHROME_BEHAVIOR_INVALID")
        chosen = sorted(set(categories or []))
        unknown = set(chosen) - set(CATEGORY_PATHS)
        if unknown or not chosen:
            raise ChromeImportError("CHROME_CATEGORY_INVALID")

        files: list[Path] = []
        for relative in CATEGORY_PATHS["cookies"]:
            candidate = source / Path(relative)
            if candidate.is_file():
                files.append(candidate)
        local_state = source.parent / "Local State"
        if local_state.is_file():
            files.append(local_state)
        files = sorted(set(files))
        digest = hashlib.sha256()
        total = 0
        records = []
        for path in files:
            relative = self._relative_for_copy(path, source)
            value = path.read_bytes()
            digest.update(relative.as_posix().encode())
            digest.update(hashlib.sha256(value).digest())
            total += len(value)
            records.append({"source": str(path), "relative": relative.as_posix(), "bytes": len(value)})
        return {
            "import_id": str(uuid.uuid4()),
            "source_profile": str(source),
            "destination_name": destination_name,
            "destination": str(self.destination_root / destination_name),
            "categories": chosen,
            "behavior": behavior,
            "files": records,
            "file_count": len(records),
            "total_bytes": total,
            "content_set_sha256": digest.hexdigest(),
        }

    def execute(self, preview: dict) -> dict:
        if preview.get("categories") != ["cookies"]:
            raise ChromeImportError("RESEARCH_SESSION_IMPORT_REQUIRED")
        # A stored legacy plan cannot smuggle other profile files into execution.
        source = Path(preview["source_profile"]).resolve()
        allowed = {source / relative for relative in CATEGORY_PATHS["cookies"]} | {source.parent / "Local State"}
        for record in preview["files"]:
            path = Path(record["source"]).resolve()
            if path not in allowed or record["relative"] != self._relative_for_copy(path, source).as_posix():
                raise ChromeImportError("RESEARCH_SESSION_IMPORT_REQUIRED")
        destination = Path(preview["destination"]).resolve()
        if destination.parent != self.destination_root:
            raise ChromeImportError("CHROME_DESTINATION_INVALID")
        source_profile = Path(preview["source_profile"])
        if any((source_profile / name).exists() for name in EXCLUDED_NAMES):
            raise ChromeImportError("CHROME_SOURCE_APPEARS_OPEN")
        replacing = destination.exists() and preview["behavior"] == "replace"
        target_root = destination
        staging = self.destination_root / f".import-{preview['import_id']}"
        if replacing:
            if staging.exists():
                shutil.rmtree(staging)
            staging.mkdir(parents=True)
            target_root = staging
        else:
            destination.mkdir(parents=True, exist_ok=True)
        copied = 0
        digest = hashlib.sha256()
        for record in preview["files"]:
            source = Path(record["source"])
            target = target_root / Path(record["relative"])
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            value = target.read_bytes()
            digest.update(Path(record["relative"]).as_posix().encode())
            digest.update(hashlib.sha256(value).digest())
            copied += 1
        if digest.hexdigest() != preview["content_set_sha256"]:
            if staging.exists():
                shutil.rmtree(staging)
            raise ChromeImportError("CHROME_IMPORT_HASH_MISMATCH")
        backup = None
        if replacing:
            backup = self.destination_root / f"{preview['destination_name']}.backup-{preview['import_id']}"
            destination.replace(backup)
            staging.replace(destination)
        return {
            "import_id": preview["import_id"],
            "destination_name": preview["destination_name"],
            "categories": preview["categories"],
            "behavior": preview["behavior"],
            "file_count": copied,
            "total_bytes": preview["total_bytes"],
            "content_set_sha256": digest.hexdigest(),
            "previous_profile_backup": str(backup) if backup else None,
            "status": "imported",
        }

    @staticmethod
    def _relative_for_copy(path: Path, source: Path) -> Path:
        if path.parent == source.parent and path.name == "Local State":
            return Path("Local State")
        return Path("Profile") / path.relative_to(source)
