"""Tests for aggregate execution analytics."""

from __future__ import annotations

from atlas.investment.execution.analytics import (
    summarize_rows,
)


def row(
    *,
    status: str,
    notional: float,
    fee: float,
    slippage: float,
):
    return {
        "status": status,
        "side": "BUY",
        "risk_approved": True,
        "reconciliation_success": True,
        "requested_quantity": 10.0,
        "filled_quantity": (
            10.0
            if status == "FILLED"
            else 5.0
        ),
        "arrival_notional": notional,
        "fill_notional": notional,
        "fee_cost": fee,
        "slippage_cost": (
            slippage
        ),
        "implementation_shortfall": (
            fee
            + slippage
        ),
        "signed_slippage_bps": 5.0,
        "implementation_shortfall_bps": 13.0,
        "time_to_completion_ms": 100.0,
    }


def test_summary_decomposes_costs():
    summary = summarize_rows([
        row(
            status="FILLED",
            notional=1000.0,
            fee=0.8,
            slippage=0.5,
        ),
        row(
            status="PARTIALLY_FILLED",
            notional=500.0,
            fee=0.4,
            slippage=0.25,
        ),
    ])

    assert (
        summary["order_count"]
        == 2
    )

    assert (
        summary["full_fill_rate"]
        == 0.5
    )

    assert (
        summary["partial_fill_rate"]
        == 0.5
    )

    assert (
        round(
            summary["fee_cost"],
            8,
        )
        == 1.2
    )

    assert (
        round(
            summary[
                "slippage_cost"
            ],
            8,
        )
        == 0.75
    )

    assert (
        round(
            summary[
                "total_execution_cost"
            ],
            8,
        )
        == 1.95
    )
