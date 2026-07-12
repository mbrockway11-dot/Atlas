"""Atlas State API v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_state_api_v1"
SCHEMA_VERSION = "1.0.0"

COMPILED_STATE_PATH = Path(
    "output/investment_atlas_compiler/"
    "atlas_compiled_state.json"
)

OUTPUT_DIR = Path(
    "output/investment_state_api"
)

VALIDATION_JSON = (
    OUTPUT_DIR
    / "state_api_validation.json"
)

VALIDATION_MD = (
    OUTPUT_DIR
    / "state_api_validation.md"
)

ALLOWED_SECTIONS = (
    "market_context",
    "alpha",
    "research",
    "ensemble",
    "learning",
    "governance",
    "variants",
    "portfolio",
)
