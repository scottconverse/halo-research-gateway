from pathlib import Path

import pytest

from halo_research_gateway.connections.chrome_import import ChromeImporter


def fixture_profile(tmp_path: Path) -> Path:
    root = tmp_path / "Chrome" / "User Data"
    profile = root / "Default"
    (profile / "Network").mkdir(parents=True)
    (profile / "Cache").mkdir()
    (profile / "Bookmarks").write_text('{"roots":{}}', encoding="utf-8")
    (profile / "Login Data").write_bytes(b"encrypted-password-database")
    (profile / "Network" / "Cookies").write_bytes(b"encrypted-cookie-database")
    (profile / "Cache" / "noise").write_bytes(b"not-imported")
    (root / "Local State").write_bytes(b"encrypted-key-metadata")
    return profile


def test_selected_import_is_previewed_then_copied_with_redacted_receipt(tmp_path):
    source = fixture_profile(tmp_path)
    importer = ChromeImporter(tmp_path / "gateway-profiles")
    preview = importer.preview(source, "research", ["bookmarks", "saved_passwords"])
    assert preview["file_count"] == 3
    assert any(record["relative"] == "Local State" for record in preview["files"])
    receipt = importer.execute(preview)
    assert receipt["status"] == "imported"
    assert (tmp_path / "gateway-profiles" / "research" / "Profile" / "Login Data").is_file()
    assert "encrypted-password" not in repr(receipt)
    assert "source_profile" not in receipt


def test_complete_import_excludes_caches_and_lock_files(tmp_path):
    source = fixture_profile(tmp_path)
    (source / "SingletonLock").write_text("lock")
    importer = ChromeImporter(tmp_path / "gateway-profiles")
    preview = importer.preview(source, "complete", complete=True)
    paths = {record["relative"] for record in preview["files"]}
    assert "Profile/Cache/noise" not in paths
    assert "Profile/SingletonLock" not in paths
    assert "Profile/Login Data" in paths


@pytest.mark.asyncio
async def test_service_import_requires_exact_approval_and_writes_redacted_receipt(tmp_path):
    from halo_research_gateway.config import GatewayConfig
    from halo_research_gateway.service import HaloService

    source = fixture_profile(tmp_path)
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    service.chrome_importer = ChromeImporter(tmp_path / "gateway-profiles")
    plan = service.chrome_import_preview(
        source_profile=source,
        destination_name="approved",
        categories=["bookmarks"],
        complete=False,
        behavior="replace",
    )
    with pytest.raises(PermissionError, match="ACTION_APPROVAL_REQUIRED"):
        await service.chrome_import_execute(plan["plan_id"], "wrong", "import-one")
    token = service.actions.approve(plan["plan_id"])
    receipt = await service.chrome_import_execute(plan["plan_id"], token, "import-one")
    assert receipt["outcome"]["status"] == "imported"
    assert str(source) not in repr(receipt)
    await service.close()
