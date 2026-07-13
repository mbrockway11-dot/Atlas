"""Tests for rolling nonannualized shadow-performance metrics."""

from __future__ import annotations

from atlas.investment.execution.performance_ledger import (
    build_rolling_metrics,
)


def test_rolling_metrics_respect_window():
    records = [
        {
            "ledger_index": 1,
            "cycle_pnl": 10.0,
            "cycle_return": 0.01,
            "total_execution_cost": 1.0,
            "execution_cost_bps": 1.0,
        },
        {
            "ledger_index": 2,
            "cycle_pnl": -5.0,
            "cycle_return": -0.005,
            "total_execution_cost": 1.0,
            "execution_cost_bps": 1.0,
        },
        {
            "ledger_index": 3,
            "cycle_pnl": 20.0,
            "cycle_return": 0.02,
            "total_execution_cost": 1.0,
            "execution_cost_bps": 1.0,
        },
    ]

    rows = build_rolling_metrics(
        records,
        window=2,
    )

    assert len(rows) == 3

    assert (
        rows[-1][
            "observations_in_window"
        ]
        == 2
    )

    assert (
        rows[-1][
            "rolling_pnl"
        ]
        == 15.0
    )

    assert (
        rows[-1][
            "rolling_win_rate"
        ]
        == 0.5
    )
