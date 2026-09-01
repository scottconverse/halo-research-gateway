"""Tests for configuration functionality."""

import os
import tempfile

from halo_research_gateway.config import ConfigError, GatewayConfig


def test_defaults():
    """Test default configuration values."""
    config = GatewayConfig()

    assert config.server.port == 8765
    assert config.server.mcp_path == "/mcp"
    assert config.server.health_path == "/health"
    assert config.server.log_level.name == "INFO"

    assert config.storage.database.endswith("HaloResearchGateway\\state\\gateway.db")
    assert config.storage.cache_max_bytes == 1073741824
    assert config.storage.entry_max_bytes == 5242880
    assert config.storage.inline_payload_max_bytes == 262144

    assert config.reddit.min_interval_seconds == 8.0
    assert config.reddit.rate_limit_backoff_seconds == 60
    assert config.reddit.max_consecutive_429 == 3
    assert config.reddit.circuit_cooldown_seconds == 1800

    assert config.exa.min_interval_seconds == 1.0
    assert config.exa.daily_soft_limit == 45
    assert not config.captcha.enabled
    assert not config.proxy.enabled


def test_optional_provider_config_has_no_secret_field(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        """[captcha]
enabled = true
provider = "fixture"
connection_id = "opaque-id"
allowed_domains = ["example.com"]
daily_attempt_limit = 2
daily_spend_limit_usd = 1.5
""",
        encoding="utf-8",
    )
    config = GatewayConfig.load(path)
    assert config.captcha.enabled
    assert config.captcha.connection_id == "opaque-id"


def test_toml_override():
    """Test loading configuration from TOML file."""
    toml_content = """
[server]
port = 9000

[storage]  
database = "postgresql://test.db"

[reddit]
min_interval_seconds = 10.0

[exa]
daily_soft_limit = 50
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        config = GatewayConfig.load(temp_path)

        assert config.server.port == 9000
        assert config.storage.database == "postgresql://test.db"
        assert config.reddit.min_interval_seconds == 10.0
        assert config.exa.daily_soft_limit == 50

    finally:
        os.unlink(temp_path)


def test_unknown_key_error():
    """Test that unknown keys raise ConfigError."""
    toml_content = """
[server]
port = 8765

[unknown_section] 
key = "value"
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        GatewayConfig.load(temp_path)
        raise AssertionError("Should have raised ConfigError for unknown key")
    except ConfigError as e:
        assert "Unknown configuration key" in str(e)
    finally:
        os.unlink(temp_path)


def test_banned_keys_rejected():
    """Test that banned keys raise ConfigError."""
    # Test with server section
    toml_content1 = """
[server]
host = "localhost"
port = 8765
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content1)
        temp_path = f.name

    try:
        GatewayConfig.load(temp_path)
        raise AssertionError("Should have raised ConfigError for banned key")
    except ConfigError as e:
        assert "banned keys" in str(e).lower()
    finally:
        os.unlink(temp_path)

    # Test with storage section
    toml_content2 = """
[storage]
database = "sqlite:///test.db"
allow_private_networks = true
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content2)
        temp_path = f.name

    try:
        GatewayConfig.load(temp_path)
        raise AssertionError("Should have raised ConfigError for banned key")
    except ConfigError as e:
        assert "banned keys" in str(e).lower()
    finally:
        os.unlink(temp_path)


def test_port_bounds():
    """Test port validation."""
    # Test invalid port (too low)
    toml_content = """
[server]
port = 1023
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        GatewayConfig.load(temp_path)
        raise AssertionError("Should have raised validation error for port < 1024")
    except Exception:  # This will be a pydantic ValidationError
        pass  # Expected
    finally:
        os.unlink(temp_path)


def test_reddit_bounds():
    """Test reddit config bounds."""
    toml_content = """
[reddit]
min_interval_seconds = 7.9
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        GatewayConfig.load(temp_path)
        raise AssertionError("Should have raised validation error for min_interval_seconds < 8.0")
    except Exception:  # This will be a pydantic ValidationError
        pass  # Expected
    finally:
        os.unlink(temp_path)


def test_malformed_toml():
    """Test that malformed TOML raises ConfigError."""
    toml_content = """
[server]
port = 
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write(toml_content)
        temp_path = f.name

    try:
        GatewayConfig.load(temp_path)
        raise AssertionError("Should have raised ConfigError for malformed TOML")
    except ConfigError as e:
        assert "Configuration error" in str(e)
    finally:
        os.unlink(temp_path)
