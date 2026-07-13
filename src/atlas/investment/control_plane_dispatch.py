"""Controlled dispatch of signed Atlas remediation approvals."""

from __future__ import annotations

from typing import Any

from atlas.investment.control_plane_approval import (
    APPROVAL_JSON,
    REMEDIATION_PLAN_JSON,
    load_json,
    mark_approval_used,
    validate_approval,
)
from atlas.investment.research_orchestrator.cycle import (
    run_research_cycle,
)


def dispatch_approved_plan(
    *,
    plan_path=REMEDIATION_PLAN_JSON,
    approval_path=APPROVAL_JSON,
    secret: str | None = None,
    timeout_seconds: int = 1800,
    continue_on_failure: bool = False,
) -> dict[str, Any]:
    """Validate and dispatch only the explicitly approved job prefix."""
    plan = load_json(
        plan_path
    )

    approval = load_json(
        approval_path
    )

    validation = validate_approval(
        plan=plan,
        approval=approval,
        secret=secret,
    )

    if not validation["valid"]:
        raise ValueError(
            "Approval validation failed: "
            + "|".join(
                validation["errors"]
            )
        )

    approved_job_ids = list(
        validation[
            "approved_job_ids"
        ]
    )

    execution = plan.get(
        "execution",
        {},
    )

    mode = str(
        execution.get(
            "mode",
            "EXECUTE",
        )
    )

    result = run_research_cycle(
        execute=True,
        resume=mode == "RESUME",
        restart=False,
        max_jobs=len(
            approved_job_ids
        ),
        timeout_seconds=(
            timeout_seconds
        ),
        continue_on_failure=(
            continue_on_failure
        ),
        self_heal=True,
        use_build_cache=True,
        allowed_job_ids=set(
            approved_job_ids
        ),
    )

    mark_approval_used(
        approval,
        run_id=str(
            result.get(
                "run_id",
                "",
            )
        ),
        path=approval_path,
    )

    return {
        "success": not bool(
            result.get(
                "failure_detected",
                False,
            )
        ),
        "approval_id": (
            validation["approval_id"]
        ),
        "approved_by": (
            validation["approved_by"]
        ),
        "approved_job_ids": (
            approved_job_ids
        ),
        "run_id": str(
            result.get(
                "run_id",
                "",
            )
        ),
        "cycle": result,
    }


__all__ = [
    "dispatch_approved_plan",
]
