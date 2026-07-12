"""Atlas Research Scheduler v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "atlas_research_scheduler_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_research_scheduler"
)

RESEARCH_SCHEDULE_CSV = (
    OUTPUT_DIR
    / "research_schedule.csv"
)

PENDING_JOBS_CSV = (
    OUTPUT_DIR
    / "pending_jobs.csv"
)

BLOCKED_JOBS_CSV = (
    OUTPUT_DIR
    / "blocked_jobs.csv"
)

COMPLETED_JOBS_CSV = (
    OUTPUT_DIR
    / "completed_jobs.csv"
)

FAILED_JOBS_CSV = (
    OUTPUT_DIR
    / "failed_jobs.csv"
)

ARTIFACT_FRESHNESS_CSV = (
    OUTPUT_DIR
    / "artifact_freshness.csv"
)

DEPENDENCY_GRAPH_CSV = (
    OUTPUT_DIR
    / "dependency_graph.csv"
)

RUN_HISTORY_CSV = (
    OUTPUT_DIR
    / "scheduler_run_history.csv"
)

SCHEDULER_STATE_JSON = (
    OUTPUT_DIR
    / "scheduler_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "scheduler_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "scheduler_report.md"
)

DEFAULT_STALE_AFTER_HOURS = 26.0
LONG_LIVED_STALE_AFTER_HOURS = 168.0

ALLOWED_JOB_STATUSES = {
    "CURRENT",
    "READY",
    "STALE",
    "MISSING",
    "BLOCKED",
    "FAILED",
    "DISABLED",
}

PRIORITY_ORDER = {
    "CRITICAL": 1,
    "HIGH": 2,
    "MEDIUM": 3,
    "LOW": 4,
}
