"""Whole GitHub operations share one deadline and decoded-response byte budget."""

import asyncio
import base64
import json

import httpx
import pytest
from test_github_provider import Connections, private_key_pem

from halo_research_gateway.providers import github
from halo_research_gateway.providers.github import GitHubProvider


def item(number=1):
    return {"html_url": f"https://github.com/acme/widgets/issues/{number}", "title": f"Evidence {number}"}


def thread():
    return {
        "data": {
            "repository": {
                "discussion": {
                    "url": "https://github.com/acme/widgets/discussions/7",
                    "bodyText": "Root evidence",
                    "comments": {
                        "nodes": [
                            {
                                "id": "C1",
                                "url": "https://github.com/acme/widgets/discussions/7#discussioncomment-1",
                                "bodyText": "Parent evidence",
                                "replies": {
                                    "nodes": [],
                                    "pageInfo": {"hasNextPage": True, "endCursor": "next"},
                                },
                            }
                        ],
                        "pageInfo": {"hasNextPage": False},
                    },
                }
            }
        }
    }


async def captured(operation):
    try:
        return await operation, None
    except Exception as error:
        return None, error


@pytest.mark.parametrize("kind", ["kinds", "ref", "discussion", "mint"])
async def test_deadline_covers_entire_sequence_not_each_request(kind):
    calls = []
    closed = []

    async def request(method, path, headers, body):
        calls.append(path)
        try:
            # Each request is under 250 ms, while two together exceed it.
            # Keep enough headroom for native Windows timer granularity.
            await asyncio.sleep(0.1 if len(calls) == 1 else 0.2)
            if path.endswith("/access_tokens"):
                return {"token": "fixture-installation-token"}
            if "/commits/" in path:
                return {"sha": "a" * 40, "commit": {"tree": {"sha": "b" * 40}}}
            if "/git/trees/" in path:
                return {"tree": [{"type": "blob", "path": "README.md", "sha": "c" * 40, "size": 8}]}
            if "/git/blobs/" in path:
                return {"encoding": "base64", "content": base64.b64encode(b"evidence").decode()}
            if path == "/graphql":
                if body["variables"].get("id"):
                    return {"data": {"node": {"replies": {"nodes": [], "pageInfo": {"hasNextPage": False}}}}}
                return thread()
            return {"items": [item(len(calls))]}
        finally:
            closed.append(path)

    secret = {"token": "fixture-token"}
    if kind == "mint":
        secret = {"app_id": "1", "installation_id": "2", "private_key_pem": private_key_pem()}
    provider = GitHubProvider(Connections(secret), requester=request, timeout_seconds=0.25)
    if kind == "discussion":
        operation = provider.discussion_thread("acme/widgets", 7, 10)
    else:
        operation = provider.research(
            "evidence",
            "acme/widgets",
            ["docs"] if kind == "ref" else ["issues", "pulls"],
            "main" if kind == "ref" else None,
            10,
        )
    result, error = await captured(operation)
    assert result is None and isinstance(error, TimeoutError), f"Unbounded sequence returned {result}, {error}"
    assert str(error) == "GITHUB_OPERATION_TIMEOUT"
    assert len(calls) == 2 and closed == calls


async def test_deadline_includes_waiting_for_installation_token_lock():
    calls = []

    async def request(*args):
        calls.append(args)
        return {"items": []}

    provider = GitHubProvider(
        Connections({"app_id": "1", "installation_id": "2", "private_key_pem": private_key_pem()}),
        requester=request,
        timeout_seconds=0.02,
    )
    await provider._mint_lock.acquire()
    try:
        result, error = await captured(asyncio.wait_for(provider.research("query", None, ["issues"], None, 1), 0.2))
        assert result is None and str(error) == "GITHUB_OPERATION_TIMEOUT", (
            f"Lock escaped operation deadline: {error!r}"
        )
        assert calls == []
    finally:
        provider._mint_lock.release()


class Stream(httpx.AsyncByteStream):
    def __init__(self, payload):
        self.payload = payload
        self.closed = False
        self.reads = 0

    async def __aiter__(self):
        self.reads += 1
        yield self.payload
        self.reads += 1
        yield b" "

    async def aclose(self):
        self.closed = True


def network(monkeypatch, payloads):
    """Keep production request streaming/JSON decoding; replace only the transport."""
    calls, streams = [], []
    original = httpx.AsyncClient

    async def response(request):
        calls.append(request.url.path)
        stream = Stream(payloads[min(len(calls) - 1, len(payloads) - 1)])
        streams.append(stream)
        await asyncio.sleep(0)  # Force concurrent operations to overlap.
        return httpx.Response(200, stream=stream)

    def client(**kwargs):
        kwargs["transport"] = httpx.MockTransport(response)
        return original(**kwargs)

    async def resolve(target):
        return "93.184.216.34"

    monkeypatch.setattr(httpx, "AsyncClient", client)
    monkeypatch.setattr(github, "PinnedTransport", lambda *args: None)
    monkeypatch.setattr(github, "resolve_public", resolve)
    return calls, streams


async def test_decoded_bytes_accumulate_across_requests_and_stop_before_next_chunk(monkeypatch):
    payload = json.dumps({"items": [item()]}).encode()
    calls, streams = network(monkeypatch, [payload])
    provider = GitHubProvider(Connections({"token": "fixture-token"}), max_response_bytes=len(payload) + 2)
    result, error = await captured(provider.research("query", None, ["issues", "pulls"], None, 10))
    assert result is None and isinstance(error, ValueError), f"Aggregate bytes ignored: {result}, {error}"
    assert str(error) == "GITHUB_OPERATION_TOO_LARGE"
    assert len(calls) == 2 and all(stream.closed for stream in streams)
    assert [stream.reads for stream in streams] == [2, 1]


async def test_token_response_counts_toward_operation_bytes(monkeypatch):
    token = json.dumps({"token": "fixture-installation-token"}).encode()
    payload = json.dumps({"items": [item()]}).encode()
    calls, streams = network(monkeypatch, [token, payload])
    provider = GitHubProvider(
        Connections({"app_id": "1", "installation_id": "2", "private_key_pem": private_key_pem()}),
        max_response_bytes=max(len(token), len(payload)) + 2,
    )
    result, error = await captured(provider.research("query", None, ["issues"], None, 1))
    assert result is None and str(error) == "GITHUB_OPERATION_TOO_LARGE", f"Mint body not counted: {result}, {error}"
    assert calls[0].endswith("/access_tokens")
    assert all(stream.closed for stream in streams)


async def test_budgets_reset_after_error_and_are_isolated_between_concurrent_callers(monkeypatch):
    payload = json.dumps({"items": [item()]}).encode()
    calls, streams = network(monkeypatch, [payload])
    provider = GitHubProvider(Connections({"token": "fixture-token"}), max_response_bytes=len(payload) + 1)
    _, error = await captured(provider.research("oversized", None, ["issues", "pulls"], None, 10))
    assert str(error) == "GITHUB_OPERATION_TOO_LARGE"
    results = await asyncio.gather(
        provider.research("first", None, ["issues"], None, 1),
        provider.research("second", None, ["issues"], None, 1),
    )
    assert all(len(result.items) == 1 for result in results)
    assert len(calls) == 4 and all(stream.closed for stream in streams)


async def test_external_cancel_is_not_converted_to_timeout_and_does_not_poison_next_operation():
    entered = asyncio.Event()
    closed = asyncio.Event()

    async def request(*args):
        try:
            entered.set()
            await asyncio.Event().wait()
        finally:
            closed.set()

    provider = GitHubProvider(Connections({"token": "fixture-token"}), requester=request)
    task = asyncio.create_task(provider.research("cancel", None, ["issues"], None, 1))
    try:
        await asyncio.wait_for(entered.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert closed.is_set()
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)

    async def normal(*args):
        return {"items": [item()]}

    provider._requester = normal
    result = await provider.research("normal", None, ["issues"], None, 1)
    assert len(result.items) == 1


async def test_service_exposes_operation_failure_without_private_evidence_or_public_fallback(tmp_path):
    from halo_research_gateway.config import GatewayConfig
    from halo_research_gateway.service import HaloService

    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    service = HaloService(config)

    async def request(*args):
        await asyncio.sleep(0.04)
        return {"items": [dict(item(), body="fixture-private-body")]}

    service.github = GitHubProvider(Connections({"token": "fixture-token"}), requester=request, timeout_seconds=0.06)

    async def forbidden(*args, **kwargs):
        raise AssertionError("Authenticated timeout must not trigger public fallback")

    service._search_result = forbidden
    try:
        result = await service.github_research("query", kinds=["issues", "pulls"], max_results=10)
        assert not result["ok"] and result["error"]["code"] == "GITHUB_OPERATION_TIMEOUT", result
        assert result["items"] == []
        assert "fixture-private-body" not in json.dumps(result)
    finally:
        await service.close()


async def test_request_timeout_keeps_its_specific_code_when_total_deadline_has_not_expired():
    async def request(*args):
        raise TimeoutError("GITHUB_REQUEST_TIMEOUT")

    provider = GitHubProvider(Connections({"token": "fixture-token"}), requester=request)
    _, error = await captured(provider.research("query", None, ["issues"], None, 1))
    assert str(error) == "GITHUB_REQUEST_TIMEOUT"


async def test_synchronous_over_deadline_result_is_not_reported_as_success():
    import time

    async def request(*args):
        # The event loop cannot preempt native/synchronous work. Verify the
        # result is rejected after it returns, without claiming preemption.
        time.sleep(0.04)  # noqa: ASYNC251 -- deliberately reproduce a synchronous provider stall
        return {"items": [item()]}

    provider = GitHubProvider(Connections({"token": "fixture-token"}), requester=request, timeout_seconds=0.01)
    result, error = await captured(provider.research("query", None, ["issues"], None, 1))
    assert result is None and str(error) == "GITHUB_OPERATION_TIMEOUT"
