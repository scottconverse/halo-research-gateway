"""Local research must honor operator methods and not echo session query values."""

import json
from urllib.parse import parse_qs, urlsplit

import pytest
from test_research_response_bounds import Payload, install
from test_research_response_bounds import service as service

from halo_research_gateway.security import redact_url


@pytest.mark.parametrize("methods", [["HEAD"], []])
async def test_get_is_denied_before_network_when_operator_did_not_allow_it(monkeypatch, service, methods):
    stream = Payload([b"must not be fetched"])
    calls = install(monkeypatch, stream)
    service.config.local_targets["fixture"].methods = methods
    result = await service.local_fetch("fixture", "/research/source")
    assert not result["ok"] and result["error"]["code"] == "LOCAL_METHOD_NOT_ALLOWED"
    assert calls == [] and stream.reads == 0
    assert service.coordinator.stats()["http"]["pending"] == 0


@pytest.mark.parametrize("name", ["token", "api_key", "X-Amz-Signature", "session", "auth_code"])
async def test_session_query_reaches_source_but_not_evidence(monkeypatch, service, name):
    stream = Payload([b"Allowed research evidence"])
    calls = install(monkeypatch, stream)
    secret = "fixture-private-query-value"
    result = await service.local_fetch("fixture", f"/research/source?{name}={secret}&q=research")
    assert result["ok"], result
    assert calls[0].url.params[name] == secret
    assert result["items"][0]["content"] == "Allowed research evidence"
    assert secret not in json.dumps(result)
    assert "SENSITIVE_URL_NOT_CACHED" in result["warnings"]
    query = parse_qs(urlsplit(result["items"][0]["url"]).query)
    assert query[name] == ["[REDACTED]"] and query["q"] == ["[REDACTED]"]
    assert all(secret.encode() not in payload for payload, _ in service._snapshots.values())
    assert service.cache.stats()["entries"] == 0


async def test_sensitive_local_cursor_preserves_text_without_restoring_query(monkeypatch, service):
    body = "Pageable local evidence. " * 200
    service.config.http.max_decompressed_bytes = 10000
    stream = Payload([body.encode()])
    calls = install(monkeypatch, stream)
    secret = "fixture-paged-query-value"
    result = await service.local_fetch("fixture", f"/research/source?token={secret}", max_chars=2000)
    content, pages = "", 0
    while True:
        assert result["ok"], result
        assert secret not in json.dumps(result)
        content += "".join(item.get("content") or "" for item in result["items"])
        pages += 1
        cursor = result["page"]["next_cursor"]
        if not cursor:
            break
        assert pages < 100
        result = await service.local_fetch(cursor=cursor)
    assert content == body and pages > 1 and len(calls) == 1
    assert service.cache.stats()["entries"] == 0


async def test_ordinary_get_query_and_citation_remain_intact(monkeypatch, service):
    stream = Payload([b"ordinary evidence"])
    calls = install(monkeypatch, stream)
    result = await service.local_fetch("fixture", "/research/source?q=ordinary&page=2")
    assert result["ok"], result
    assert calls[0].method == "GET"
    assert result["items"][0]["url"] == "http://127.0.0.1:3090/research/source?q=ordinary&page=2"
    assert "SENSITIVE_URL_NOT_CACHED" not in result["warnings"]


def test_redacted_ipv6_citation_remains_a_parseable_exact_origin():
    result = redact_url("http://[::1]:3090/research/source?token=fixture-value")
    assert result == "http://[::1]:3090/research/source?token=%5BREDACTED%5D"
    assert urlsplit(result).hostname == "::1" and urlsplit(result).port == 3090
