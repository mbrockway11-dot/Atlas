"""Audit the G.14 historical shadow performance ledger and views."""

from __future__ import annotations

import json

from atlas.investment.execution.performance_ledger import (
    SHADOW_DRAWDOWN_CURVE_JSON,
    SHADOW_EQUITY_CURVE_JSON,
    SHADOW_PERFORMANCE_SUMMARY_JSON,
    SHADOW_ROLLING_METRICS_JSON,
    read_performance_ledger,
    validate_performance_ledger,
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
    validation = (
        validate_performance_ledger()
    )

    records = (
        read_performance_ledger()
    )

    summary_payload = load(
        SHADOW_PERFORMANCE_SUMMARY_JSON
    )

    equity_payload = load(
        SHADOW_EQUITY_CURVE_JSON
    )

    drawdown_payload = load(
        SHADOW_DRAWDOWN_CURVE_JSON
    )

    rolling_payload = load(
        SHADOW_ROLLING_METRICS_JSON
    )

    summary = summary_payload.get(
        "summary",
        {},
    )

    contract = summary_payload.get(
        "contract",
        {},
    )

    views_match = bool(
        len(
            equity_payload.get(
                "rows",
                [],
            )
        )
        == len(records)
        and len(
            drawdown_payload.get(
                "rows",
                [],
            )
        )
        == len(records)
        and len(
            rolling_payload.get(
                "rows",
                [],
            )
        )
        == len(records)
    )

    summary_matches = bool(
        summary.get(
            "observation_count",
            -1,
        )
        == len(records)
    )

    safety_valid = bool(
        contract.get(
            "append_only_source",
            False,
        )
        and contract.get(
            "hash_chained",
            False,
        )
        and contract.get(
            "read_only_views",
            False,
        )
        and contract.get(
            "paper_only",
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
            "live_execution",
            True,
        )
        and not contract.get(
            "credentials_used",
            True,
        )
    )

    cost_decomposition_valid = all(
        abs(
            float(
                record.get(
                    "total_execution_cost",
                    0.0,
                )
            )
            - (
                float(
                    record.get(
                        "fee_cost",
                        0.0,
                    )
                )
                + float(
                    record.get(
                        "slippage_cost",
                        0.0,
                    )
                )
            )
        )
        <= 1e-8
        for record in records
    )

    success = bool(
        validation["valid"]
        and records
        and views_match
        and summary_matches
        and safety_valid
        and cost_decomposition_valid
    )

    print(
        "ATLAS SHADOW PERFORMANCE LEDGER "
        + (
            "PASSED"
            if success
            else "FAILED"
        )
    )

    print(
        "Ledger present:",
        bool(records),
    )

    print(
        "Ledger records:",
        len(records),
    )

    print(
        "Hash chain valid:",
        validation["valid"],
    )

    print(
        "Views match ledger:",
        views_match,
    )

    print(
        "Summary matches ledger:",
        summary_matches,
    )

    print(
        "Safety boundary valid:",
        safety_valid,
    )

    print(
        "Cost decomposition valid:",
        cost_decomposition_valid,
    )

    print(
        "Cumulative PnL:",
        summary.get(
            "cumulative_pnl",
            0.0,
        ),
    )

    print(
        "Linked return:",
        summary.get(
            "linked_return",
            0.0,
        ),
    )

    print(
        "Maximum drawdown:",
        summary.get(
            "maximum_drawdown_pct",
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
        validation["errors"],
    )

    print(
        "Warnings:",
        validation["warnings"],
    )

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
