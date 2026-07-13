"""Audit the latest Atlas shadow portfolio pipeline."""

from __future__ import annotations

import json

from atlas.investment.execution.shadow_pipeline import (
    SHADOW_PIPELINE_CHECKPOINT_JSON,
    SHADOW_PIPELINE_REPORT_JSON,
)
from atlas.investment.market_data import (
    validate_market_data_audit,
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
    report = load(
        SHADOW_PIPELINE_REPORT_JSON
    )

    checkpoint = load(
        SHADOW_PIPELINE_CHECKPOINT_JSON
    )

    market_audit = (
        validate_market_data_audit()
    )

    contract = report.get(
        "contract",
        {}
    )

    paper_only = bool(
        report
        and contract.get(
            "paper_only",
            False,
        )
        and not contract.get(
            "live_execution",
            False,
        )
        and not contract.get(
            "credentials_used",
            False,
        )
    )

    checkpoint_matches = bool(
        report
        and checkpoint.get(
            "pipeline_id"
        )
        == report.get(
            "pipeline_id"
        )
        and checkpoint.get(
            "status"
        )
        == report.get(
            "status"
        )
        and checkpoint.get(
            "snapshot_id"
        )
        == report.get(
            "snapshot_id"
        )
    )

    attribution_present = bool(
        report.get(
            "attribution_id"
        )
        and report.get(
            "performance"
        )
    )

    success = bool(
        report.get(
            "success",
            False,
        )
        and report.get(
            "status"
        )
        in {
            "COMPLETED",
            "PAUSED",
        }
        and paper_only
        and checkpoint_matches
        and attribution_present
        and market_audit["valid"]
    )

    print(
        "ATLAS SHADOW PORTFOLIO PIPELINE "
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
        "Status:",
        report.get(
            "status",
            "",
        ),
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
        "Market audit valid:",
        market_audit["valid"],
    )

    print(
        "Attribution present:",
        attribution_present,
    )

    if report:
        print(
            "Pipeline ID:",
            report.get(
                "pipeline_id",
                "",
            ),
        )

        print(
            "Snapshot ID:",
            report.get(
                "snapshot_id",
                "",
            ),
        )

        print(
            "Performance:",
            report.get(
                "performance",
                {},
            ),
        )

        print(
            "Errors:",
            report.get(
                "errors",
                [],
            ),
        )

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
