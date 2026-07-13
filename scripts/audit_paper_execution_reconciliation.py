"""Audit paper execution provenance and reconciliation."""

from __future__ import annotations

import json

from atlas.investment.execution.provenance import (
    read_execution_events,
    validate_execution_provenance,
)
from atlas.investment.execution.reconciliation import (
    LATEST_RECONCILIATION_JSON,
)
from atlas.investment.execution.service import (
    LATEST_REPORT_JSON,
)


def main() -> int:
    report = {}

    if LATEST_REPORT_JSON.exists():
        report = json.loads(
            LATEST_REPORT_JSON.read_text(
                encoding="utf-8"
            )
        )

    reconciliation = {}

    if (
        LATEST_RECONCILIATION_JSON.exists()
    ):
        reconciliation = json.loads(
            LATEST_RECONCILIATION_JSON.read_text(
                encoding="utf-8"
            )
        )

    events = read_execution_events()

    provenance = (
        validate_execution_provenance(
            events
        )
    )

    reconciliation_success = bool(
        not reconciliation
        or reconciliation.get(
            "success",
            False,
        )
    )

    paper_only = bool(
        not report
        or (
            report.get(
                "mode"
            )
            == "PAPER"
            and not report.get(
                "live_execution",
                False,
            )
        )
    )

    success = bool(
        provenance["valid"]
        and reconciliation_success
        and paper_only
    )

    print(
        "ATLAS PAPER EXECUTION RECONCILIATION "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )

    print(
        "Provenance events:",
        provenance[
            "event_count"
        ],
    )

    print(
        "Provenance chain valid:",
        provenance["valid"],
    )

    print(
        "Reconciliation present:",
        bool(
            reconciliation
        ),
    )

    print(
        "Reconciliation success:",
        reconciliation_success,
    )

    print(
        "Paper-only boundary:",
        paper_only,
    )

    if reconciliation:
        print(
            "Reconciliation ID:",
            reconciliation.get(
                "reconciliation_id",
                "",
            ),
        )
        print(
            "Errors:",
            reconciliation.get(
                "errors",
                [],
            ),
        )
        print(
            "Warnings:",
            reconciliation.get(
                "warnings",
                [],
            ),
        )

    if provenance["errors"]:
        print(
            "Provenance errors:"
        )

        for error in provenance[
            "errors"
        ]:
            print("-", error)

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
