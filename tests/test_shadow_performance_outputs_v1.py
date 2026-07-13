"""Tests for rebuilding G.14 historical performance outputs."""

from __future__ import annotations

from pathlib import Path

from atlas.investment.execution.performance_ledger import (
    append_performance_observation,
    build_observation_id,
    rebuild_performance_outputs,
)


def observation():
    result = {
        "version": "1.0.0",
        "analytics_id": "ANALYTICS-1",
        "pipeline_id": "PIPELINE-1",
        "cycle_id": "CYCLE-1",
        "plan_id": "PLAN-1",
        "snapshot_id": "SNAPSHOT-1",
        "observed_at": (
            "2026-07-13T16:00:00+00:00"
        ),
        "starting_equity": 10000.0,
        "ending_equity": 9997.4,
        "cycle_pnl": -2.6,
        "cycle_return": -0.00026,
        "realized_pnl_change": -1.6,
        "fee_cost": 1.6,
        "slippage_cost": 1.0,
        "total_execution_cost": 2.6,
        "execution_cost_bps": 2.6,
        "gross_fill_notional": 2000.0,
        "turnover_ratio": 0.2,
        "ending_cash_weight": 0.8,
        "ending_gross_exposure_ratio": 0.2,
        "order_count": 2,
        "filled_order_count": 2,
        "full_fill_rate": 1.0,
        "rejection_rate": 0.0,
        "reconciliation_success_rate": 1.0,
        "weighted_slippage_bps": 5.0,
        "weighted_implementation_shortfall_bps": 13.0,
        "average_time_to_completion_ms": 0.1,
        "paper_only": True,
        "live_execution": False,
        "credentials_used": False,
    }

    result["observation_id"] = (
        build_observation_id(
            result
        )
    )

    return result


def test_rebuilds_all_views(
    tmp_path: Path,
):
    ledger = (
        tmp_path / "ledger.jsonl"
    )

    summary = (
        tmp_path / "summary.json"
    )

    equity = (
        tmp_path / "equity.json"
    )

    drawdown = (
        tmp_path / "drawdown.json"
    )

    rolling = (
        tmp_path / "rolling.json"
    )

    append_performance_observation(
        observation(),
        path=ledger,
    )

    report = (
        rebuild_performance_outputs(
            ledger_path=ledger,
            summary_path=summary,
            equity_path=equity,
            drawdown_path=drawdown,
            rolling_path=rolling,
            write_outputs=True,
        )
    )

    assert report["success"]

    assert (
        report["summary"][
            "observation_count"
        ]
        == 1
    )

    assert summary.exists()
    assert equity.exists()
    assert drawdown.exists()
    assert rolling.exists()
