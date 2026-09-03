"""Expected job-control failures must reach MCP callers as safe explicit codes."""

from types import SimpleNamespace

import pytest
from mcp.server.mcpserver import Context
from mcp.server.mcpserver.exceptions import UnexpectedToolError

from halo_research_gateway.app import create_application
from halo_research_gateway.config import GatewayConfig


@pytest.fixture
async def app(tmp_path):
    config = GatewayConfig()
    config.storage.database = str(tmp_path / "state" / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    application = create_application(config)
    try:
        yield application
    finally:
        await application.state.halo_service.close()


async def call(app, arguments):
    context = Context(
        request_context=SimpleNamespace(request=SimpleNamespace(headers={})),
        mcp_server=app.state.mcp_server,
    )
    return await app.state.mcp_server._tool_manager.call_tool("research_job", arguments, context)


@pytest.mark.parametrize(
    "case,code",
    [
        ("missing", "JOB_NOT_FOUND"),
        ("other_owner", "JOB_NOT_OWNED"),
        ("terminal", "JOB_STATE_CONFLICT"),
        ("limits", "INVALID_JOB_LIMITS"),
        ("capacity", "JOB_CAPACITY_REACHED"),
        ("empty", "INVALID_ARGUMENT"),
    ],
)
async def test_expected_job_failure_has_explicit_safe_mcp_code(app, case, code):
    service = app.state.halo_service
    arguments = {"operation": "status", "job_id": "missing-fixture-job"}
    if case in {"other_owner", "terminal"}:
        job = service.jobs.create("other" if case == "other_owner" else "unidentified", "fixture", {})
        arguments["job_id"] = job["job_id"]
        if case == "terminal":
            service.jobs.transition(job["job_id"], "unidentified", "cancel")
            arguments["operation"] = "resume"
    elif case in {"limits", "capacity", "empty"}:
        arguments = {"operation": "create", "question": "fixture"}
        if case == "limits":
            arguments["limits"] = {"max_pages": 0}
        elif case == "capacity":
            service.config.jobs.max_active = 1
            service.jobs.create("unidentified", "occupied fixture", {})
        else:
            arguments["question"] = ""
    count_before = len(service.jobs.list())
    try:
        result = await call(app, arguments)
    except Exception:
        result = {"error": {"code": "GENERIC_MCP_EXCEPTION"}}
    assert result.get("error", {}).get("code") == code, "Caller lost the actionable job failure code"
    assert result["ok"] is False
    assert result["items"] == []
    assert "fixture" not in str(result)
    assert len(service.jobs.list()) == count_before


async def test_unexpected_job_exception_is_not_promoted_to_public_error_text(app):
    async def unexpected(*args, **kwargs):
        raise ValueError("fixture-sensitive-debug-detail")

    app.state.halo_service.research_job = unexpected
    with pytest.raises(UnexpectedToolError, match="Error executing tool research_job") as failure:
        await call(app, {"operation": "status", "job_id": "fixture"})
    assert "fixture-sensitive-debug-detail" not in str(failure.value)
