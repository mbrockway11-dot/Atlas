"""Validated Variant Registry v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "validated_variant_registry_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_validated_variants"
)

REGISTRY_CSV = (
    OUTPUT_DIR
    / "validated_variant_registry.csv"
)

SPECIFICATIONS_JSONL = (
    OUTPUT_DIR
    / "validated_variant_specifications.jsonl"
)

MANIFEST_CSV = (
    OUTPUT_DIR
    / "validated_variant_manifest.csv"
)

CONFLICTS_CSV = (
    OUTPUT_DIR
    / "validated_variant_conflicts.csv"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "validated_variant_registry_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "validated_variant_registry_report.md"
)

SUPPORTED_HYPOTHESIS_TYPES = {
    "FAILURE_MODE_GATE",
    "CONDITIONAL_OPPORTUNITY",
}

VALID_DECISION = "VALIDATE"

RESEARCH_STATUS = "RESEARCH_VALIDATED"
REVIEW_STATUS = "PENDING_MANUAL_REVIEW"
IMPLEMENTATION_STATUS = "NOT_IMPLEMENTED"
PRODUCTION_STATUS = "NOT_PRODUCTION_ELIGIBLE"
