"""Audit the Atlas scheduler and market-session control plane."""

from __future__ import annotations

import json

from atlas.investment.scheduling import (
    DEFAULT_JOBS,
    SCHEDULER_DECISION_JSON,
    SUPPORTED_SESSIONS,
    evaluate_scheduler,
    validate_job_graph,
)


def load(path):
    if not path.exists():
        return {}

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    return (
        payload
        if isinstance(
            payload,
            dict,
        )
        else {}
    )


def main() -> int:
    graph = validate_job_graph(
        DEFAULT_JOBS
    )

    decision = load(
        SCHEDULER_DECISION_JSON
    )

    if not decision:
        decision = evaluate_scheduler()

    contract = dict(
        decision.get(
            "contract",
            {},
        )
        or {}
    )

    safety_valid = bool(
        contract.get(
            "decision_only",
            False,
        )
        and contract.get(
            "commands_not_executed",
            False,
        )
        and contract.get(
            "paper_only",
            False,
        )
        and not contract.get(
            "submits_orders",
            True,
        )
        and not contract.get(
            "mutates_account",
            True,
        )
        and not contract.get(
            "credentials_used",
            True,
        )
        and not contract.get(
            "live_execution",
            True,
        )
    )

    job_names = {
        job.name
        for job in DEFAULT_JOBS
    }

    due_jobs_valid = all(
        name in job_names
        for name in decision.get(
            "due_jobs",
            [],
        )
    )

    sessions_valid = all(
        job.session_name
        in SUPPORTED_SESSIONS
        for job in DEFAULT_JOBS
    )

    commands_remain_plans = all(
        isinstance(
            row.get(
                "command"
            ),
            (
                list,
                tuple,
            ),
        )
        for row in decision.get(
            "execution_plan",
            [],
        )
    )

    execution_plan_matches = bool(
        len(
            decision.get(
                "execution_plan",
                [],
            )
        )
        == len(
            decision.get(
                "due_jobs",
                [],
            )
        )
    )

    success = bool(
        graph["valid"]
        and decision.get(
            "success",
            False,
        )
        and safety_valid
        and due_jobs_valid
        and sessions_valid
        and commands_remain_plans
        and execution_plan_matches
    )

    print(
        "ATLAS INVESTMENT SCHEDULER "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )

    print(
        "Job graph valid:",
        graph["valid"],
    )

    print(
        "Jobs:",
        graph["job_count"],
    )

    print(
        "Registry sessions aligned:",
        sessions_valid,
    )

    print(
        "Decision present:",
        bool(decision),
    )

    print(
        "Safety boundary valid:",
        safety_valid,
    )

    print(
        "Due jobs valid:",
        due_jobs_valid,
    )

    print(
        "Commands remain plans:",
        commands_remain_plans,
    )

    print(
        "Execution plan matches due jobs:",
        execution_plan_matches,
    )

    print(
        "Due jobs:",
        decision.get(
            "due_jobs",
            [],
        ),
    )

    print(
        "Errors:",
        graph["errors"],
    )

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
