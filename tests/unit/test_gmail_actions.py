import base64
import hashlib
import json
import urllib.parse

import pytest

from halo_research_gateway.actions.gmail import GMAIL_COMPOSE_SCOPE, GmailComposeAdapter, freeze_mime
from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.service import HaloService


class Connections:
    def get(self, connection_id):
        return {
            "connection_id": connection_id,
            "provider": "Gmail",
            "status": "ready",
            "scopes": [GMAIL_COMPOSE_SCOPE],
        }

    def secret(self, connection_id):
        return {"access_token": "opaque-google-token"}


def test_freeze_mime_is_deterministic_and_hashes_exact_submitted_bytes():
    values = dict(
        sender="scott@example.com",
        to=["alice@example.com"],
        cc=["bob@example.com"],
        subject="Gateway evidence",
        text="A deterministic body.\n",
        message_id="<halo-plan-1@example.com>",
    )
    first = freeze_mime(**values)
    second = freeze_mime(**values)
    raw = base64.urlsafe_b64decode(first["raw"] + "=" * (-len(first["raw"]) % 4))
    assert first == second
    assert first["submitted_raw_sha256"] == hashlib.sha256(raw).hexdigest()
    assert b"Message-ID: <halo-plan-1@example.com>" in raw
    assert "opaque-google-token" not in json.dumps(first)


@pytest.mark.asyncio
async def test_create_draft_preserves_distinct_draft_and_message_ids():
    calls = []

    async def request(method, path, headers, body):
        calls.append((method, path, headers, body))
        return {"id": "draft-7", "message": {"id": "draft-message-9", "threadId": "thread-2"}}

    frozen = freeze_mime(to=["alice@example.com"], subject="Draft", text="Body", sender=None)
    result = await GmailComposeAdapter(Connections(), request).execute(
        {
            "action": "gmail_draft_create",
            "connection_id": "gmail-1",
            "gmail": frozen,
        }
    )
    assert result["draft_id"] == "draft-7"
    assert result["draft_message_id"] == "draft-message-9"
    assert result["sent_message_id"] is None
    assert result["accepted_by_gmail"] is True
    assert calls[0][0:2] == ("POST", "/gmail/v1/users/me/drafts")
    assert calls[0][2]["Authorization"] == "Bearer opaque-google-token"
    assert "opaque-google-token" not in json.dumps(result)


@pytest.mark.asyncio
async def test_send_draft_records_new_sent_message_without_equating_ids():
    async def request(method, path, headers, body):
        assert body == {"id": "draft-7"}
        return {"id": "sent-message-10", "threadId": "thread-2"}

    result = await GmailComposeAdapter(Connections(), request).execute(
        {
            "action": "gmail_draft_send",
            "connection_id": "gmail-1",
            "gmail": {"draft_id": "draft-7", "submitted_raw_sha256": "abc"},
        }
    )
    assert result["draft_id"] == "draft-7"
    assert result["draft_message_id"] is None
    assert result["sent_message_id"] == "sent-message-10"
    assert result["status"] == "accepted_by_gmail"


@pytest.mark.asyncio
async def test_compose_scope_is_required_without_broadening_consent():
    class WrongScope(Connections):
        def get(self, connection_id):
            value = super().get(connection_id)
            value["scopes"] = ["https://www.googleapis.com/auth/gmail.send"]
            return value

    with pytest.raises(PermissionError, match="GMAIL_COMPOSE_SCOPE_REQUIRED"):
        await GmailComposeAdapter(WrongScope(), lambda *args: None).execute(
            {
                "action": "gmail_message_send",
                "connection_id": "gmail-1",
                "gmail": {"raw": "Zm9v", "submitted_raw_sha256": "abc"},
            }
        )


@pytest.mark.asyncio
async def test_service_freezes_approved_gmail_payload_and_executes_once(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    connection = service.connections.create(
        "Gmail",
        "Scott Gmail",
        "oauth",
        {"access_token": "opaque-google-token"},
        [GMAIL_COMPOSE_SCOPE],
    )
    calls = 0

    async def request(method, path, headers, body):
        nonlocal calls
        calls += 1
        return {"id": "draft-7", "message": {"id": "draft-message-9", "threadId": "thread-2"}}

    service.gmail._requester = request
    try:
        prepared = service.web_action_prepare(
            "gmail_draft_create",
            "gmail://me",
            "Draft an exact reviewed message",
            {"to": ["alice@example.com"], "subject": "Reviewed", "text": "Frozen body"},
            connection["connection_id"],
        )
        assert "opaque-google-token" not in json.dumps(prepared)
        assert prepared["preview"]["gmail"]["submitted_raw_sha256"]
        token = service.actions.approve(prepared["plan_id"])
        receipt = await service.web_action_execute(prepared["plan_id"], token, "gmail-once")
    finally:
        await service.close()

    assert calls == 1
    assert receipt["outcome"]["draft_id"] == "draft-7"
    assert receipt["outcome"]["draft_message_id"] == "draft-message-9"


@pytest.mark.asyncio
async def test_gmail_oauth_policy_forces_offline_narrow_compose_consent(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    try:
        begun = await service.oauth_begin(
            provider="Gmail",
            label="Scott Gmail",
            authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
            token_endpoint="https://oauth2.googleapis.com/token",
            client_id="desktop-client-id",
            client_secret="desktop-client-secret",
            scopes=[GMAIL_COMPOSE_SCOPE],
        )
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(begun["authorization_url"]).query)
        assert query["scope"] == [GMAIL_COMPOSE_SCOPE]
        assert query["access_type"] == ["offline"]
        assert query["include_granted_scopes"] == ["true"]
        assert query["code_challenge_method"] == ["S256"]
    finally:
        await service.close()


@pytest.mark.asyncio
async def test_gmail_oauth_rejects_broader_scope_before_opening_listener(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    try:
        with pytest.raises(ValueError, match="GMAIL_OAUTH_POLICY_MISMATCH"):
            await service.oauth_begin(
                provider="Gmail",
                label="Scott Gmail",
                authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
                token_endpoint="https://oauth2.googleapis.com/token",
                client_id="desktop-client-id",
                scopes=["https://mail.google.com/"],
            )
    finally:
        await service.close()
