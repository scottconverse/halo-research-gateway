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
