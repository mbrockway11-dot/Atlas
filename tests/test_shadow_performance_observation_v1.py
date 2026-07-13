"""Tests for canonical G.14 performance observations."""

from __future__ import annotations

import pytest

from atlas.investment.execution.performance_ledger import (
    build_performance_observation,
)


def analytics(
    *,
    cycle_id: str = "CYCLE-1",
):
    return {
        "success": True,
        "analytics_id": (
            "ANALYTICS-1"
        ),
        "pipeline_id": (
            "PIPELINE-1"
        ),
        "cycle_id": cycle_id,
        "plan_id": "PLAN-1",
        "generated_at": (
            "2026-07-13T16:00:00+00:00"
        ),
        "summary": {
            "order_count": 2,
            "filled_order_count": 2,
            "full_fill_rate": 1.0,
            "rejection_rate": 0.0,
            "reconciliation_success_rate": 1.0,
            "gross_fill_notional": 2000.0,
            "fee_cost": 1.6,
            "slippage_cost": 1.0,
            "total_execution_cost": 2.6,
            "weighted_slippage_bps": 5.0,
            "weighted_implementation_shortfall_bps": 13.0,
            "average_time_to_completion_ms": 0.1,
        },
        "utilization": {
            "starting_equity": 10000.0,
            "ending_equity": 9997.4,
            "turnover_ratio": 0.20,
            "execution_cost_bps_of_starting_equity": 2.6,
            "ending_cash_weight": 0.80,
            "ending_gross_exposure_ratio": 0.20,
        },
        "contract": {
            "paper_only": True,
            "read_only": True,
            "live_execution": False,
        },
    }


def pipeline(
    *,
    cycle_id: str = "CYCLE-1",
):
    return {
        "success": True,
        "pipeline_id": (
            "PIPELINE-1"
        ),
        "cycle_id": cycle_id,
        "plan_id": "PLAN-1",
        "snapshot_id": "SNAPSHOT-1",
        "started_at": (
            "2026-07-13T15:59:00+00:00"
        ),
        "completed_at": (
            "2026-07-13T16:00:00+00:00"
        ),
        "performance": {
            "starting_net_liquidation_value": 10000.0,
            "ending_net_liquidation_value": 9997.4,
            "total_pnl": -2.6,
            "return_pct": -0.00026,
            "realized_pnl_change": -1.6,
        },
        "contract": {
            "paper_only": True,
            "credentials_used": False,
            "live_execution": False,
        },
    }


def test_builds_verified_observation():
    observation = (
        build_performance_observation(
            analytics_report=(
                analytics()
            ),
            pipeline_report=(
                pipeline()
            ),
        )
    )

    assert (
        observation["cycle_id"]
        == "CYCLE-1"
    )

    assert (
        observation[
            "total_execution_cost"
        ]
        == 2.6
    )

    assert observation[
        "observation_id"
    ].startswith(
        "PERFORMANCE-OBSERVATION-"
    )


def test_cycle_mismatch_fails():
    with pytest.raises(
        ValueError,
        match=(
            "ANALYTICS_PIPELINE_CYCLE_MISMATCH"
        ),
    ):
        build_performance_observation(
            analytics_report=(
                analytics(
                    cycle_id="A"
                )
            ),
            pipeline_report=(
                pipeline(
                    cycle_id="B"
                )
            ),
        )
