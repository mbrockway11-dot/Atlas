"""Atlas Compiler v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_compiler_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_atlas_compiler"
)

COMPILED_STATE_JSON = (
    OUTPUT_DIR
    / "atlas_compiled_state.json"
)

COMPILED_STATE_MD = (
    OUTPUT_DIR
    / "atlas_compiled_state.md"
)

COMPONENT_INVENTORY_CSV = (
    OUTPUT_DIR
    / "atlas_component_inventory.csv"
)

COMPONENT_VALIDATION_CSV = (
    OUTPUT_DIR
    / "atlas_component_validation.csv"
)

STATE_MANIFEST_CSV = (
    OUTPUT_DIR
    / "atlas_state_manifest.csv"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "atlas_compiler_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "atlas_compiler_report.md"
)

SOURCE = VERSION
