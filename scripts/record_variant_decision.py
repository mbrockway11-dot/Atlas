"""Record an explicit manual variant decision."""

from __future__ import annotations

import argparse

import pandas as pd

from atlas.investment.variant_decisions.config import (
    DECISION_HISTORY_CSV,
    LEDGER_CSV,
)
from atlas.investment.variant_decisions.decisions import (
    record_manual_decision,
    safe_read_csv,
)
from atlas.investment.variant_decisions.report import (
    build_variant_decision_report,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record a human decision for one "
            "validated Atlas variant."
        )
    )

    parser.add_argument(
        "--variant-id",
        required=True,
    )

    parser.add_argument(
        "--decision",
        required=True,
        choices=[
            "PENDING",
            "APPROVED",
            "REJECTED",
            "ARCHIVED",
            "DEFERRED",
            "REVISIT_LATER",
        ],
    )

    parser.add_argument(
        "--reviewer",
        required=True,
    )

    parser.add_argument(
        "--rationale",
        required=True,
    )

    parser.add_argument(
        "--approval-version",
        default="",
    )

    parser.add_argument(
        "--implementation-status",
        default="",
    )

    parser.add_argument(
        "--revisit-after",
        default="",
    )

    parser.add_argument(
        "--notes",
        default="",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    build_variant_decision_report()

    ledger = safe_read_csv(
        LEDGER_CSV
    )

    history = safe_read_csv(
        DECISION_HISTORY_CSV
    )

    updated_ledger, updated_history, record = (
        record_manual_decision(
            ledger=ledger,
            history=history,
            variant_id=(
                arguments.variant_id
            ),
            decision=(
                arguments.decision
            ),
            reviewer=(
                arguments.reviewer
            ),
            rationale=(
                arguments.rationale
            ),
            approval_version=(
                arguments.approval_version
            ),
            implementation_status=(
                arguments.implementation_status
            ),
            revisit_after=(
                arguments.revisit_after
            ),
            notes=arguments.notes,
        )
    )

    updated_ledger.to_csv(
        LEDGER_CSV,
        index=False,
    )

    updated_history.to_csv(
        DECISION_HISTORY_CSV,
        index=False,
    )

    report = (
        build_variant_decision_report()
    )

    print(True)
    print(
        "Recorded manual variant decision."
    )
    print(record)
    print(report["summary"])


if __name__ == "__main__":
    main()
