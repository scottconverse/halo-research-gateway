import pytest

from halo_research_gateway.providers.paid import BrightDataUnlockerAdapter, CapSolverAdapter


class Clock:
    def __init__(self):
        self.value = 0

    def monotonic(self):
        return self.value

    async def sleep(self, seconds):
        self.value += seconds


@pytest.mark.asyncio
async def test_capsolver_is_exact_domain_and_bounded():
    calls = []

    async def request(method, path, headers, body):
        calls.append((path, body))
        if path == "/createTask":
            return {"errorId": 0, "taskId": "task-1"}
        return {"errorId": 0, "status": "ready", "solution": {"token": "captcha-token"}}

    result = await CapSolverAdapter(Clock(), request)(
        domain="example.com",
        secret={"api_key": "capsolver-key"},
        task={"type": "ReCaptchaV2TaskProxyLess", "websiteURL": "https://example.com/challenge"},
    )
    assert result["status"] == "ready"
    assert result["task_id"] == "task-1"
    assert [call[0] for call in calls] == ["/createTask", "/getTaskResult"]


@pytest.mark.asyncio
async def test_capsolver_rejects_cross_domain_and_callbacks_before_spend_call():
    async def unexpected(*args):
        raise AssertionError("provider must not be called")

    adapter = CapSolverAdapter(Clock(), unexpected)
    with pytest.raises(ValueError, match="TARGET_MISMATCH"):
        await adapter(
            domain="example.com",
            secret={"api_key": "key"},
            task={"type": "ReCaptchaV2TaskProxyLess", "websiteURL": "https://evil.example/challenge"},
        )
    with pytest.raises(ValueError, match="CALLBACK_NOT_ALLOWED"):
        await adapter(
            domain="example.com",
            secret={"api_key": "key"},
            task={
                "type": "ReCaptchaV2TaskProxyLess",
                "websiteURL": "https://example.com/challenge",
                "callbackUrl": "https://callback.example",
            },
        )


@pytest.mark.asyncio
async def test_brightdata_uses_fixed_api_and_never_exposes_key_in_result():
    calls = []

    async def request(method, path, headers, body):
        calls.append((method, path, headers, body))
        return {"status_code": 200, "headers": {"content-type": "text/html"}, "body": "<p>ok</p>"}

    result = await BrightDataUnlockerAdapter(request)(
        domain="example.com",
        secret={"api_key": "bright-secret", "zone": "halo_unlocker"},
        url="https://example.com/page#fragment",
        country="US",
    )
    assert result["target"] == "https://example.com/page"
    assert result["body"] == "<p>ok</p>"
    assert calls[0][0:2] == ("POST", "/request")
    assert calls[0][2]["Authorization"] == "Bearer bright-secret"
    assert "bright-secret" not in repr(result)
