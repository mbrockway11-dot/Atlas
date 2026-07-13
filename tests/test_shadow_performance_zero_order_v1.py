"""Tests for zero-order cycle semantics in the performance ledger."""

from __future__ import annotations

from atlas.investment.execution.performance_ledger import (
    build_equity_and_drawdown_curves,
    summarize_performance,
)


def test_zero_order_cycles_do_not_dilute_execution_rates():
    records = [
        {
            "ledger_index": 1,
            "starting_equity": 10000.0,
            "cycle_pnl": -2.0,
            "cycle_return": -0.0002,
            "fee_cost": 1.2,
            "slippage_cost": 0.8,
            "total_execution_cost": 2.0,
            "execution_cost_bps": 2.0,
            "full_fill_rate": 1.0,
            "reconciliation_success_rate": 1.0,
            "order_count": 2,
        },
        {
            "ledger_index": 2,
            "starting_equity": 9998.0,
            "cycle_pnl": 0.0,
            "cycle_return": 0.0,
            "fee_cost": 0.0,
            "slippage_cost": 0.0,
            "total_execution_cost": 0.0,
            "execution_cost_bps": 0.0,
            "full_fill_rate": 0.0,
            "reconciliation_success_rate": 0.0,
            "order_count": 0,
        },
    ]

    curves = (
        build_equity_and_drawdown_curves(
            records
        )
    )

    summary = summarize_performance(
        records,
        equity_curve=(
            curves["equity_curve"]
        ),
        drawdown_curve=(
            curves["drawdown_curve"]
        ),
    )

    assert (
        summary[
            "average_full_fill_rate"
        ]
        == 1.0
    )

    assert (
        summary[
            "average_reconciliation_success_rate"
        ]
        == 1.0
    )

    assert summary[
        "observation_count"
    ] == 2

    assert summary[
        "total_orders"
    ] == 2
