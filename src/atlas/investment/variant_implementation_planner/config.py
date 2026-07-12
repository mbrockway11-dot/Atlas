"""Research Variant Implementation Planner v1 configuration."""

from __future__ import annotations

from pathlib import Path


VERSION = "research_variant_implementation_planner_v1"
SCHEMA_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_variant_implementation_planner"
)

PLANS_CSV = (
    OUTPUT_DIR
    / "variant_implementation_plans.csv"
)

FILE_PLAN_CSV = (
    OUTPUT_DIR
    / "variant_target_files.csv"
)

TEST_PLAN_CSV = (
    OUTPUT_DIR
    / "variant_test_plan.csv"
)

ACCEPTANCE_CSV = (
    OUTPUT_DIR
    / "variant_acceptance_criteria.csv"
)

ROLLBACK_CSV = (
    OUTPUT_DIR
    / "variant_rollback_plan.csv"
)

ENGINEERING_BACKLOG_CSV = (
    OUTPUT_DIR
    / "variant_engineering_backlog.csv"
)

SPECIFICATIONS_JSONL = (
    OUTPUT_DIR
    / "variant_implementation_specifications.jsonl"
)

REPORT_JSON = (
    OUTPUT_DIR
    / "variant_implementation_planner_report.json"
)

REPORT_MD = (
    OUTPUT_DIR
    / "variant_implementation_planner_report.md"
)

ALLOWED_PLAN_STATUSES = {
    "PLANNED",
    "READY_FOR_ENGINEERING",
    "IN_PROGRESS",
    "IMPLEMENTED_RESEARCH_ONLY",
    "VALIDATING_IMPLEMENTATION",
    "BLOCKED",
    "RETIRED",
}

DEFAULT_PLAN_STATUS = "PLANNED"

SOURCE = VERSION
