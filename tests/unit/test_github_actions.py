import json
import sqlite3

import pytest

from halo_research_gateway.actions.github import GitHubIssueActionAdapter, github_target
from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.migrations import migrate
from halo_research_gateway.service import HaloService


class Connections:
    def get(self, connection_id):
        return {
            "connection_id": connection_id,
            "provider": "GitHub Actions App",
            "status": "ready",
            "scopes": ["metadata:read", "issues:write"],
        }

    def secret(self, connection_id):
        return {"token": "opaque-github-actions-token"}


def database(tmp_path):
    path = tmp_path / "gateway.db"
    migrate(str(path), str(tmp_path / "backups"))
    return path


@pytest.mark.asyncio
async def test_create_issue_returns_stable_owned_object_receipt(tmp_path):
    calls = []

    async def request(method, path, headers, body):
        calls.append((method, path, headers, body))
        return {
            "number": 17,
            "node_id": "ISSUE_node",
            "html_url": "https://github.com/acme/widgets/issues/17",
            "state": "open",
            "performed_via_github_app": {"id": 9},
        }

    result = await GitHubIssueActionAdapter(Connections(), str(database(tmp_path)), request).execute(
        {
            "action": "github_issue_create",
            "connection_id": "actions-1",
            "github": {"repository": "acme/widgets", "title": "Bug", "body": "Exact body"},
        }
    )
    assert result["object_id"] == 17
    assert result["object_kind"] == "issue"
    assert calls[0][0:2] == ("POST", "/repos/acme/widgets/issues")
    assert calls[0][2]["Authorization"] == "Bearer opaque-github-actions-token"
    assert "opaque-github-actions-token" not in json.dumps(result)


@pytest.mark.asyncio
async def test_edit_rejects_object_without_prior_halo_receipt(tmp_path):
    async def unexpected(*args):
        raise AssertionError("upstream must not be called")

    with pytest.raises(PermissionError, match="NOT_HALO_OWNED"):
        await GitHubIssueActionAdapter(Connections(), str(database(tmp_path)), unexpected).execute(
            {
                "action": "github_comment_edit",
                "connection_id": "actions-1",
                "github": {"repository": "acme/widgets", "comment_id": 44, "body": "Changed"},
            }
        )


@pytest.mark.asyncio
async def test_state_change_requires_receipt_and_rejects_pull_requests(tmp_path):
    db = database(tmp_path)
    outcome = {
        "provider": "github-actions-app",
        "connection_id": "actions-1",
        "repository": "acme/widgets",
        "object_kind": "issue",
        "object_id": 17,
    }
    receipt = {"outcome": outcome}
    with sqlite3.connect(db) as connection:
        connection.execute(
            "INSERT INTO action_plans(plan_id,plan_hash,plan_json,created_at,expires_at) VALUES (?,?,?,?,?)",
            ("plan-1", "hash", "{}", "2026-09-01T00:00:00Z", "2026-09-02T00:00:00Z"),
        )
        connection.execute(
            "INSERT INTO action_receipts VALUES (?,?,?,?,?,?)",
            ("receipt-1", "plan-1", "key-1", "complete", json.dumps(receipt), "2026-09-01T00:00:00Z"),
        )

    async def request(method, path, headers, body):
        assert method == "GET"
        return {"number": 17, "pull_request": {"url": "https://api.github.com/pulls/17"}}

    with pytest.raises(PermissionError, match="OWNERSHIP_UNVERIFIED"):
        await GitHubIssueActionAdapter(Connections(), str(db), request).execute(
            {
                "action": "github_issue_set_state",
                "connection_id": "actions-1",
                "github": {"repository": "acme/widgets", "issue_number": 17, "state": "closed"},
            }
        )


def test_github_target_is_an_exact_owner_repository():
    assert github_target("github://acme/widgets") == "acme/widgets"
    with pytest.raises(ValueError, match="TARGET_INVALID"):
        github_target("https://github.com/acme/widgets")


@pytest.mark.asyncio
async def test_service_freezes_and_executes_exact_github_issue_plan(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "service.db")
    config.storage.backup_directory = str(tmp_path / "service-backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    connection = service.connections.create(
        "GitHub Actions App",
        "Halo issue actions",
        "token",
        {"token": "opaque-github-actions-token"},
        ["metadata:read", "issues:write"],
    )
    calls = 0

    async def request(method, path, headers, body):
        nonlocal calls
        calls += 1
        return {
            "number": 17,
            "node_id": "ISSUE_node",
            "html_url": "https://github.com/acme/widgets/issues/17",
            "state": "open",
            "performed_via_github_app": {"id": 9},
        }

    service.github_actions._requester = request
    try:
        prepared = service.web_action_prepare(
            "github_issue_create",
            "github://acme/widgets",
            "Create the reviewed issue",
            {"title": "Exact title", "body": "Exact body"},
            connection["connection_id"],
        )
        assert prepared["preview"]["github"] == {
            "repository": "acme/widgets",
            "title": "Exact title",
            "body": "Exact body",
        }
        token = service.actions.approve(prepared["plan_id"])
        receipt = await service.web_action_execute(prepared["plan_id"], token, "github-once")
    finally:
        await service.close()

    assert calls == 1
    assert receipt["outcome"]["object_id"] == 17
