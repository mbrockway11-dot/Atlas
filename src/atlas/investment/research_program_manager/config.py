"""Atlas Research Program Manager v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_research_program_manager_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_research_program_manager"
)

REGISTRY_CSV = (
    OUTPUT_DIR
    / "research_program_registry.csv"
)

STATUS_HISTORY_CSV = (
    OUTPUT_DIR
    / "research_program_status_history.csv"
)

EVIDENCE_CSV = (
    OUTPUT_DIR
    / "research_program_evidence.csv"
)

DEPENDENCIES_CSV = (
    OUTPUT_DIR
    / "research_program_dependencies.csv"
)

APPROVAL_QUEUE_CSV = (
    OUTPUT_DIR
    / "research_program_approval_queue.csv"
)

ACTIVE_QUEUE_CSV = (
    OUTPUT_DIR
    / "research_program_active_queue.csv"
)

BLOCKED_QUEUE_CSV = (
    OUTPUT_DIR
    / "research_program_blocked_queue.csv"
)

PROMOTION_QUEUE_CSV = (
    OUTPUT_DIR
    / "research_program_promotion_queue.csv"
)

ARCHIVED_CSV = (
    OUTPUT_DIR
    / "research_program_archived.csv"
)

STATE_JSON = (
    OUTPUT_DIR
    / "research_program_manager_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "research_program_manager_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "research_program_manager_report.md"
)

SOURCE = VERSION

PROGRAM_STATUSES = {
    "PROPOSED",
    "APPROVED_FOR_DESIGN",
    "EXPERIMENT_DESIGNED",
    "VALIDATING",
    "EVIDENCE_ACCUMULATING",
    "PROMOTED",
    "DEFERRED",
    "REJECTED",
    "ARCHIVED",
}

ACTIVE_STATUSES = {
    "APPROVED_FOR_DESIGN",
    "EXPERIMENT_DESIGNED",
    "VALIDATING",
    "EVIDENCE_ACCUMULATING",
}

TERMINAL_STATUSES = {
    "PROMOTED",
    "REJECTED",
    "ARCHIVED",
}

ALLOWED_TRANSITIONS = {
    "PROPOSED": {
        "APPROVED_FOR_DESIGN",
        "DEFERRED",
        "REJECTED",
        "ARCHIVED",
    },
    "APPROVED_FOR_DESIGN": {
        "EXPERIMENT_DESIGNED",
        "DEFERRED",
        "REJECTED",
        "ARCHIVED",
    },
    "EXPERIMENT_DESIGNED": {
        "VALIDATING",
        "DEFERRED",
        "REJECTED",
        "ARCHIVED",
    },
    "VALIDATING": {
        "EVIDENCE_ACCUMULATING",
        "DEFERRED",
        "REJECTED",
        "ARCHIVED",
    },
    "EVIDENCE_ACCUMULATING": {
        "PROMOTED",
        "DEFERRED",
        "REJECTED",
        "ARCHIVED",
        "VALIDATING",
    },
    "DEFERRED": {
        "PROPOSED",
        "APPROVED_FOR_DESIGN",
        "REJECTED",
        "ARCHIVED",
    },
    "PROMOTED": {
        "ARCHIVED",
    },
    "REJECTED": {
        "ARCHIVED",
        "PROPOSED",
    },
    "ARCHIVED": set(),
}

DEFAULT_REVIEW_AFTER_DAYS = 30
STALE_ACTIVE_AFTER_DAYS = 45
PROMOTION_SCORE_THRESHOLD = 0.72
PROMOTION_CONFIDENCE_THRESHOLD = 0.65
