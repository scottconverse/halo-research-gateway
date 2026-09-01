"""GitHub issue/comment actions through a separate least-privilege App."""

from __future__ import annotations

import json
import sqlite3
import urllib.parse
from collections.abc import Awaitable, Callable
from typing import Any

from ..connections.store import ConnectionStore
from ..providers.github import GitHubProvider

RequestJson = Callable[[str, str, dict[str, str], dict[str, Any] | None], Awaitable[Any]]


class GitHubIssueActionAdapter:
    ACTIONS = {
        "github_issue_create",
        "github_comment_create",
        "github_comment_edit",
        "github_issue_set_state",
    }

    def __init__(
        self,
        connections: ConnectionStore,
        db_path: str,
        requester: RequestJson | None = None,
    ) -> None:
        self.connections = connections
        self.db_path = db_path
        self.tokens = GitHubProvider(connections, requester=requester)
        self._requester = requester or self.tokens._request_json

    def _connection(self, connection_id: str) -> dict[str, Any]:
        connection = self.connections.get(connection_id)
        if connection["status"] != "ready" or connection["provider"].strip().casefold() not in {
            "github actions app",
            "github action app",
        }:
            raise PermissionError("GITHUB_ACTIONS_APP_REQUIRED")
        if "issues:write" not in connection.get("scopes", []):
            raise PermissionError("GITHUB_ISSUES_WRITE_SCOPE_REQUIRED")
        return connection

    def _owned(self, connection_id: str, repository: str, object_kind: str, object_id: int) -> bool:
        with sqlite3.connect(self.db_path) as db:
            rows = db.execute(
                "SELECT receipt_json FROM action_receipts WHERE outcome='complete' ORDER BY created_at DESC"
            ).fetchall()
        for (encoded,) in rows:
            outcome = json.loads(encoded).get("outcome", {})
            if (
                outcome.get("provider") == "github-actions-app"
                and outcome.get("connection_id") == connection_id
                and outcome.get("repository") == repository
                and outcome.get("object_kind") == object_kind
                and outcome.get("object_id") == object_id
            ):
                return True
        return False

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        action = plan.get("action")
        if action not in self.ACTIONS:
            raise ValueError("GITHUB_ACTION_REQUIRED")
        connection_id = str(plan.get("connection_id") or "")
        connection = self._connection(connection_id)
        repository = str((plan.get("github") or {}).get("repository") or "")
        if repository.count("/") != 1:
            raise ValueError("GITHUB_REPOSITORY_INVALID")
        token = await self.tokens._token(connection)
        headers = self.tokens._headers(token)
        values = plan["github"]
        if action == "github_issue_create":
            method = "POST"
            path = f"/repos/{repository}/issues"
            body = {"title": values["title"], "body": values.get("body", "")}
            object_kind = "issue"
        elif action == "github_comment_create":
            issue_number = int(values["issue_number"])
            method = "POST"
            path = f"/repos/{repository}/issues/{issue_number}/comments"
            body = {"body": values["body"]}
            object_kind = "comment"
        elif action == "github_comment_edit":
            comment_id = int(values["comment_id"])
            if not self._owned(connection_id, repository, "comment", comment_id):
                raise PermissionError("GITHUB_OBJECT_NOT_HALO_OWNED")
            method = "PATCH"
            path = f"/repos/{repository}/issues/comments/{comment_id}"
            body = {"body": values["body"]}
            object_kind = "comment"
        else:
            issue_number = int(values["issue_number"])
            if not self._owned(connection_id, repository, "issue", issue_number):
                raise PermissionError("GITHUB_OBJECT_NOT_HALO_OWNED")
            current = await self._requester("GET", f"/repos/{repository}/issues/{issue_number}", headers, None)
            if current.get("pull_request") or not current.get("performed_via_github_app"):
                raise PermissionError("GITHUB_OBJECT_OWNERSHIP_UNVERIFIED")
            method = "PATCH"
            path = f"/repos/{repository}/issues/{issue_number}"
            body = {"state": values["state"]}
            if values.get("state_reason"):
                body["state_reason"] = values["state_reason"]
            object_kind = "issue"
        response = await self._requester(method, path, headers, body)
        object_id = int(response.get("id") if object_kind == "comment" else response.get("number"))
        return {
            "status": "accepted_by_github",
            "provider": "github-actions-app",
            "connection_id": connection_id,
            "repository": repository,
            "object_kind": object_kind,
            "object_id": object_id,
            "node_id": response.get("node_id"),
            "url": response.get("html_url"),
            "state": response.get("state"),
            "performed_via_github_app": bool(response.get("performed_via_github_app")),
        }


def github_target(target_url: str) -> str:
    parsed = urllib.parse.urlsplit(target_url)
    repository = (parsed.netloc + parsed.path).strip("/")
    if parsed.scheme != "github" or repository.count("/") != 1:
        raise ValueError("GITHUB_ACTION_TARGET_INVALID")
    return repository
