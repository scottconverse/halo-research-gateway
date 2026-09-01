from halo_research_gateway import __version__


def test_package_imports():
    """Test that the package imports correctly"""
    import halo_research_gateway

    assert halo_research_gateway.__version__ == "0.1.0"


def test_application_has_mcp_and_operator_routes(tmp_path):
    """The package entrypoint now serves the real MCP/health/operator app."""
    from halo_research_gateway.app import create_application
    from halo_research_gateway.config import GatewayConfig

    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    app = create_application(config)
    paths = {getattr(route, "path", None) for route in app.routes}
    assert {
        "/mcp",
        "/health",
        "/stats",
        "/operator",
        "/operator/api/oauth",
        "/operator/api/imports/chrome",
        "/operator/api/imports/chrome/{plan_id:str}/execute",
    } <= paths


def test_version_matches_pyproject():
    """Test that the version in __init__.py matches pyproject.toml"""
    assert __version__ == "0.1.0"


async def _job_owner_for_header(tmp_path, header):
    from types import SimpleNamespace

    from mcp.server.mcpserver import Context

    from halo_research_gateway.app import create_application
    from halo_research_gateway.config import GatewayConfig, OutputProfile

    config = GatewayConfig()
    config.storage.database = str(tmp_path / "gateway.db")
    config.storage.backup_directory = str(tmp_path / "backups")
    config.storage.content_directory = str(tmp_path / "content")
    config.output.profiles["known-planner"] = OutputProfile()
    app = create_application(config)

    async def capture_owner(operation, owner, job_id, question, profile, limits):
        return {"owner": owner}

    app.state.halo_service.research_job = capture_owner
    request_context = SimpleNamespace(request=SimpleNamespace(headers={"X-Halo-Client": header}))
    context = Context(request_context=request_context, mcp_server=app.state.mcp_server)
    try:
        return await app.state.mcp_server._tool_manager.call_tool("research_job", {"operation": "status"}, context)
    finally:
        await app.state.halo_service.close()


async def test_configured_request_header_owns_research_job(tmp_path):
    result = await _job_owner_for_header(tmp_path, "known-planner")
    assert result["owner"] == "known-planner"


async def test_unknown_request_header_uses_shared_unidentified_owner(tmp_path):
    result = await _job_owner_for_header(tmp_path, "attacker-chosen-bucket")
    assert result["owner"] == "unidentified"
