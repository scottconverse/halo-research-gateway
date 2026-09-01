"""Least-scope Gmail compose actions with frozen MIME evidence."""

from __future__ import annotations

import base64
import hashlib
import urllib.parse
from collections.abc import Awaitable, Callable
from email.message import EmailMessage
from email.policy import SMTP
from typing import Any

import httpx

from ..connections.store import ConnectionStore
from ..providers.http_fetch import PinnedTransport, resolve_public
from ..security import validate_url

GMAIL_COMPOSE_SCOPE = "https://www.googleapis.com/auth/gmail.compose"
GMAIL_BASE = "https://gmail.googleapis.com"
RequestJson = Callable[[str, str, dict[str, str], dict[str, Any]], Awaitable[dict[str, Any]]]


def freeze_mime(
    *,
    sender: str | None,
    to: list[str],
    subject: str,
    text: str,
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    reply_to: str | None = None,
    message_id: str | None = None,
) -> dict[str, Any]:
    """Create deterministic RFC 5322 bytes for exact operator review."""

    if not to or not all(address.strip() for address in to):
        raise ValueError("GMAIL_RECIPIENT_REQUIRED")
    message = EmailMessage(policy=SMTP)
    if sender:
        message["From"] = sender
    message["To"] = ", ".join(to)
    if cc:
        message["Cc"] = ", ".join(cc)
    if bcc:
        message["Bcc"] = ", ".join(bcc)
    if reply_to:
        message["Reply-To"] = reply_to
    if message_id:
        message["Message-ID"] = message_id
    message["Subject"] = subject
    message.set_content(text)
    raw = message.as_bytes(policy=SMTP)
    return {
        "raw": base64.urlsafe_b64encode(raw).decode("ascii").rstrip("="),
        "submitted_raw_sha256": hashlib.sha256(raw).hexdigest(),
        "rfc_message_id": message_id,
        "recipients": {"to": list(to), "cc": list(cc or []), "bcc": list(bcc or [])},
        "subject": subject,
        "body_chars": len(text),
    }


class GmailComposeAdapter:
    ACTIONS = {
        "gmail_draft_create",
        "gmail_draft_update",
        "gmail_draft_send",
        "gmail_message_send",
    }

    def __init__(
        self,
        connections: ConnectionStore,
        requester: RequestJson | None = None,
    ) -> None:
        self.connections = connections
        self._requester = requester or self._request_json

    async def _request_json(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> dict[str, Any]:
        url = GMAIL_BASE + path
        target = validate_url(url)
        address = await resolve_public(target)
        async with httpx.AsyncClient(
            transport=PinnedTransport(target, address),
            trust_env=False,
            timeout=30,
            follow_redirects=False,
        ) as client:
            response = await client.request(method, url, headers=headers, json=body)
            response.raise_for_status()
            return response.json()

    def _credential(self, connection_id: str) -> str:
        connection = self.connections.get(connection_id)
        if connection["status"] != "ready" or connection["provider"].strip().casefold() not in {
            "gmail",
            "google gmail",
        }:
            raise PermissionError("GMAIL_CONNECTION_REQUIRED")
        if GMAIL_COMPOSE_SCOPE not in connection.get("scopes", []):
            raise PermissionError("GMAIL_COMPOSE_SCOPE_REQUIRED")
        token = self.connections.secret(connection_id).get("access_token")
        if not token:
            raise PermissionError("GMAIL_ACCESS_TOKEN_REQUIRED")
        return token

    async def execute(self, plan: dict[str, Any]) -> dict[str, Any]:
        action = plan.get("action")
        if action not in self.ACTIONS:
            raise ValueError("GMAIL_ACTION_REQUIRED")
        connection_id = str(plan.get("connection_id") or "")
        token = self._credential(connection_id)
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        frozen = plan.get("gmail") or {}
        draft_id = frozen.get("draft_id")
        if action == "gmail_draft_create":
            method, path, body = "POST", "/gmail/v1/users/me/drafts", {"message": {"raw": frozen["raw"]}}
        elif action == "gmail_draft_update":
            if not draft_id:
                raise ValueError("GMAIL_DRAFT_ID_REQUIRED")
            quoted = urllib.parse.quote(str(draft_id), safe="")
            method, path, body = (
                "PUT",
                f"/gmail/v1/users/me/drafts/{quoted}",
                {"id": draft_id, "message": {"raw": frozen["raw"]}},
            )
        elif action == "gmail_draft_send":
            if not draft_id:
                raise ValueError("GMAIL_DRAFT_ID_REQUIRED")
            method, path, body = "POST", "/gmail/v1/users/me/drafts/send", {"id": draft_id}
        else:
            method, path, body = "POST", "/gmail/v1/users/me/messages/send", {"raw": frozen["raw"]}
        response = await self._requester(method, path, headers, body)
        message = response.get("message") if isinstance(response.get("message"), dict) else response
        return {
            "status": "accepted_by_gmail",
            "accepted_by_gmail": True,
            "action": action,
            "draft_id": response.get("id") if action in {"gmail_draft_create", "gmail_draft_update"} else draft_id,
            "draft_message_id": message.get("id") if action in {"gmail_draft_create", "gmail_draft_update"} else None,
            "sent_message_id": message.get("id") if action in {"gmail_draft_send", "gmail_message_send"} else None,
            "thread_id": message.get("threadId"),
            "submitted_raw_sha256": frozen.get("submitted_raw_sha256"),
            "rfc_message_id": frozen.get("rfc_message_id"),
        }
