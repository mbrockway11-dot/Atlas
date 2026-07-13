"""Tests for paper execution reconciliation."""

from __future__ import annotations

from atlas.investment.execution.reconciliation import (
    reconcile_paper_execution,
)


def valid_report():
    return {
        "mode": "PAPER",
        "live_execution": False,
        "intent": {
            "intent_id": "INTENT-1",
            "asset": "BTC-USD",
            "side": "BUY",
            "quantity": 0.01,
        },
        "risk": {
            "intent_id": "INTENT-1",
            "approved": True,
        },
        "order": {
            "order_id": "ORDER-1",
            "intent_id": "INTENT-1",
            "status": "FILLED",
            "requested_quantity": 0.01,
            "filled_quantity": 0.01,
            "remaining_quantity": 0.0,
            "fee_paid": 0.4,
        },
        "fills": [
            {
                "fill_id": "FILL-1",
                "order_id": "ORDER-1",
                "intent_id": "INTENT-1",
                "quantity": 0.01,
                "notional": 500.0,
                "fee": 0.4,
            }
        ],
        "account_before": {
            "cash": 10_000.0,
            "net_liquidation_value": (
                10_000.0
            ),
            "positions": {},
        },
        "account_after": {
            "cash": 9_499.6,
            "net_liquidation_value": (
                9_999.6
            ),
            "positions": {
                "BTC-USD": {
                    "quantity": 0.01,
                }
            },
        },
    }


def test_valid_execution_reconciles():
    result = (
        reconcile_paper_execution(
            valid_report()
        )
    )

    assert result["success"]
    assert result["errors"] == []


def test_fill_quantity_mismatch_fails():
    report = valid_report()

    report["fills"][0][
        "quantity"
    ] = 0.005

    result = (
        reconcile_paper_execution(
            report
        )
    )

    assert not result["success"]

    assert (
        "FILL_QUANTITY_ORDER_MISMATCH"
        in result["errors"]
    )


def test_duplicate_fill_id_fails():
    report = valid_report()

    report["fills"].append(
        dict(
            report["fills"][0]
        )
    )

    result = (
        reconcile_paper_execution(
            report
        )
    )

    assert not result["success"]

    assert any(
        value.startswith(
            "DUPLICATE_FILL_ID"
        )
        for value in result[
            "errors"
        ]
    )


def test_lifecycle_mismatch_fails():
    result = (
        reconcile_paper_execution(
            valid_report(),
            lifecycle_record={
                "state": (
                    "PARTIALLY_FILLED"
                ),
                "filled_quantity": (
                    0.005
                ),
                "remaining_quantity": (
                    0.005
                ),
            },
        )
    )

    assert not result["success"]

    assert (
        "LIFECYCLE_ORDER_STATE_MISMATCH"
        in result["errors"]
    )
