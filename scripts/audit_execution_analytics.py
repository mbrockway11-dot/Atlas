"""Audit the latest G.13 execution analytics report."""

from __future__ import annotations

import json

from atlas.investment.execution.analytics import (
    ASSET_CLASS_EXECUTION_SCORECARD_JSON,
    ASSET_EXECUTION_SCORECARD_JSON,
    DAILY_EXECUTION_SUMMARY_JSON,
    EXECUTION_ANALYTICS_JSON,
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
        EXECUTION_ANALYTICS_JSON
    )

    daily = load(
        DAILY_EXECUTION_SUMMARY_JSON
    )

    asset = load(
        ASSET_EXECUTION_SCORECARD_JSON
    )

    asset_class = load(
        ASSET_CLASS_EXECUTION_SCORECARD_JSON
    )

    summary = report.get(
        "summary",
        {},
    )

    contract = report.get(
        "contract",
        {},
    )

    paper_only = bool(
        contract.get(
            "paper_only",
            False,
        )
        and contract.get(
            "read_only",
            False,
        )
        and contract.get(
            "verified_records_only",
            False,
        )
        and not contract.get(
            "mutates_account",
            True,
        )
        and not contract.get(
            "submits_orders",
            True,
        )
        and not contract.get(
            "uses_credentials",
            True,
        )
        and not contract.get(
            "live_execution",
            True,
        )
    )

    output_ids_match = bool(
        report
        and daily.get(
            "analytics_id"
        )
        == report.get(
            "analytics_id"
        )
        and asset.get(
            "analytics_id"
        )
        == report.get(
            "analytics_id"
        )
        and asset_class.get(
            "analytics_id"
        )
        == report.get(
            "analytics_id"
        )
    )

    reconciled = bool(
        summary.get(
            "order_count",
            0,
        )
        == 0
        or summary.get(
            "reconciliation_success_rate",
            0.0,
        )
        == 1.0
    )

    costs_consistent = abs(
        float(
            summary.get(
                "total_execution_cost",
                0.0,
            )
        )
        - (
            float(
                summary.get(
                    "fee_cost",
                    0.0,
                )
            )
            + float(
                summary.get(
                    "slippage_cost",
                    0.0,
                )
            )
        )
    ) <= 1e-8

    success = bool(
        report.get(
            "success",
            False,
        )
        and paper_only
        and output_ids_match
        and reconciled
        and costs_consistent
    )

    print(
        "ATLAS EXECUTION ANALYTICS "
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
        "Paper-only/read-only boundary:",
        paper_only,
    )

    print(
        "Output IDs match:",
        output_ids_match,
    )

    print(
        "Reconciliation rate valid:",
        reconciled,
    )

    print(
        "Cost decomposition valid:",
        costs_consistent,
    )

    print(
        "Orders analyzed:",
        summary.get(
            "order_count",
            0,
        ),
    )

    print(
        "Full fill rate:",
        summary.get(
            "full_fill_rate",
            0.0,
        ),
    )

    print(
        "Fees:",
        summary.get(
            "fee_cost",
            0.0,
        ),
    )

    print(
        "Slippage cost:",
        summary.get(
            "slippage_cost",
            0.0,
        ),
    )

    print(
        "Total execution cost:",
        summary.get(
            "total_execution_cost",
            0.0,
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
