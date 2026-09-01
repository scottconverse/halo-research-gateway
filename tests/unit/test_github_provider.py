import asyncio
import base64
import json
from datetime import UTC, datetime

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from halo_research_gateway.config import GatewayConfig
from halo_research_gateway.models import EvidenceItem, ProviderResult
from halo_research_gateway.providers.github import GitHubProvider, build_app_jwt
from halo_research_gateway.service import HaloService


class FixedClock:
    now = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)

    def utcnow(self):
        return self.now

    @staticmethod
    def parse_rfc3339(value):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


class Connections:
    def __init__(self, secret):
        self.value = secret

    def list(self):
        return [
            {
                "connection_id": "github-1",
                "provider": "GitHub App",
                "status": "ready",
            }
        ]

    def secret(self, connection_id):
        assert connection_id == "github-1"
        return self.value


def private_key_pem():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()


def test_app_jwt_uses_short_lived_issuer_claims():
    token = build_app_jwt("12345", private_key_pem(), 1_788_264_000)
    _, payload, _ = token.split(".")
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    assert claims == {"iat": 1_788_263_940, "exp": 1_788_264_540, "iss": "12345"}


@pytest.mark.asyncio
async def test_github_app_token_stays_internal_and_structured_results_are_returned():
    calls = []

    async def request(method, path, headers, body):
        calls.append((method, path, headers, body))
        if path.endswith("/access_tokens"):
            return {"token": "ghs_secret_installation_token", "expires_at": "2026-09-01T13:00:00Z"}
        return {
            "items": [
                {
                    "html_url": "https://github.com/acme/widgets/issues/7",
                    "title": "Widget race",
                    "body": "Reproduction details",
                    "number": 7,
                    "state": "open",
                    "created_at": "2026-08-30T10:00:00Z",
                    "user": {"login": "octocat"},
                    "repository_url": "https://api.github.com/repos/acme/widgets",
                }
            ]
        }

    provider = GitHubProvider(
        Connections({"app_id": "123", "installation_id": "456", "private_key_pem": private_key_pem()}),
        FixedClock(),
        request,
    )
    result = await provider.research("race", "acme/widgets", ["issues"], None, 10)
    assert result.provider == "github-api"
    assert result.items[0].metadata["number"] == 7
    assert result.items[0].metadata["author"] == "octocat"
    assert "ghs_secret_installation_token" not in json.dumps(result.items[0].as_dict())
    assert calls[0][0:2] == ("POST", "/app/installations/456/access_tokens")
    assert calls[1][2]["Authorization"] == "Bearer ghs_secret_installation_token"


@pytest.mark.asyncio
async def test_installation_token_is_reused_until_near_expiry():
    calls = []

    async def request(method, path, headers, body):
        calls.append(path)
        if path.endswith("/access_tokens"):
            return {"token": "ghs_token", "expires_at": "2026-09-01T13:00:00Z"}
        return {"items": []}

    provider = GitHubProvider(
        Connections({"app_id": "123", "installation_id": "456", "private_key_pem": private_key_pem()}),
        FixedClock(),
        request,
    )
    await provider.research("one", None, ["issues"], None, 5)
    await provider.research("two", None, ["issues"], None, 5)
    assert calls.count("/app/installations/456/access_tokens") == 1


@pytest.mark.asyncio
async def test_concurrent_research_mints_one_installation_token():
    calls = []

    async def request(method, path, headers, body):
        calls.append(path)
        if path.endswith("/access_tokens"):
            await asyncio.sleep(0)
            return {"token": "ghs_token", "expires_at": "2026-09-01T13:00:00Z"}
        return {"items": []}

    provider = GitHubProvider(
        Connections({"app_id": "123", "installation_id": "456", "private_key_pem": private_key_pem()}),
        FixedClock(),
        request,
    )
    await asyncio.gather(
        provider.research("one", None, ["issues"], None, 5),
        provider.research("two", None, ["issues"], None, 5),
    )
    assert calls.count("/app/installations/456/access_tokens") == 1


@pytest.mark.asyncio
async def test_missing_connection_degrades_without_requesting_network():
    class EmptyConnections:
        def list(self):
            return []

    async def unexpected(*args):
        raise AssertionError("network should not be called")

    result = await GitHubProvider(EmptyConnections(), FixedClock(), unexpected).research("query", None, None, None, 5)
    assert result.items == []
    assert result.warnings == ["GITHUB_AUTH_NOT_CONFIGURED"]


@pytest.mark.asyncio
async def test_service_forwards_structured_query_and_returns_github_envelope(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)
    captured = {}

    class StructuredGitHub:
        async def research(self, query, repository, kinds, ref, max_results):
            captured.update(
                query=query,
                repository=repository,
                kinds=kinds,
                ref=ref,
                max_results=max_results,
            )
            return ProviderResult(
                "github-api",
                [
                    EvidenceItem(
                        title="Pinned evidence",
                        url="https://github.com/acme/widgets/blob/abc123/README.md",
                        retrieved_at="2026-09-01T12:00:00Z",
                        source="api.github.com",
                        metadata={"repository": "acme/widgets", "sha": "abc123", "path": "README.md"},
                    )
                ],
                [],
                1,
            )

    service.github = StructuredGitHub()
    try:
        result = await service.github_research(
            "install",
            "acme/widgets",
            ["docs"],
            "abc123",
            7,
            4000,
            None,
            "known-planner",
        )
    finally:
        await service.close()

    assert result["ok"] is True
    assert result["tool"] == "github_research"
    assert result["provider"] == "github-api"
    assert result["items"][0]["metadata"]["sha"] == "abc123"
    assert captured == {
        "query": "install",
        "repository": "acme/widgets",
        "kinds": ["docs"],
        "ref": "abc123",
        "max_results": 7,
    }
