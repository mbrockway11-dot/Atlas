"""Tests for append-only G.14 performance ledger behavior."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.execution.performance_ledger import (
    append_performance_observation,
    build_observation_id,
    validate_performance_ledger,
)


def observation(
    *,
    analytics_id: str,
    cycle_id: str,
):
    result = {
        "version": "1.0.0",
        "analytics_id": analytics_id,
        "pipeline_id": (
            "PIPELINE-"
            + cycle_id
        ),
        "cycle_id": cycle_id,
        "plan_id": (
            "PLAN-"
            + cycle_id
        ),
        "snapshot_id": "SNAPSHOT-1",
        "observed_at": (
            "2026-07-13T16:00:00+00:00"
        ),
        "starting_equity": 10000.0,
        "ending_equity": 9999.0,
        "cycle_pnl": -1.0,
        "cycle_return": -0.0001,
        "fee_cost": 0.6,
        "slippage_cost": 0.4,
        "total_execution_cost": 1.0,
        "execution_cost_bps": 1.0,
        "gross_fill_notional": 1000.0,
        "turnover_ratio": 0.1,
        "ending_cash_weight": 0.9,
        "ending_gross_exposure_ratio": 0.1,
        "order_count": 1,
        "filled_order_count": 1,
        "full_fill_rate": 1.0,
        "rejection_rate": 0.0,
        "reconciliation_success_rate": 1.0,
        "weighted_slippage_bps": 4.0,
        "weighted_implementation_shortfall_bps": 10.0,
        "average_time_to_completion_ms": 0.1,
        "realized_pnl_change": -0.6,
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


def test_append_and_duplicate_protection(
    tmp_path: Path,
):
    path = tmp_path / "ledger.jsonl"

    first = observation(
        analytics_id="A-1",
        cycle_id="C-1",
    )

    result_one = (
        append_performance_observation(
            first,
            path=path,
        )
    )

    result_two = (
        append_performance_observation(
            first,
            path=path,
        )
    )

    assert result_one["appended"]
    assert not result_two["appended"]
    assert result_two["duplicate"]

    validation = (
        validate_performance_ledger(
            path=path
        )
    )

    assert validation["valid"]


def test_tampering_is_detected(
    tmp_path: Path,
):
    path = tmp_path / "ledger.jsonl"

    append_performance_observation(
        observation(
            analytics_id="A-1",
            cycle_id="C-1",
        ),
        path=path,
    )

    record = json.loads(
        path.read_text(
            encoding="utf-8"
        ).strip()
    )

    record["cycle_pnl"] = 999.0

    path.write_text(
        json.dumps(record)
        + "\n",
        encoding="utf-8",
    )

    validation = (
        validate_performance_ledger(
            path=path
        )
    )

    assert not validation["valid"]

    assert any(
        value.startswith(
            "RECORD_HASH_MISMATCH"
        )
        for value
        in validation["errors"]
    )
