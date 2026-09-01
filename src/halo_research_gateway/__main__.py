"""Run the single-worker loopback Halo Research Gateway service."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from .app import create_application
from .config import ROOT, GatewayConfig
from .windows_job import contain_current_process


def main() -> None:
    contain_current_process()
    config_path = Path(os.environ.get("HALO_RESEARCH_CONFIG", ROOT / "config.toml"))
    config = GatewayConfig.load(config_path if config_path.exists() else None)
    app = create_application(config)
    uvicorn.run(
        app, host="127.0.0.1", port=config.server.port, log_level=config.server.log_level.value.lower(), workers=1
    )


if __name__ == "__main__":
    main()
