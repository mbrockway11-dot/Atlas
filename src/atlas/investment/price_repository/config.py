
"""Price Repository configuration."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.common.io import safe_read_json


DEFAULT_CONFIG = Path(
    "config/investment/price_repository.json"
)


def load_price_repository_config(
    path: str | Path = DEFAULT_CONFIG,
) -> dict[str, Any]:
    config = safe_read_json(Path(path))

    if not config:
        raise FileNotFoundError(
            f"Price Repository config unavailable: {path}"
        )

    return config
