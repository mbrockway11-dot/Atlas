"""Research Variant Implementation Planner v1 orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.variant_implementation_planner.artifacts import (
    build_acceptance_criteria,
    build_engineering_backlog,
    build_rollback_plan,
    build_target_files,
    build_test_plan,
)
from atlas.investment.variant_implementation_planner.builder import (
    build_implementation_plans,
)
from atlas.investment.variant_implementation_planner.config import (
    ACCEPTANCE_CSV,
    ENGINEERING_BACKLOG_CSV,
    FILE_PLAN_CSV,
    OUTPUT_DIR,
    PLANS_CSV,
    REPORT_JSON,
    REPORT_MD,
    ROLLBACK_CSV,
    SCHEMA_VERSION,
    SPECIFICATIONS_JSONL,
    TEST_PLAN_CSV,
    VERSION,
)
from atlas.investment.variant_implementation_planner.loader import (
    load_implementation_planner_inputs,
    safe_read_csv,
)
from atlas.investment.variant_implementation_planner.storage import (
    merge_plans,
    write_jsonl,
)


CONFLICTS_CSV = (
    OUTPUT_DIR
    / "variant_implementation_conflicts.csv"
)


def build_variant_implementation_planner_report() -> dict[str, Any]:
    """Build non-executable engineering plans for approved variants."""
    inputs = (
        load_implementation_planner_inputs()
    )

    incoming = build_implementation_plans(
        inputs["implementation_queue"],
        inputs["decision_ledger"],
        inputs["variant_registry"],
    )

    existing = safe_read_csv(
        PLANS_CSV
    )

    plans, conflicts, merge_stats = (
        merge_plans(
            existing,
            incoming,
        )
    )

    target_files = build_target_files(
        plans
    )

    tests = build_test_plan(
        plans
    )

    criteria = build_acceptance_criteria(
        plans
    )

    rollback = build_rollback_plan(
        plans
    )

    backlog = build_engineering_backlog(
        plans
    )

    report = {
        "success": bool(
            not plans.empty
            and conflicts.empty
        ),
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Research Variant Implementation Planner v1 "
            f"contains {len(plans)} implementation plan(s), "
            f"{len(target_files)} target-file instruction(s), "
            f"{len(tests)} required test(s), and "
            f"{len(conflicts)} immutable specification conflict(s)."
        ),
        "counts": {
            "plans": int(
                len(plans)
            ),
            "target_files": int(
                len(target_files)
            ),
            "tests": int(
                len(tests)
            ),
            "acceptance_criteria": int(
                len(criteria)
            ),
            "rollback_steps": int(
                len(rollback)
            ),
            "engineering_backlog": int(
                len(backlog)
            ),
            **merge_stats,
        },
        "plans": plans.to_dict(
            orient="records"
        ),
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "creates_engine_code": False,
            "changes_parent_engine": False,
            "changes_engine_registry": False,
            "changes_production_registry": False,
            "implementation_authorized": False,
            "production_activation": False,
            "manual_engineering_required": True,
            "manual_post_implementation_review_required": True,
            "immutable_plan_specifications": True,
            "deterministic_given_inputs": True,
        },
        "outputs": {
            "plans_csv": str(
                PLANS_CSV
            ),
            "target_files_csv": str(
                FILE_PLAN_CSV
            ),
            "test_plan_csv": str(
                TEST_PLAN_CSV
            ),
            "acceptance_csv": str(
                ACCEPTANCE_CSV
            ),
            "rollback_csv": str(
                ROLLBACK_CSV
            ),
            "engineering_backlog_csv": str(
                ENGINEERING_BACKLOG_CSV
            ),
            "specifications_jsonl": str(
                SPECIFICATIONS_JSONL
            ),
            "conflicts_csv": str(
                CONFLICTS_CSV
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    write_outputs(
        report=report,
        plans=plans,
        target_files=target_files,
        tests=tests,
        criteria=criteria,
        rollback=rollback,
        backlog=backlog,
        conflicts=conflicts,
    )

    return report


def write_outputs(
    *,
    report: dict,
    plans: pd.DataFrame,
    target_files: pd.DataFrame,
    tests: pd.DataFrame,
    criteria: pd.DataFrame,
    rollback: pd.DataFrame,
    backlog: pd.DataFrame,
    conflicts: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    plans.to_csv(
        PLANS_CSV,
        index=False,
    )

    target_files.to_csv(
        FILE_PLAN_CSV,
        index=False,
    )

    tests.to_csv(
        TEST_PLAN_CSV,
        index=False,
    )

    criteria.to_csv(
        ACCEPTANCE_CSV,
        index=False,
    )

    rollback.to_csv(
        ROLLBACK_CSV,
        index=False,
    )

    backlog.to_csv(
        ENGINEERING_BACKLOG_CSV,
        index=False,
    )

    conflicts.to_csv(
        CONFLICTS_CSV,
        index=False,
    )

    write_jsonl(
        plans,
        SPECIFICATIONS_JSONL,
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        build_markdown(
            report
        ),
        encoding="utf-8",
    )


def build_markdown(
    report: dict,
) -> str:
    lines = [
        "# Research Variant Implementation Planner v1",
        "",
        report["summary"],
        "",
        "## Plans",
        "",
    ]

    for plan in report.get(
        "plans",
        [],
    ):
        lines.extend([
            (
                f"### {plan.get('plan_id')} - "
                f"{plan.get('variant_name')}"
            ),
            "",
            (
                f"- Variant: "
                f"`{plan.get('variant_id')}`"
            ),
            (
                f"- Parent engine: "
                f"`{plan.get('parent_engine_id')}`"
            ),
            (
                f"- Gate: "
                f"`{plan.get('gate_expression')}`"
            ),
            (
                f"- Parent file: "
                f"`{plan.get('parent_engine_file')}`"
            ),
            (
                f"- Variant file: "
                f"`{plan.get('variant_module_file')}`"
            ),
            (
                f"- Test file: "
                f"`{plan.get('variant_test_file')}`"
            ),
            (
                f"- Status: "
                f"`{plan.get('plan_status')}`"
            ),
            (
                f"- Implementation authorized: "
                f"`{plan.get('implementation_authorized')}`"
            ),
            (
                f"- Production eligible: "
                f"`{plan.get('production_eligible')}`"
            ),
            "",
        ])

    lines.extend([
        "## Contract",
        "",
        "```json",
        json.dumps(
            report["contract"],
            indent=2,
        ),
        "```",
        "",
    ])

    return "\n".join(lines)
