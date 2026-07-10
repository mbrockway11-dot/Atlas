
"""Market Universe v1 configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.common.io import safe_read_json


DEFAULT_CONFIG_PATH = Path(
    "config/investment/market_universe.json"
)


def load_market_universe_config(
    path: str | Path = DEFAULT_CONFIG_PATH,
) -> dict[str, Any]:
    config = safe_read_json(Path(path))

    if not config:
        raise FileNotFoundError(
            f"Market Universe config was not found: {path}"
        )

    return config


def enabled_assets(config: dict) -> list[str]:
    return [
        str(row.get("asset"))
        for row in config.get("whitelist", [])
        if row.get("enabled") is True
        and row.get("asset")
    ]


def metadata_by_asset(config: dict) -> dict[str, dict]:
    return {
        str(row.get("asset")): dict(row)
        for row in config.get("whitelist", [])
        if row.get("asset")
    }
