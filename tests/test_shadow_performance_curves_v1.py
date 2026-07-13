"""Tests for historical equity and drawdown curves."""

from __future__ import annotations

from atlas.investment.execution.performance_ledger import (
    build_equity_and_drawdown_curves,
    summarize_performance,
)


def records():
    return [
        {
            "ledger_index": 1,
            "starting_equity": 10000.0,
            "cycle_pnl": 100.0,
            "cycle_return": 0.01,
            "fee_cost": 1.0,
            "slippage_cost": 0.5,
            "total_execution_cost": 1.5,
            "execution_cost_bps": 1.5,
            "full_fill_rate": 1.0,
            "reconciliation_success_rate": 1.0,
            "order_count": 1,
        },
        {
            "ledger_index": 2,
            "starting_equity": 10100.0,
            "cycle_pnl": -202.0,
            "cycle_return": -0.02,
            "fee_cost": 1.0,
            "slippage_cost": 0.5,
            "total_execution_cost": 1.5,
            "execution_cost_bps": 1.5,
            "full_fill_rate": 1.0,
            "reconciliation_success_rate": 1.0,
            "order_count": 1,
        },
    ]


def test_linked_equity_and_drawdown():
    values = (
        build_equity_and_drawdown_curves(
            records()
        )
    )

    assert (
        round(
            values[
                "equity_curve"
            ][-1][
                "linked_equity"
            ],
            8,
        )
        == 9898.0
    )

    assert (
        round(
            values[
                "drawdown_curve"
            ][-1][
                "drawdown_pct"
            ],
            8,
        )
        == -0.02
    )


def test_summary_uses_linked_returns():
    values = (
        build_equity_and_drawdown_curves(
            records()
        )
    )

    summary = summarize_performance(
        records(),
        equity_curve=(
            values["equity_curve"]
        ),
        drawdown_curve=(
            values[
                "drawdown_curve"
            ]
        ),
    )

    assert (
        round(
            summary[
                "linked_return"
            ],
            8,
        )
        == -0.0102
    )

    assert (
        summary[
            "maximum_drawdown_pct"
        ]
        == -0.02
    )
