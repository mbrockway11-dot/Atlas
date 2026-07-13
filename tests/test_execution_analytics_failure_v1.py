"""Failure-boundary tests for execution analytics."""

from __future__ import annotations

from atlas.investment.execution.analytics import (
    build_execution_analytics,
)


def test_unreconciled_record_fails_report():
    report = build_execution_analytics(
        {
            "cycle_id": "CYCLE-1",
            "plan_id": "PLAN-1",
            "status": "HALTED",
            "account_before": {
                "cash": 1000.0,
            },
            "account_after": {
                "cash": 1000.0,
            },
            "results": [
                {
                    "success": False,
                    "intent_id": "INTENT-1",
                    "execution": {
                        "intent": {
                            "intent_id": (
                                "INTENT-1"
                            ),
                            "asset": "BTC-USD",
                            "side": "BUY",
                            "quantity": 0.01,
                            "reference_price": 50_000.0,
                        },
                        "risk": {
                            "approved": True,
                        },
                        "order": {
                            "order_id": (
                                "ORDER-1"
                            ),
                            "asset": "BTC-USD",
                            "side": "BUY",
                            "requested_quantity": 0.01,
                            "filled_quantity": 0.01,
                            "remaining_quantity": 0.0,
                            "status": "FILLED",
                            "average_fill_price": 50_025.0,
                            "fee_paid": 0.4,
                        },
                        "fills": [],
                        "reconciliation": {
                            "success": False,
                        },
                    },
                }
            ],
        },
        write_outputs=False,
    )

    assert not report["success"]

    assert any(
        error.startswith(
            "RECONCILIATION_NOT_VERIFIED"
        )
        for error
        in report["errors"]
    )
