"""Configuration for Halo Research Gateway."""

import tomllib
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict, BaseSettings
from enum import Enum


class LogLevel(str, Enum):
    """Logging level options."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ServerConfig(BaseModel):
    """Server configuration section."""
    port: int = Field(8765, ge=1024, le=65535)
    mcp_path: str = "/mcp"
    health_path: str = "/health"
    log_level: LogLevel = LogLevel.INFO


class StorageConfig(BaseModel):
    """Storage configuration section."""
    database: str
    cache_max_bytes: int = 1073741824  # 1 GiB
    entry_max_bytes: int = 5242880  # 5 MiB
    inline_payload_max_bytes: int = 262144  # 256 KiB


class RedditConfig(BaseModel):
    """Reddit configuration section."""
    min_interval_seconds: float = Field(8.0, ge=8.0)
    rate_limit_backoff_seconds: int = 60
    max_consecutive_429: int = 3
    circuit_cooldown_seconds: int = 1800


class ExaConfig(BaseModel):
    """Exa configuration section."""
    min_interval_seconds: float = Field(1.0, ge=1.0)
    daily_soft_limit: int = Field(45, ge=1, le=500)


# Define banned keys for validation
BANNED_KEYS = {
    "host", "bind", "allow_private_networks", "allowed_schemes",
    "allowed_ports", "require_dns_pinning", "trust_environment_proxies",
    "cache_sensitive_urls", "respect_robots"
}


class GatewayConfig(BaseSettings):
    """Main gateway configuration."""

    # Configuration sections
    server: ServerConfig = ServerConfig()
    storage: StorageConfig = StorageConfig(database="sqlite:///default.db")
    reddit: RedditConfig = RedditConfig()
    exa: ExaConfig = ExaConfig()

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra='forbid'  # This will cause validation errors for unknown keys
    )

    @classmethod
    def load(cls, path: Optional[str] = None) -> 'GatewayConfig':
        """Load configuration from TOML file."""
        try:
            if path is None:
                # Return defaults when no config provided
                return cls()
            
            with open(path, "rb") as f:
                data = tomllib.load(f)
                
            # Validate that all keys are known (fail closed on unknown keys) 
            allowed_keys = {"server", "storage", "reddit", "exa"}
            for key in data.keys():
                if key not in allowed_keys:
                    raise ValueError(f"Unknown configuration key: {key}")
            
            # Validate banned keys at each section level
            for section_name, section_data in data.items():
                if isinstance(section_data, dict):
                    banned_found = set()
                    for key in section_data.keys():
                        if key.lower() in BANNED_KEYS:
                            banned_found.add(key)
                    
                    if banned_found:
                        raise ValueError(f"Configuration contains banned keys: {banned_found}")
            
            return cls(**data)
        except Exception as e:
            raise ConfigError(f"Configuration error: {str(e)}")


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass
