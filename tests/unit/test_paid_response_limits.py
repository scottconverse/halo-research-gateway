"""Real HTTPX streaming contracts against a local fake vendor transport."""

import asyncio
import json

import httpx

from halo_research_gateway.providers import paid


class Payload(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
        self.reads = 0
        self.closed = False

    async def __aiter__(self):
        for chunk in self.chunks:
            self.reads += 1
            yield chunk

    async def aclose(self):
        self.closed = True


def install(monkeypatch, stream, status=200):
    async def resolve(target):
        return "93.184.216.34"

    async def reply(request):
        return httpx.Response(status, headers={"content-type": "application/json"}, stream=stream)

    monkeypatch.setattr(paid, "resolve_public", resolve)
    monkeypatch.setattr(paid, "PinnedTransport", lambda *args: httpx.MockTransport(reply))


async def test_paid_api_stops_reading_at_response_cap_and_closes(monkeypatch):
    stream = Payload([b"x" * 65, b"never read"])
    install(monkeypatch, stream)
    adapter = paid.BrightDataUnlockerAdapter()
    adapter.max_response_bytes = 64
    error = None
    try:
        await adapter(domain="example.org", secret={"api_key": "fixture", "zone": "fixture"}, url="https://example.org")
    except Exception as exc:
        error = exc
    assert isinstance(error, ValueError) and str(error) == "OPTIONAL_PROVIDER_RESPONSE_TOO_LARGE"
    assert stream.reads == 1 and stream.closed


async def test_paid_api_rejects_non_object_json_without_leaking_body(monkeypatch):
    stream = Payload([b'["fixture-private"]'])
    install(monkeypatch, stream)
    error = None
    try:
        await paid.BrightDataUnlockerAdapter()(
            domain="example.org", secret={"api_key": "fixture", "zone": "fixture"}, url="https://example.org"
        )
    except Exception as exc:
        error = exc
    assert isinstance(error, ValueError) and str(error) == "OPTIONAL_PROVIDER_RESPONSE_INVALID"
    assert stream.closed


async def test_paid_api_wall_clock_timeout_closes_slow_stream(monkeypatch):
    class Slow(Payload):
        async def __aiter__(self):
            await asyncio.sleep(0.1)
            yield json.dumps({"body": "late", "status_code": 200}).encode()

    stream = Slow([])
    install(monkeypatch, stream)
    adapter = paid.BrightDataUnlockerAdapter()
    adapter.timeout_seconds = 0.02
    error = None
    try:
        await adapter(domain="example.org", secret={"api_key": "fixture", "zone": "fixture"}, url="https://example.org")
    except Exception as exc:
        error = exc
    assert isinstance(error, TimeoutError), "Paid response has no total wall-clock limit"
    assert stream.closed


async def test_explicit_raw_unlocker_response_remains_supported(monkeypatch):
    stream = Payload([b"<p>Raw source evidence</p>"])
    install(monkeypatch, stream)
    result, error = None, None
    try:
        result = await paid.BrightDataUnlockerAdapter()(
            domain="example.org",
            secret={"api_key": "fixture", "zone": "fixture"},
            url="https://example.org",
            output_format="raw",
        )
    except Exception as exc:
        error = exc
    assert error is None, f"Raw Unlocker response cannot be decoded: {error}"
    assert result["body"] == "<p>Raw source evidence</p>"
    assert stream.closed


async def test_capsolver_total_deadline_includes_create_and_poll_requests():
    async def pending(*args):
        await asyncio.sleep(0.1)
        return {"status": "ready", "solution": {"token": "fixture"}}

    adapter = paid.CapSolverAdapter(requester=pending)
    adapter.solve_timeout_seconds = 0.02
    error = None
    try:
        await adapter(domain="example.org", secret={"api_key": "fixture"}, task={"websiteURL": "https://example.org"})
    except Exception as exc:
        error = exc
    assert isinstance(error, TimeoutError), "Solver creation bypasses the overall solve deadline"
