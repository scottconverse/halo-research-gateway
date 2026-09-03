"""Strict runtime configuration. Network safety invariants are not switches."""

from __future__ import annotations

import tomllib
from enum import StrEnum
from pathlib import Path
from typing import Literal

from platformdirs import user_data_path
from pydantic import BaseModel, ConfigDict, Field, model_validator

ROOT = Path(user_data_path("HaloResearchGateway", appauthor=False))
BANNED_KEYS = {
    "host",
    "bind",
    "allow_private_networks",
    "allowed_schemes",
    "allowed_ports",
    "require_dns_pinning",
    "trust_environment_proxies",
    "cache_sensitive_urls",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ServerConfig(StrictModel):
    port: int = Field(8765, ge=1024, le=65535)
    mcp_path: str = "/mcp"
    health_path: str = "/health"
    log_level: LogLevel = LogLevel.INFO


class StorageConfig(StrictModel):
    database: str = str(ROOT / "state" / "gateway.db")
    cache_max_bytes: int = Field(1_073_741_824, ge=1)
    entry_max_bytes: int = Field(5_242_880, ge=1)
    inline_payload_max_bytes: int = 262_144
    content_directory: str = str(ROOT / "state" / "content" / "sha256")
    backup_directory: str = str(ROOT / "state" / "backups")


class QueueConfig(StrictModel):
    exa_max_pending: int = 20
    http_max_pending: int = 50
    reddit_max_pending: int = 12
    crawl_max_pending: int = 4
    default_per_client_pending: int = 4


class OutputProfile(StrictModel):
    default_chars: int = Field(6000, ge=1000, le=30000)
    ceiling_chars: int = Field(6000, ge=1000, le=30000)
    evidence_sha256: str = "unverified"

    @model_validator(mode="after")
    def default_below_ceiling(self):
        if self.default_chars > self.ceiling_chars:
            raise ValueError("profile default exceeds ceiling")
        return self


class OutputConfig(StrictModel):
    unidentified_default_chars: int = 6000
    unidentified_ceiling_chars: int = 6000
    cursor_ttl_seconds: int = Field(3600, ge=1, le=86400)
    snapshot_max_entries: int = Field(128, ge=1, le=4096)
    snapshot_max_bytes: int = Field(67_108_864, ge=1, le=1_073_741_824)
    profiles: dict[str, OutputProfile] = {}


class HttpConfig(StrictModel):
    global_concurrency: int = 4
    per_origin_concurrency: int = 1
    per_origin_interval_seconds: float = 1.0
    connect_timeout_seconds: float = 10
    total_timeout_seconds: float = 30
    max_redirects: int = 5
    max_compressed_bytes: int = 10_485_760
    max_decompressed_bytes: int = 20_971_520


class RedditConfig(StrictModel):
    base_url: str = "https://www.reddit.com"
    min_interval_seconds: float = Field(8.0, ge=8.0)
    rate_limit_backoff_seconds: int = 60
    max_consecutive_429: int = 3
    circuit_cooldown_seconds: int = 1800


class ExaConfig(StrictModel):
    url: str = "https://mcp.exa.ai/mcp?tools=web_search_exa,web_fetch_exa"
    anonymous: bool = True
    min_interval_seconds: float = Field(1.0, ge=1.0)
    daily_soft_limit: int = Field(45, ge=1, le=500)


class CrawlConfig(StrictModel):
    enabled: bool = True
    gate_evidence_sha256: str = "development-unverified"
    concurrency: int = Field(1, ge=1, le=2)
    page_timeout_seconds: int = 45
    job_timeout_seconds: int = 120
    max_pages: int = 25
    max_depth: int = 3
    base_directory: str = str(ROOT / "browser")


class LocalTargetConfig(StrictModel):
    scheme: Literal["http", "https"]
    host: str
    port: int = Field(ge=1, le=65535)
    path_prefixes: list[str]
    methods: list[Literal["GET", "HEAD"]] = ["GET", "HEAD"]
    browser_allowed: bool = False
    cache_authenticated: bool = False


class ImportConfig(StrictModel):
    approval_ttl_seconds: int = Field(300, ge=30, le=3600)


class JobConfig(StrictModel):
    max_active: int = Field(2, ge=1, le=8)
    default_timeout_seconds: int = 1800
    absolute_timeout_seconds: int = 21600
    absolute_pages: int = 5000
    lease_seconds: int = 30


class OptionalProviderConfig(StrictModel):
    """Operator-owned paid-provider policy; disabled until explicitly configured."""

    enabled: bool = False
    provider: str | None = None
    connection_id: str | None = None
    allowed_domains: list[str] = Field(default_factory=list)
    daily_attempt_limit: int = Field(0, ge=0, le=10000)
    daily_spend_limit_usd: float = Field(0, ge=0, le=10000)

    @model_validator(mode="after")
    def enabled_provider_is_complete(self):
        if self.enabled and (
            not self.provider
            or not self.connection_id
            or not self.allowed_domains
            or self.daily_attempt_limit < 1
            or self.daily_spend_limit_usd <= 0
        ):
            raise ValueError(
                "enabled optional provider requires provider, connection_id, allowed_domains, "
                "daily_attempt_limit, and daily_spend_limit_usd"
            )
        return self


class GatewayConfig(StrictModel):
    server: ServerConfig = ServerConfig()
    storage: StorageConfig = StorageConfig()
    output: OutputConfig = OutputConfig()
    queues: QueueConfig = QueueConfig()
    http: HttpConfig = HttpConfig()
    reddit: RedditConfig = RedditConfig()
    exa: ExaConfig = ExaConfig()
    crawl: CrawlConfig = CrawlConfig()
    local_targets: dict[str, LocalTargetConfig] = {}
    imports: ImportConfig = ImportConfig()
    jobs: JobConfig = JobConfig()
    captcha: OptionalProviderConfig = OptionalProviderConfig()
    proxy: OptionalProviderConfig = OptionalProviderConfig()

    @classmethod
    def load(cls, path: str | Path | None = None) -> GatewayConfig:
        if path is None:
            return cls()
        try:
            with Path(path).open("rb") as stream:
                data = tomllib.load(stream)
            _reject_banned(data)
            # Legacy action settings cannot enable a removed feature. Keep old
            # installs startable without modifying their operator-owned config.
            data.pop("actions", None)
            known = set(cls.model_fields)
            unknown = set(data) - known
            if unknown:
                raise ConfigError(f"Unknown configuration key: {sorted(unknown)[0]}")
            return cls.model_validate(data)
        except Exception as exc:
            if isinstance(exc, ConfigError):
                raise
            raise ConfigError(f"Configuration error: {exc}") from exc

    def ensure_directories(self) -> None:
        paths = [
            Path(self.storage.database).parent,
            Path(self.storage.content_directory),
            Path(self.storage.backup_directory),
            ROOT / "logs",
            ROOT / "state" / "jobs",
            ROOT / "state" / "receipts",
            ROOT / "vault",
            ROOT / "browser" / "profiles",
            ROOT / "run",
        ]
        for path in paths:
            path.mkdir(parents=True, exist_ok=True)


class ConfigError(ValueError):
    pass


def _reject_banned(value: object, prefix: str = "") -> None:
    if not isinstance(value, dict):
        return
    for key, nested in value.items():
        path = f"{prefix}.{key}" if prefix else key
        # Exact local-target records intentionally contain host identity. The
        # forbidden keys apply to public/global policy, never this named seam.
        local_target_field = prefix.startswith("local_targets.")
        if key.lower() in BANNED_KEYS and not local_target_field:
            raise ConfigError(f"Configuration contains banned keys: {path}")
        _reject_banned(nested, path)
