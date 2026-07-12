"""Manual Variant Decision Ledger v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "manual_variant_decision_ledger_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_variant_decisions"
)

LEDGER_CSV = (
    OUTPUT_DIR
    / "variant_decision_ledger.csv"
)

DECISION_HISTORY_CSV = (
    OUTPUT_DIR
    / "decision_history.csv"
)

APPROVED_CSV = (
    OUTPUT_DIR
    / "approved_variants.csv"
)

REJECTED_CSV = (
    OUTPUT_DIR
    / "rejected_variants.csv"
)

ARCHIVED_CSV = (
    OUTPUT_DIR
    / "archived_variants.csv"
)

DEFERRED_CSV = (
    OUTPUT_DIR
    / "deferred_variants.csv"
)

REVISIT_CSV = (
    OUTPUT_DIR
    / "revisit_later_variants.csv"
)

IMPLEMENTATION_QUEUE_CSV = (
    OUTPUT_DIR
    / "implementation_queue.csv"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "variant_decision_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "variant_decision_report.md"
)

ALLOWED_MANUAL_DECISIONS = {
    "PENDING",
    "APPROVED",
    "REJECTED",
    "ARCHIVED",
    "DEFERRED",
    "REVISIT_LATER",
}

ALLOWED_IMPLEMENTATION_STATUSES = {
    "NOT_IMPLEMENTED",
    "QUEUED",
    "IN_PROGRESS",
    "IMPLEMENTED_RESEARCH_ONLY",
    "VALIDATING_IMPLEMENTATION",
    "RETIRED",
}

DEFAULT_MANUAL_DECISION = "PENDING"
DEFAULT_IMPLEMENTATION_STATUS = "NOT_IMPLEMENTED"

SOURCE = VERSION
