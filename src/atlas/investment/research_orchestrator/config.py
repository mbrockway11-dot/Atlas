"""Continuous Research Orchestrator v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "continuous_research_orchestrator_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_research_orchestrator"
)

LOG_DIR = OUTPUT_DIR / "logs"

EXECUTION_PLAN_CSV = (
    OUTPUT_DIR
    / "execution_plan.csv"
)

EXECUTED_JOBS_CSV = (
    OUTPUT_DIR
    / "executed_jobs.csv"
)

SKIPPED_JOBS_CSV = (
    OUTPUT_DIR
    / "skipped_jobs.csv"
)

BLOCKED_JOBS_CSV = (
    OUTPUT_DIR
    / "blocked_jobs.csv"
)

FAILED_JOBS_CSV = (
    OUTPUT_DIR
    / "failed_jobs.csv"
)

EXECUTION_TIMELINE_CSV = (
    OUTPUT_DIR
    / "execution_timeline.csv"
)

EXECUTION_GRAPH_CSV = (
    OUTPUT_DIR
    / "execution_graph.csv"
)

RUN_HISTORY_CSV = (
    OUTPUT_DIR
    / "orchestrator_run_history.csv"
)

EXECUTION_STATE_JSON = (
    OUTPUT_DIR
    / "execution_state.json"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "execution_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "execution_report.md"
)

DEFAULT_TIMEOUT_SECONDS = 1800
DEFAULT_MAX_JOBS = 100
DEFAULT_MAX_RECOVERY_ATTEMPTS = 2

ALLOWED_PLANNED_STATUSES = {
    "READY",
}

TERMINAL_JOB_STATUSES = {
    "SUCCEEDED",
    "FAILED",
    "TIMED_OUT",
    "SKIPPED",
    "BLOCKED",
    "DRY_RUN",
}


BUILD_CACHE_JSON = (
    OUTPUT_DIR
    / "build_cache.json"
)
