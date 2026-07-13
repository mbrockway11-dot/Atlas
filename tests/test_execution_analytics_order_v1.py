"""Tests for per-order execution-quality analytics."""

from __future__ import annotations

from atlas.investment.execution.analytics import (
    analyze_execution_result,
)


def execution_result(
    *,
    side: str = "BUY",
    fill_price: float = 100.05,
):
    return {
        "success": True,
        "intent_id": "INTENT-1",
        "execution": {
            "execution_id": "EXECUTION-1",
            "intent": {
                "intent_id": "INTENT-1",
                "asset": "SPY",
                "side": side,
                "quantity": 10.0,
                "reference_price": 100.0,
            },
            "risk": {
                "approved": True,
            },
            "order": {
                "order_id": "ORDER-1",
                "intent_id": "INTENT-1",
                "asset": "SPY",
                "side": side,
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
                "average_fill_price": (
                    fill_price
                ),
                "fee_paid": 0.8,
                "rejection_reason": "",
            },
            "fills": [
                {
                    "fill_id": "FILL-1",
                    "quantity": 10.0,
                    "price": fill_price,
                    "notional": (
                        10.0
                        * fill_price
                    ),
                    "fee": 0.8,
                    "slippage_bps": 5.0,
                }
            ],
            "reconciliation": {
                "success": True,
            },
        },
    }


def test_buy_slippage_is_positive_cost():
    row = analyze_execution_result(
        execution_result(),
        index=1,
    )

    assert (
        round(
            row[
                "signed_slippage_bps"
            ],
            8,
        )
        == 5.0
    )

    assert (
        round(
            row["slippage_cost"],
            8,
        )
        == 0.5
    )

    assert (
        round(
            row[
                "implementation_shortfall"
            ],
            8,
        )
        == 1.3
    )

    assert row[
        "time_to_completion_ms"
    ] == 100.0


def test_sell_lower_fill_is_positive_cost():
    row = analyze_execution_result(
        execution_result(
            side="SELL",
            fill_price=99.95,
        ),
        index=1,
    )

    assert (
        round(
            row[
                "signed_slippage_bps"
            ],
            8,
        )
        == 5.0
    )

    assert (
        round(
            row["slippage_cost"],
            8,
        )
        == 0.5
    )
