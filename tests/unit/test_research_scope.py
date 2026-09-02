"""Product boundary: retrieve evidence, never send, publish, or purchase."""

import hashlib
import json
import re
import sqlite3
from pathlib import Path

import httpx
import pytest

import halo_research_gateway
from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.connections.chrome_import import ChromeImporter


@pytest.fixture
def app(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    return create_application(config)


@pytest.mark.asyncio
async def test_only_research_tools_and_operator_routes_remain(app):
    service = app.state.halo_service
    try:
        names = {tool.name for tool in await app.state.mcp_server.list_tools()}
        assert names == {
            "web_search",
            "web_fetch",
            "web_crawl",
            "reddit_search",
            "reddit_thread",
            "document_extract",
            "deep_research",
            "github_research",
            "transcript_fetch",
            "community_search",
            "community_thread",
            "local_fetch",
            "local_crawl",
            "research_job",
        }
        for name in ("web_action_prepare", "web_action_execute", "gmail", "github_actions", "actions"):
            assert not hasattr(service, name), name
        assert not hasattr(service.http, "submit_form")
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8765"
        ) as client:
            assert (await client.post("/operator/api/actions/legacy-plan/approve")).status_code == 404
            state = (await client.get("/operator/api/state")).json()
            assert "actions" not in state
            assert "actions" not in state["health"]
            html = (await client.get("/operator")).text
            for removed in (
                "gmailPreset",
                "githubActionsApp",
                "issues:write",
                "saved_passwords",
                "payment_metadata",
                "Complete profile",
                "/operator/api/actions",
            ):
                assert removed not in html
            assert "GitHub App (read-only research)" in html
    finally:
        await service.close()


@pytest.mark.parametrize(
    "category", ["saved_passwords", "autofill", "payment_metadata", "extensions", "history", "bookmarks", "settings"]
)
def test_personal_data_import_categories_are_removed(tmp_path, category):
    source = tmp_path / "source"
    source.mkdir()
    with pytest.raises(ValueError):
        ChromeImporter(tmp_path / "owned").preview(source, "research", [category])


def test_outbound_adapters_are_not_shipped():
    source = Path(halo_research_gateway.__file__).parent / "actions"
    assert not list(source.glob("*.py"))


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["gmail_draft_send", "github_issue_create", "purchase", "form_submit"])
async def test_legacy_plans_cannot_use_import_approval_or_execution(app, action):
    service = app.state.halo_service
    try:
        plan = json.dumps(
            {"action": action, "target_url": "https://example.com"}, sort_keys=True, separators=(",", ":")
        )
        with sqlite3.connect(service.config.storage.database) as db:
            db.execute(
                "INSERT INTO action_plans(plan_id,plan_hash,plan_json,created_at,expires_at) VALUES (?,?,?,?,?)",
                ("legacy", hashlib.sha256(plan.encode()).hexdigest(), plan, "2026-09-02", "2099-01-01"),
            )
        with pytest.raises(ValueError, match="RESEARCH_SESSION_IMPORT_REQUIRED"):
            service.import_reviews.approve("legacy")
        with pytest.raises(ValueError, match="RESEARCH_SESSION_IMPORT_REQUIRED"):
            await service.chrome_import_execute("legacy", "old-token", "old-key")
        assert service.import_reviews.list_plans() == []
        # Preserved, not erased during the product removal.
        with sqlite3.connect(service.config.storage.database) as db:
            assert db.execute("SELECT count(*) FROM action_plans").fetchone()[0] == 1
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_http_import_rejects_complete_and_removed_categories(app, tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1:8765"
        ) as client:
            html = (await client.get("/operator")).text
            csrf = re.search(r'window.HALO_CSRF="([^"]+)"', html).group(1)
            for extra in ({"complete": True, "categories": ["cookies"]}, {"categories": ["saved_passwords"]}):
                response = await client.post(
                    "/operator/api/imports/chrome",
                    headers={"x-halo-csrf": csrf},
                    json={"source_profile": str(source), "destination_name": "research", **extra},
                )
                assert response.status_code == 400
            assert app.state.halo_service.import_reviews.list_plans() == []
    finally:
        await app.state.halo_service.close()


def test_old_actions_config_cannot_restore_removed_capability(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[actions]\nenabled = true\ndefault_policy = "standing"\n', encoding="utf-8")
    config = GatewayConfig.load(path)
    assert not hasattr(config, "actions")
    assert config.imports.approval_ttl_seconds == 300


def test_legacy_cookie_plan_cannot_copy_passwords(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    password_file = source / "Login Data"
    password_file.write_bytes(b"fixture-only")
    importer = ChromeImporter(tmp_path / "owned")
    preview = importer.preview(source, "research", ["cookies"])
    preview["files"].append({"source": str(password_file), "relative": "Profile/Login Data", "bytes": 12})
    with pytest.raises(ValueError, match="RESEARCH_SESSION_IMPORT_REQUIRED"):
        importer.execute(preview)
    assert not (tmp_path / "owned" / "research").exists()
