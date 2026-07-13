"""Deterministic remediation planning for the Atlas Control Plane.

The planner consumes the read-only E.1 system-health snapshot and canonical
research DAG. It does not execute jobs, mutate artifacts, or own dependencies.

Its responsibilities are:

- normalize control-plane recommendations;
- identify executable canonical job targets;
- expand blocked jobs to their root dependencies;
- remove duplicate work;
- order jobs using the canonical topological order;
- distinguish executable, manual, informational, and blocked actions;
- produce one operator-reviewable remediation plan.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd

from atlas.investment.control_plane import (
    build_system_health,
)
from atlas.investment.research_scheduler import (
    JOB_MAP,
    topological_order,
)


REMEDIATION_PLAN_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/atlas_control_plane"
)

REMEDIATION_PLAN_JSON = (
    OUTPUT_DIR
    / "remediation_plan.json"
)

REMEDIATION_PLAN_CSV = (
    OUTPUT_DIR
    / "remediation_plan.csv"
)

REMEDIATION_PLAN_MD = (
    OUTPUT_DIR
    / "remediation_plan.md"
)


EXECUTABLE_ACTION_TYPES = {
    "REBUILD_REQUIRED_OUTPUTS",
    "RESTORE_REQUIRED_INPUTS",
    "EXECUTE_READY_JOB",
    "RESOLVE_BLOCKING_DEPENDENCIES",
}

MANUAL_ACTION_TYPES = {
    "REPAIR_STRUCTURAL_CONTRACT",
}

INFORMATIONAL_ACTION_TYPES = {
    "ESTABLISH_BUILD_CACHE",
    "NO_ACTION_REQUIRED",
}

SEVERITY_RANK = {
    "INFO": 1,
    "LOW": 2,
    "MEDIUM": 3,
    "HIGH": 4,
    "CRITICAL": 5,
}


def build_remediation_plan(
    health_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one deterministic operator-reviewable remediation plan."""
    health = dict(
        health_report
        if health_report is not None
        else build_system_health()
    )

    generated_at = datetime.now(
        UTC
    ).isoformat()

    recommendations = [
        dict(item)
        for item in health.get(
            "recommended_actions",
            [],
        )
        if isinstance(item, Mapping)
    ]

    execution_component = (
        health.get(
            "components",
            {},
        )
        or {}
    ).get(
        "execution",
        {},
    )

    manual_actions: list[
        dict[str, Any]
    ] = []

    informational_actions: list[
        dict[str, Any]
    ] = []

    candidate_jobs: set[str] = set()
    source_actions_by_job: dict[
        str,
        list[str],
    ] = {}
    source_severity_by_job: dict[
        str,
        str,
    ] = {}

    resume_action = find_action(
        recommendations,
        "RESUME_INTERRUPTED_CYCLE",
    )

    structural_actions = [
        item
        for item in recommendations
        if str(
            item.get(
                "action_type",
                "",
            )
        )
        in MANUAL_ACTION_TYPES
    ]

    structural_blocked = bool(
        structural_actions
    )

    for item in recommendations:
        action_type = str(
            item.get(
                "action_type",
                "",
            )
        )

        target = str(
            item.get(
                "target",
                "",
            )
        )

        if action_type in MANUAL_ACTION_TYPES:
            manual_actions.append(
                normalize_manual_action(
                    item
                )
            )
            continue

        if action_type in INFORMATIONAL_ACTION_TYPES:
            informational_actions.append(
                normalize_information_action(
                    item
                )
            )
            continue

        if action_type not in (
            EXECUTABLE_ACTION_TYPES
        ):
            manual_actions.append(
                normalize_unknown_action(
                    item
                )
            )
            continue

        if target not in JOB_MAP:
            manual_actions.append({
                "action_class": "manual",
                "severity": str(
                    item.get(
                        "severity",
                        "HIGH",
                    )
                ),
                "action_type": (
                    "RESOLVE_UNKNOWN_JOB_TARGET"
                ),
                "target": target,
                "reason": (
                    "Control-plane recommendation "
                    "references a noncanonical job."
                ),
                "recommended_command": "",
                "source_action_type": (
                    action_type
                ),
            })
            continue

        expanded_jobs = expand_job_repair_set(
            target
        )

        for job_id in expanded_jobs:
            candidate_jobs.add(job_id)

            source_actions_by_job.setdefault(
                job_id,
                [],
            ).append(
                action_type
            )

            source_severity_by_job[
                job_id
            ] = more_severe(
                source_severity_by_job.get(
                    job_id,
                    "INFO",
                ),
                str(
                    item.get(
                        "severity",
                        "MEDIUM",
                    )
                ),
            )

    ordered_jobs = [
        job_id
        for job_id in topological_order()
        if job_id in candidate_jobs
    ]

    execution_steps = build_execution_steps(
        ordered_jobs=ordered_jobs,
        source_actions_by_job=(
            source_actions_by_job
        ),
        source_severity_by_job=(
            source_severity_by_job
        ),
        structural_blocked=(
            structural_blocked
        ),
    )

    if resume_action:
        execution_mode = "RESUME"
        execution_command = (
            "python scripts/"
            "run_research_cycle.py "
            "--execute --resume"
        )
    elif execution_steps:
        execution_mode = "EXECUTE"
        execution_command = (
            "python scripts/"
            "run_research_cycle.py "
            "--execute"
        )
    else:
        execution_mode = "NONE"
        execution_command = ""

    if structural_blocked:
        executable = False
        blocked_reason = (
            "Structural architecture errors must "
            "be repaired before automated execution."
        )
    elif not execution_steps and not resume_action:
        executable = False
        blocked_reason = (
            "No executable remediation work "
            "is currently required."
        )
    else:
        executable = True
        blocked_reason = ""

    counts = {
        "source_recommendations": len(
            recommendations
        ),
        "execution_steps": len(
            execution_steps
        ),
        "manual_actions": len(
            manual_actions
        ),
        "informational_actions": len(
            informational_actions
        ),
        "deduplicated_job_targets": len(
            candidate_jobs
        ),
        "structural_blockers": len(
            structural_actions
        ),
    }

    plan_status = derive_plan_status(
        structural_blocked=(
            structural_blocked
        ),
        executable=executable,
        execution_steps=execution_steps,
        manual_actions=manual_actions,
    )

    return {
        "success": not structural_blocked,
        "version": (
            REMEDIATION_PLAN_VERSION
        ),
        "generated_at": generated_at,
        "source_health_status": str(
            health.get(
                "overall_status",
                "UNKNOWN",
            )
        ),
        "plan_status": plan_status,
        "summary": build_plan_summary(
            plan_status=plan_status,
            counts=counts,
            execution_mode=execution_mode,
        ),
        "execution": {
            "authorized": False,
            "executable": executable,
            "mode": execution_mode,
            "recommended_command": (
                execution_command
            ),
            "blocked_reason": (
                blocked_reason
            ),
            "resume_run_id": str(
                (
                    health.get(
                        "components",
                        {},
                    )
                    or {}
                ).get(
                    "execution",
                    {},
                ).get(
                    "metrics",
                    {},
                ).get(
                    "run_id",
                    "",
                )
            ),
        },
        "counts": counts,
        "execution_steps": (
            execution_steps
        ),
        "manual_actions": (
            sort_actions(
                manual_actions
            )
        ),
        "informational_actions": (
            sort_actions(
                informational_actions
            )
        ),
        "contract": {
            "read_only": True,
            "execution_authorized": False,
            "canonical_dag_only": True,
            "canonical_job_registry_only": True,
            "deduplicates_recommendations": True,
            "topologically_orders_jobs": True,
            "operator_approval_required": True,
        },
        "outputs": {
            "remediation_plan_json": str(
                REMEDIATION_PLAN_JSON
            ),
            "remediation_plan_csv": str(
                REMEDIATION_PLAN_CSV
            ),
            "remediation_plan_markdown": str(
                REMEDIATION_PLAN_MD
            ),
        },
    }


def expand_job_repair_set(
    job_id: str,
) -> set[str]:
    """Return the target plus every canonical upstream dependency."""
    if job_id not in JOB_MAP:
        return set()

    required: set[str] = {
        job_id
    }

    pending = list(
        JOB_MAP[job_id].dependencies
    )

    while pending:
        dependency_id = pending.pop()

        if dependency_id in required:
            continue

        if dependency_id not in JOB_MAP:
            continue

        required.add(
            dependency_id
        )

        pending.extend(
            JOB_MAP[
                dependency_id
            ].dependencies
        )

    return required


def build_execution_steps(
    *,
    ordered_jobs: Iterable[str],
    source_actions_by_job: Mapping[
        str,
        list[str],
    ],
    source_severity_by_job: Mapping[
        str,
        str,
    ],
    structural_blocked: bool,
) -> list[dict[str, Any]]:
    """Build topologically ordered execution steps."""
    steps: list[
        dict[str, Any]
    ] = []

    selected = list(
        ordered_jobs
    )
    selected_set = set(
        selected
    )

    for sequence, job_id in enumerate(
        selected,
        start=1,
    ):
        job = JOB_MAP[
            job_id
        ]

        prerequisite_jobs = [
            dependency_id
            for dependency_id
            in job.dependencies
            if dependency_id
            in selected_set
        ]

        steps.append({
            "step": sequence,
            "job_id": job_id,
            "title": str(
                job.title
            ),
            "category": str(
                job.category
            ),
            "severity": str(
                source_severity_by_job.get(
                    job_id,
                    "MEDIUM",
                )
            ),
            "priority": str(
                job.priority
            ),
            "dependencies": "|".join(
                job.dependencies
            ),
            "prerequisite_plan_jobs": (
                "|".join(
                    prerequisite_jobs
                )
            ),
            "source_action_types": (
                "|".join(
                    sorted(
                        set(
                            source_actions_by_job.get(
                                job_id,
                                [],
                            )
                        )
                    )
                )
            ),
            "command": str(
                job.command
            ),
            "output_path": str(
                job.output_path
            ),
            "execution_authorized": False,
            "blocked_by_structure": bool(
                structural_blocked
            ),
        })

    return steps


def find_action(
    actions: Iterable[
        Mapping[str, Any]
    ],
    action_type: str,
) -> dict[str, Any]:
    for item in actions:
        if str(
            item.get(
                "action_type",
                "",
            )
        ) == action_type:
            return dict(item)

    return {}


def normalize_manual_action(
    item: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "action_class": "manual",
        "severity": str(
            item.get(
                "severity",
                "HIGH",
            )
        ),
        "action_type": str(
            item.get(
                "action_type",
                "",
            )
        ),
        "target": str(
            item.get(
                "target",
                "",
            )
        ),
        "reason": str(
            item.get(
                "reason",
                "",
            )
        ),
        "recommended_command": str(
            item.get(
                "recommended_command",
                "",
            )
        ),
        "source_action_type": str(
            item.get(
                "action_type",
                "",
            )
        ),
    }


def normalize_information_action(
    item: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "action_class": "informational",
        "severity": str(
            item.get(
                "severity",
                "INFO",
            )
        ),
        "action_type": str(
            item.get(
                "action_type",
                "",
            )
        ),
        "target": str(
            item.get(
                "target",
                "",
            )
        ),
        "reason": str(
            item.get(
                "reason",
                "",
            )
        ),
        "recommended_command": str(
            item.get(
                "recommended_command",
                "",
            )
        ),
    }


def normalize_unknown_action(
    item: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = normalize_manual_action(
        item
    )
    normalized["action_type"] = (
        "REVIEW_UNKNOWN_ACTION"
    )
    normalized["source_action_type"] = str(
        item.get(
            "action_type",
            "",
        )
    )
    return normalized


def derive_plan_status(
    *,
    structural_blocked: bool,
    executable: bool,
    execution_steps: list[
        dict[str, Any]
    ],
    manual_actions: list[
        dict[str, Any]
    ],
) -> str:
    if structural_blocked:
        return "BLOCKED"

    if executable and execution_steps:
        return "READY"

    if manual_actions:
        return "MANUAL_REVIEW"

    return "NO_ACTION"


def build_plan_summary(
    *,
    plan_status: str,
    counts: Mapping[str, Any],
    execution_mode: str,
) -> str:
    return (
        "Atlas remediation planner produced "
        f"{counts['execution_steps']} ordered "
        "execution step(s), "
        f"{counts['manual_actions']} manual "
        "action(s), and "
        f"{counts['informational_actions']} "
        "informational action(s). "
        f"Plan status: {plan_status}. "
        f"Execution mode: {execution_mode}."
    )


def more_severe(
    first: str,
    second: str,
) -> str:
    return max(
        (
            first,
            second,
        ),
        key=lambda value: (
            SEVERITY_RANK.get(
                value,
                0,
            )
        ),
    )


def sort_actions(
    actions: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:
    result = deduplicate_actions(
        actions
    )

    result.sort(
        key=lambda item: (
            -SEVERITY_RANK.get(
                str(
                    item.get(
                        "severity",
                        "INFO",
                    )
                ),
                0,
            ),
            str(
                item.get(
                    "target",
                    "",
                )
            ),
            str(
                item.get(
                    "action_type",
                    "",
                )
            ),
        )
    )

    for index, item in enumerate(
        result,
        start=1,
    ):
        item["action_rank"] = index

    return result


def deduplicate_actions(
    actions: Iterable[
        Mapping[str, Any]
    ],
) -> list[dict[str, Any]]:
    result: list[
        dict[str, Any]
    ] = []

    seen: set[
        tuple[str, str, str]
    ] = set()

    for source in actions:
        item = dict(source)

        identity = (
            str(
                item.get(
                    "action_class",
                    "",
                )
            ),
            str(
                item.get(
                    "action_type",
                    "",
                )
            ),
            str(
                item.get(
                    "target",
                    "",
                )
            ),
        )

        if identity in seen:
            continue

        seen.add(identity)
        result.append(item)

    return result


def write_remediation_outputs(
    plan: Mapping[str, Any],
) -> None:
    """Write remediation plan JSON, CSV, and Markdown outputs."""
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REMEDIATION_PLAN_JSON.write_text(
        json.dumps(
            dict(plan),
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    pd.DataFrame(
        plan.get(
            "execution_steps",
            [],
        )
    ).to_csv(
        REMEDIATION_PLAN_CSV,
        index=False,
    )

    REMEDIATION_PLAN_MD.write_text(
        render_remediation_markdown(
            plan
        ),
        encoding="utf-8",
    )


def build_and_write_remediation_plan(
    health_report: Mapping[
        str,
        Any,
    ] | None = None,
) -> dict[str, Any]:
    plan = build_remediation_plan(
        health_report
    )

    write_remediation_outputs(
        plan
    )

    return plan


def render_remediation_markdown(
    plan: Mapping[str, Any],
) -> str:
    execution = plan.get(
        "execution",
        {},
    )

    lines = [
        "# Atlas Remediation Plan",
        "",
        (
            f"- Plan status: "
            f"`{plan['plan_status']}`"
        ),
        (
            f"- Source health: "
            f"`{plan['source_health_status']}`"
        ),
        (
            f"- Execution mode: "
            f"`{execution.get('mode', 'NONE')}`"
        ),
        (
            f"- Execution authorized: "
            f"`{execution.get('authorized', False)}`"
        ),
        (
            f"- Recommended command: "
            f"`{execution.get('recommended_command', '')}`"
        ),
        "",
        "## Ordered Execution Steps",
        "",
        "| Step | Job | Severity | Prerequisites | Sources |",
        "|---:|---|---:|---|---|",
    ]

    for step in plan.get(
        "execution_steps",
        [],
    ):
        lines.append(
            "| "
            + str(step["step"])
            + " | "
            + str(step["job_id"])
            + " | "
            + str(step["severity"])
            + " | "
            + str(
                step[
                    "prerequisite_plan_jobs"
                ]
            ).replace(
                "|",
                ", ",
            )
            + " | "
            + str(
                step[
                    "source_action_types"
                ]
            ).replace(
                "|",
                ", ",
            )
            + " |"
        )

    lines.extend([
        "",
        "## Manual Actions",
        "",
    ])

    for item in plan.get(
        "manual_actions",
        [],
    ):
        lines.append(
            "- "
            + str(
                item.get(
                    "severity",
                    "",
                )
            )
            + ": "
            + str(
                item.get(
                    "action_type",
                    "",
                )
            )
            + " ? "
            + str(
                item.get(
                    "target",
                    "",
                )
            )
        )

    lines.extend([
        "",
        "## Informational Actions",
        "",
    ])

    for item in plan.get(
        "informational_actions",
        [],
    ):
        lines.append(
            "- "
            + str(
                item.get(
                    "action_type",
                    "",
                )
            )
            + " ? "
            + str(
                item.get(
                    "target",
                    "",
                )
            )
        )

    lines.append("")

    return "\n".join(lines)


__all__ = [
    "EXECUTABLE_ACTION_TYPES",
    "INFORMATIONAL_ACTION_TYPES",
    "MANUAL_ACTION_TYPES",
    "OUTPUT_DIR",
    "REMEDIATION_PLAN_CSV",
    "REMEDIATION_PLAN_JSON",
    "REMEDIATION_PLAN_MD",
    "REMEDIATION_PLAN_VERSION",
    "build_and_write_remediation_plan",
    "build_execution_steps",
    "build_remediation_plan",
    "expand_job_repair_set",
    "render_remediation_markdown",
    "write_remediation_outputs",
]
