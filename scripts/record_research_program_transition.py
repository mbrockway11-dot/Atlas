"""Record one manual research-program lifecycle transition."""

from __future__ import annotations

import argparse

import pandas as pd

from atlas.investment.research_program_manager.config import (
    REGISTRY_CSV,
    STATUS_HISTORY_CSV,
)
from atlas.investment.research_program_manager.report import (
    build_research_program_manager_report,
)
from atlas.investment.research_program_manager.transitions import (
    record_program_transition,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Record one explicit human-governed "
            "research program lifecycle transition."
        )
    )

    parser.add_argument(
        "--program-id",
        required=True,
    )

    parser.add_argument(
        "--status",
        required=True,
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
        default="research-program-manager-v1",
    )

    parser.add_argument(
        "--program-owner",
        default="",
    )

    parser.add_argument(
        "--review-after",
        default="",
    )

    parser.add_argument(
        "--notes",
        default="",
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    build_research_program_manager_report()

    registry = pd.read_csv(
        REGISTRY_CSV,
        dtype=object,
    )

    if (
        STATUS_HISTORY_CSV.exists()
        and STATUS_HISTORY_CSV.stat().st_size > 0
    ):
        try:
            history = pd.read_csv(
                STATUS_HISTORY_CSV,
                dtype=object,
            )
        except pd.errors.EmptyDataError:
            history = pd.DataFrame()
    else:
        history = pd.DataFrame()

    (
        updated_registry,
        updated_history,
        history_row,
    ) = record_program_transition(
        registry=registry,
        history=history,
        program_id=arguments.program_id,
        new_status=arguments.status,
        reviewer=arguments.reviewer,
        rationale=arguments.rationale,
        approval_version=(
            arguments.approval_version
        ),
        program_owner=(
            arguments.program_owner
        ),
        review_after=(
            arguments.review_after
        ),
        notes=arguments.notes,
    )

    updated_registry.to_csv(
        REGISTRY_CSV,
        index=False,
    )

    updated_history.to_csv(
        STATUS_HISTORY_CSV,
        index=False,
    )

    report = (
        build_research_program_manager_report()
    )

    print(True)
    print(
        "Recorded research program transition."
    )
    print(history_row)
    print(report["summary"])


if __name__ == "__main__":
    main()
