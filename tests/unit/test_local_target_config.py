from halo_research_gateway.config import GatewayConfig


def test_named_local_target_may_define_exact_host(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        """
[local_targets.mission_control]
scheme = "http"
host = "127.0.0.1"
port = 3090
path_prefixes = ["/"]
""",
        encoding="utf-8",
    )
    config = GatewayConfig.load(path)
    assert config.local_targets["mission_control"].host == "127.0.0.1"
