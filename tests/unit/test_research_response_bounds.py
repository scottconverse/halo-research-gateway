"""Response limits exercise real HTTPX streaming, not pre-buffered responses."""

import asyncio
import gzip
import json
from contextlib import asynccontextmanager

import httpx
import pytest

from halo_research_gateway.config import GatewayConfig, LocalTargetConfig
from halo_research_gateway.coordinator import QueuePolicy
from halo_research_gateway.providers import github
from halo_research_gateway.service import HaloService


class Payload(httpx.AsyncByteStream):
    def __init__(self, chunks, delay=0):
        self.chunks = chunks
        self.delay = delay
        self.reads = 0
        self.closed = False

    async def __aiter__(self):
        for chunk in self.chunks:
            await asyncio.sleep(self.delay)
            self.reads += 1
            yield chunk

    async def aclose(self):
        self.closed = True


@pytest.fixture
async def service(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    config.http.max_decompressed_bytes = 64
    config.http.per_origin_interval_seconds = 0
    config.local_targets["fixture"] = LocalTargetConfig(
        scheme="http", host="127.0.0.1", port=3090, path_prefixes=["/research"]
    )
    instance = HaloService(config)
    try:
        yield instance
    finally:
        await instance.close()


def install(monkeypatch, stream, headers=None, status=200):
    calls = []
    original = httpx.AsyncClient

    async def reply(request):
        calls.append(request)
        return httpx.Response(status, headers=headers or {}, stream=stream)

    def client(**kwargs):
        kwargs["transport"] = httpx.MockTransport(reply)
        return original(**kwargs)

    async def resolve(target):
        return "93.184.216.34"

    monkeypatch.setattr(httpx, "AsyncClient", client)
    monkeypatch.setattr(github, "resolve_public", resolve)
    monkeypatch.setattr(github, "PinnedTransport", lambda *args: None)
    return calls


@pytest.mark.parametrize("kind", ["local", "github"])
async def test_overflow_stops_before_next_chunk_and_closes(monkeypatch, service, kind):
    stream = Payload([b"x" * 65, b"must not be read"])
    install(monkeypatch, stream)
    if kind == "local":
        result = await service.local_fetch("fixture", "/research/source")
        assert not result["ok"] and result["error"]["code"] == "LOCAL_RESPONSE_TOO_LARGE"
    else:
        error = None
        try:
            await service.github._request_json("GET", "/search/issues", {}, None)
        except Exception as exc:
            error = exc
        assert isinstance(error, ValueError) and str(error) == "GITHUB_RESPONSE_TOO_LARGE"
    assert stream.reads == 1 and stream.closed


@pytest.mark.parametrize("kind", ["local", "github"])
async def test_compressed_response_is_limited_after_decoding(monkeypatch, service, kind):
    stream = Payload([gzip.compress(b'"' + b"x" * 1000 + b'"')])
    install(monkeypatch, stream, {"content-encoding": "gzip"})
    if kind == "local":
        result = await service.local_fetch("fixture", "/research/source")
        assert not result["ok"] and result["error"]["code"] == "LOCAL_RESPONSE_TOO_LARGE"
    else:
        error = None
        try:
            await service.github._request_json("GET", "/search/issues", {}, None)
        except Exception as exc:
            error = exc
        assert isinstance(error, ValueError) and str(error) == "GITHUB_RESPONSE_TOO_LARGE"
    assert stream.closed


@pytest.mark.parametrize("kind", ["local", "github"])
async def test_total_deadline_stops_slow_response(monkeypatch, service, kind):
    stream = Payload([b"{}"], delay=0.1)
    install(monkeypatch, stream)
    if kind == "local":
        service.config.http.total_timeout_seconds = 0.02
        result = await service.local_fetch("fixture", "/research/source")
        assert not result["ok"] and result["error"]["code"] == "LOCAL_REQUEST_TIMEOUT"
    else:
        service.github.timeout_seconds = 0.02
        error = None
        try:
            await service.github._request_json("GET", "/search/issues", {}, None)
        except Exception as exc:
            error = exc
        assert isinstance(error, TimeoutError) and str(error) == "GITHUB_REQUEST_TIMEOUT"
    assert stream.closed and stream.reads == 0


async def test_github_deadline_includes_dns(monkeypatch, service):
    stream = Payload([b"{}"])
    calls = install(monkeypatch, stream)

    async def slow_dns(target):
        await asyncio.sleep(0.1)
        return "93.184.216.34"

    monkeypatch.setattr(github, "resolve_public", slow_dns)
    service.github.timeout_seconds = 0.02
    error = None
    try:
        await service.github._request_json("GET", "/search/issues", {}, None)
    except Exception as exc:
        error = exc
    assert isinstance(error, TimeoutError) and str(error) == "GITHUB_REQUEST_TIMEOUT"
    assert calls == []


@pytest.mark.parametrize("body", [b'"fixture-private"', b'{"secret":"fixture-private"'])
async def test_github_rejects_invalid_json_shape_without_body(monkeypatch, service, body):
    stream = Payload([body])
    install(monkeypatch, stream)
    error = None
    try:
        await service.github._request_json("GET", "/search/issues", {}, None)
    except Exception as exc:
        error = exc
    assert isinstance(error, ValueError) and str(error) == "GITHUB_RESPONSE_INVALID"
    assert stream.closed


@pytest.mark.parametrize("body", [b"{}", b"[]", b'{"ok":true}', b'"' + b"x" * 62 + b'"'])
async def test_exact_cap_and_normal_evidence_remain_readable(monkeypatch, service, body):
    stream = Payload([body[:1], body[1:]])
    install(monkeypatch, stream)
    if body.startswith(b'"'):
        result = await service.local_fetch("fixture", "/research/source")
        assert result["ok"] and result["items"][0]["content"] == body.decode()
    else:
        assert await service.github._request_json("GET", "/search/issues", {}, None) == json.loads(body)
    assert stream.closed


async def test_local_read_obeys_shared_http_admission(monkeypatch, service):
    stream = Payload([b"evidence"])
    calls = install(monkeypatch, stream)
    service.coordinator.policies["http"] = QueuePolicy(1, 1, 1, 0)
    started, release = asyncio.Event(), asyncio.Event()

    async def occupied():
        started.set()
        await release.wait()

    task = asyncio.create_task(service.coordinator.run("http", "other-client", "occupied", occupied))
    try:
        await started.wait()
        result = await service.local_fetch("fixture", "/research/source", client="local-client")
        assert not result["ok"] and result["error"]["code"] == "QUEUE_FULL"
        assert calls == []
    finally:
        release.set()
        await task
    result = await service.local_fetch("fixture", "/research/source", client="local-client")
    assert result["ok"] and len(calls) == 1


async def test_local_read_uses_the_shared_origin_gate(monkeypatch, service):
    stream = Payload([b"evidence"])
    install(monkeypatch, stream)
    origins = []

    @asynccontextmanager
    async def gate(target):
        origins.append((target.scheme, target.host, target.port))
        yield

    monkeypatch.setattr(service.http, "_origin_gate", gate)
    result = await service.local_fetch("fixture", "/research/source")
    assert result["ok"]
    assert origins == [("http", "127.0.0.1", 3090)]


@pytest.mark.parametrize("kind", ["local", "github"])
async def test_cancel_closes_response_without_returning_partial_evidence(monkeypatch, service, kind):
    entered = asyncio.Event()

    class Waiting(Payload):
        async def __aiter__(self):
            entered.set()
            yield b"partial"
            await asyncio.Event().wait()

    stream = Waiting([])
    install(monkeypatch, stream)
    operation = (
        service.local_fetch("fixture", "/research/source")
        if kind == "local"
        else service.github._request_json("GET", "/search/issues", {}, None)
    )
    task = asyncio.create_task(operation)
    try:
        await asyncio.wait_for(entered.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        # Coordinator cleanup can finish in the next event-loop turn.
        for _ in range(100):
            if stream.closed:
                break
            await asyncio.sleep(0.001)
        assert stream.closed
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)


async def test_local_redirect_is_denied_without_body_or_second_request(monkeypatch, service):
    stream = Payload([b"private redirect body"])
    calls = install(monkeypatch, stream, {"location": "http://127.0.0.1/admin"}, status=302)
    result = await service.local_fetch("fixture", "/research/source")
    assert not result["ok"] and result["error"]["code"] == "LOCAL_REDIRECT_DENIED"
    assert len(calls) == 1 and stream.reads == 0 and stream.closed
