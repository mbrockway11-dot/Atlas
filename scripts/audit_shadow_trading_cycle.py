"""Audit the latest Atlas paper shadow-trading cycle."""

from __future__ import annotations

import json

from atlas.investment.execution.account_store import (
    PAPER_ACCOUNT_JSON,
)
from atlas.investment.execution.lifecycle import (
    PaperOrderLifecycleStore,
)
from atlas.investment.execution.provenance import (
    validate_execution_provenance,
)
from atlas.investment.execution.shadow_loop import (
    SHADOW_CHECKPOINT_JSON,
    SHADOW_REPORT_JSON,
)


def load(path):
    if not path.exists():
        return {}

    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def main() -> int:
    report = load(
        SHADOW_REPORT_JSON
    )

    checkpoint = load(
        SHADOW_CHECKPOINT_JSON
    )

    account = load(
        PAPER_ACCOUNT_JSON
    )

    lifecycle = (
        PaperOrderLifecycleStore()
        .validate_transition_chain()
    )

    provenance = (
        validate_execution_provenance()
    )

    paper_only = bool(
        report.get(
            "mode"
        )
        in {
            None,
            "SHADOW_PAPER",
        }
        and not report.get(
            "live_execution",
            False,
        )
        and not checkpoint.get(
            "live_execution",
            False,
        )
    )

    checkpoint_matches = bool(
        not report
        or (
            checkpoint.get(
                "cycle_id"
            )
            == report.get(
                "cycle_id"
            )
            and checkpoint.get(
                "plan_id"
            )
            == report.get(
                "plan_id"
            )
            and checkpoint.get(
                "status"
            )
            == report.get(
                "status"
            )
        )
    )

    success = bool(
        paper_only
        and lifecycle["valid"]
        and provenance["valid"]
        and checkpoint_matches
        and (
            not report
            or report.get(
                "status"
            )
            in {
                "COMPLETED",
                "PAUSED",
            }
        )
    )

    print(
        "ATLAS SHADOW TRADING AUDIT "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )

    print(
        "Report present:",
        bool(report),
    )

    print(
        "Account present:",
        bool(account),
    )

    print(
        "Paper-only boundary:",
        paper_only,
    )

    print(
        "Checkpoint matches:",
        checkpoint_matches,
    )

    print(
        "Lifecycle chain valid:",
        lifecycle["valid"],
    )

    print(
        "Provenance chain valid:",
        provenance["valid"],
    )

    if report:
        print(
            "Status:",
            report.get(
                "status",
                "",
            ),
        )
        print(
            "Counts:",
            report.get(
                "counts",
                {},
            ),
        )
        print(
            "Halt reason:",
            report.get(
                "halt_reason",
                "",
            ),
        )

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
