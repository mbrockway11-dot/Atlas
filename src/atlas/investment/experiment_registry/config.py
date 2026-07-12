"""Atlas Experiment Registry v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_experiment_registry_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_experiment_registry"
)

EXPERIMENTS_CSV = (
    OUTPUT_DIR
    / "experiment_registry.csv"
)

OBSERVATIONS_CSV = (
    OUTPUT_DIR
    / "experiment_observations.csv"
)

METRICS_CSV = (
    OUTPUT_DIR
    / "experiment_metrics.csv"
)

ARTIFACTS_CSV = (
    OUTPUT_DIR
    / "experiment_artifacts.csv"
)

RELATIONSHIPS_CSV = (
    OUTPUT_DIR
    / "experiment_relationships.csv"
)

STATUS_HISTORY_CSV = (
    OUTPUT_DIR
    / "experiment_status_history.csv"
)

ORCHESTRATOR_RUNS_CSV = (
    OUTPUT_DIR
    / "experiment_orchestrator_runs.csv"
)

STATE_JSON = (
    OUTPUT_DIR
    / "experiment_registry_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "experiment_registry_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "experiment_registry_report.md"
)

ALLOWED_EXPERIMENT_TYPES = {
    "HYPOTHESIS",
    "VALIDATED_VARIANT",
    "PORTFOLIO_EXPERIMENT",
    "RESEARCH_CYCLE",
}

ALLOWED_STATUSES = {
    "PROPOSED",
    "VALIDATING",
    "VALIDATED",
    "REJECTED",
    "APPROVED",
    "DEFERRED",
    "ARCHIVED",
    "PLANNED",
    "IMPLEMENTED_RESEARCH_ONLY",
    "FAILED",
    "COMPLETED",
}

SOURCE = VERSION
