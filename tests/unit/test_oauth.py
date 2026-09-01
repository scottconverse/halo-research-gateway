import asyncio
import urllib.parse

import httpx
import pytest

from halo_research_gateway.connections.oauth import OAuthFlowError, OAuthManager


class FakeConnections:
    def __init__(self):
        self.created = None
        self.values = {}

    def create(self, provider, label, kind, secret, scopes):
        self.created = {"connection_id": "one", "provider": provider, "label": label, "type": kind, "scopes": scopes}
        self.values["one"] = secret
        return self.created

    def secret(self, connection_id):
        return dict(self.values[connection_id])

    def replace_secret(self, connection_id, secret):
        self.values[connection_id] = secret

    def get(self, connection_id):
        return {"connection_id": connection_id, "status": "ready"}


@pytest.mark.asyncio
async def test_oauth_pkce_loopback_validates_state_and_stores_tokens(monkeypatch):
    connections = FakeConnections()
    manager = OAuthManager(connections)
    sent = {}

    async def token_request(url, payload):
        sent.update(payload)
        return {"access_token": "access-secret", "refresh_token": "refresh-secret", "token_type": "Bearer"}

    monkeypatch.setattr(manager, "_token_request", token_request)
    begun = await manager.begin(
        provider="fixture",
        label="Scott",
        authorization_endpoint="https://auth.example.com/authorize",
        token_endpoint="https://auth.example.com/token",
        client_id="client",
        scopes=["read", "profile"],
    )
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(begun["authorization_url"]).query)
    assert query["code_challenge_method"] == ["S256"]
    complete = asyncio.create_task(manager.complete(begun["flow_id"]))
    async with httpx.AsyncClient(trust_env=False) as client:
        response = await client.get(begun["redirect_uri"], params={"code": "code", "state": query["state"][0]})
    assert response.status_code == 200
    result = await complete
    assert result["connection_id"] == "one"
    assert sent["code_verifier"]
    assert connections.values["one"]["access_token"] == "access-secret"
    assert "access-secret" not in repr(result)


@pytest.mark.asyncio
async def test_oauth_rejects_wrong_state(monkeypatch):
    manager = OAuthManager(FakeConnections())
    begun = await manager.begin(
        provider="fixture",
        label="Scott",
        authorization_endpoint="https://auth.example.com/authorize",
        token_endpoint="https://auth.example.com/token",
        client_id="client",
        scopes=["read"],
    )
    complete = asyncio.create_task(manager.complete(begun["flow_id"]))
    async with httpx.AsyncClient(trust_env=False) as client:
        response = await client.get(begun["redirect_uri"], params={"code": "code", "state": "wrong"})
    assert response.status_code == 400
    with pytest.raises(OAuthFlowError, match="OAUTH_STATE_MISMATCH"):
        await complete


@pytest.mark.asyncio
async def test_oauth_cannot_override_pkce_or_state_parameters():
    manager = OAuthManager(FakeConnections())
    with pytest.raises(OAuthFlowError, match="OAUTH_RESERVED_PARAMETER"):
        await manager.begin(
            provider="fixture",
            label="Scott",
            authorization_endpoint="https://auth.example.com/authorize",
            token_endpoint="https://auth.example.com/token",
            client_id="client",
            scopes=["read"],
            extra_authorize={"state": "attacker-selected"},
        )


@pytest.mark.asyncio
async def test_oauth_refresh_replaces_secret_without_returning_it(monkeypatch):
    connections = FakeConnections()
    connections.values["one"] = {
        "access_token": "old",
        "refresh_token": "refresh-secret",
        "client_id": "client",
        "token_endpoint": "https://auth.example.com/token",
    }
    manager = OAuthManager(connections)

    async def token_request(url, payload):
        assert url == "https://auth.example.com/token"
        assert payload["refresh_token"] == "refresh-secret"
        return {"access_token": "new", "refresh_token": "rotated"}

    monkeypatch.setattr(manager, "_token_request", token_request)
    result = await manager.refresh("one")
    assert result == {"connection_id": "one", "status": "ready"}
    assert connections.values["one"]["access_token"] == "new"
    assert "new" not in repr(result)
