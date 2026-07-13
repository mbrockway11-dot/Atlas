"""Tests for the complete G.13 execution analytics report."""

from __future__ import annotations

from pathlib import Path

from atlas.investment.execution.analytics import (
    build_execution_analytics,
)


def test_builds_scorecards_and_outputs(
    tmp_path: Path,
):
    shadow = {
        "cycle_id": "CYCLE-1",
        "plan_id": "PLAN-1",
        "status": "COMPLETED",
        "completed_at": (
            "2026-07-13T16:00:00+00:00"
        ),
        "account_before": {
            "cash": 10_000.0,
            "positions": {},
        },
        "account_after": {
            "cash": 8_998.7,
            "positions": {
                "SPY": {
                    "asset": "SPY",
                    "quantity": 10.0,
                    "average_price": 100.05,
                    "mark_price": 100.0,
                }
            },
        },
        "results": [
            {
                "success": True,
                "intent_id": "INTENT-1",
                "execution": {
                    "execution_id": "EXEC-1",
                    "intent": {
                        "intent_id": (
                            "INTENT-1"
                        ),
                        "asset": "SPY",
                        "side": "BUY",
                        "quantity": 10.0,
                        "reference_price": 100.0,
                    },
                    "risk": {
                        "approved": True,
                    },
                    "order": {
                        "order_id": "ORDER-1",
                        "asset": "SPY",
                        "side": "BUY",
                        "requested_quantity": 10.0,
                        "filled_quantity": 10.0,
                        "remaining_quantity": 0.0,
                        "status": "FILLED",
                        "submitted_at": (
                            "2026-07-13T16:00:00+00:00"
                        ),
                        "completed_at": (
                            "2026-07-13T16:00:00.100000+00:00"
                        ),
                        "average_fill_price": 100.05,
                        "fee_paid": 0.8,
                    },
                    "fills": [
                        {
                            "quantity": 10.0,
                            "price": 100.05,
                            "notional": 1000.5,
                            "fee": 0.8,
                            "slippage_bps": 5.0,
                        }
                    ],
                    "reconciliation": {
                        "success": True,
                    },
                },
            }
        ],
    }

    report = build_execution_analytics(
        shadow,
        pipeline_report={
            "pipeline_id": (
                "PIPELINE-1"
            )
        },
        write_outputs=True,
        report_path=(
            tmp_path / "report.json"
        ),
        history_path=(
            tmp_path / "history.jsonl"
        ),
        daily_path=(
            tmp_path / "daily.json"
        ),
        asset_path=(
            tmp_path / "asset.json"
        ),
        asset_class_path=(
            tmp_path / "class.json"
        ),
    )

    assert report["success"]

    assert (
        report["summary"][
            "order_count"
        ]
        == 1
    )

    assert (
        report["asset_scorecard"][0][
            "asset"
        ]
        == "SPY"
    )

    assert (
        report[
            "asset_class_scorecard"
        ][0][
            "asset_class"
        ]
        == "EQUITY"
    )

    assert (
        tmp_path
        .joinpath("report.json")
        .exists()
    )
