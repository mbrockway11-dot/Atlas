"""Historical Governance Snapshots v1 configuration."""

from __future__ import annotations

from pathlib import Path


OUTPUT_DIR = Path(
    "output/investment_governance_snapshots"
)

ENGINE_SNAPSHOTS_CSV = (
    OUTPUT_DIR
    / "engine_governance_snapshots.csv"
)

CONTEXT_SNAPSHOTS_CSV = (
    OUTPUT_DIR
    / "market_context_snapshots.csv"
)

MANIFEST_CSV = (
    OUTPUT_DIR
    / "governance_snapshot_manifest.csv"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "governance_snapshots_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "governance_snapshots_report.md"
)

SCHEMA_VERSION = "1.0.0"
SOURCE = "historical_governance_snapshots_v1"
