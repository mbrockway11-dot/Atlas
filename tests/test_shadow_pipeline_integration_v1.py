"""Integration test for market snapshot ? intent plan ? paper execution."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.execution import (
    RebalancePolicy,
    RiskLimits,
)
from atlas.investment.execution.shadow_pipeline import (
    run_shadow_pipeline,
)


def test_shadow_pipeline_builds_and_executes(
    tmp_path: Path,
    monkeypatch,
):
    targets_path = (
        tmp_path / "targets.json"
    )

    snapshot_path = (
        tmp_path / "snapshot.json"
    )

    targets_path.write_text(
        json.dumps({
            "portfolio_rows": [
                {
                    "asset": "BTC-USD",
                    "weight": 0.10,
                },
                {
                    "asset": "GLD",
                    "weight": 0.10,
                },
                {
                    "asset": "CASH",
                    "weight": 0.80,
                },
            ]
        }),
        encoding="utf-8",
    )

    snapshot_path.write_text(
        json.dumps({
            "success": True,
            "snapshot_id": "SNAPSHOT-1",
            "reference_prices": {
                "BTC-USD": 50_000.0,
                "GLD": 300.0,
            },
            "counts": {
                "resolved": 2,
            },
            "contract": {
                "provider_neutral": True,
                "broker_independent": True,
                "credentials_used": False,
                "live_execution": False,
            },
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "atlas.investment.execution."
        "shadow_pipeline."
        "validate_market_data_audit",
        lambda: {
            "valid": True,
            "errors": [],
        },
    )

    monkeypatch.setattr(
        "atlas.investment.execution."
        "shadow_loop."
        "validate_execution_provenance",
        lambda: {
            "valid": True,
            "errors": [],
        },
    )

    report = run_shadow_pipeline(
        targets_path=targets_path,
        snapshot_path=snapshot_path,
        account_path=(
            tmp_path / "account.json"
        ),
        intent_plan_path=(
            tmp_path / "intent_plan.json"
        ),
        report_path=(
            tmp_path / "pipeline.json"
        ),
        history_path=(
            tmp_path / "history.jsonl"
        ),
        checkpoint_path=(
            tmp_path / "checkpoint.json"
        ),
        initial_cash=10_000.0,
        policy=RebalancePolicy(
            minimum_cash_weight=0.80,
            maximum_total_turnover=0.20,
        ),
        limits=RiskLimits(
            maximum_order_notional=(
                2_000.0
            ),
            maximum_asset_notional=(
                2_000.0
            ),
            maximum_gross_exposure=(
                4_000.0
            ),
        ),
        resume=False,
        write_outputs=True,
    )

    assert report["success"]

    assert (
        report["status"]
        == "COMPLETED"
    )

    assert (
        report[
            "intent_plan"
        ][
            "counts"
        ][
            "generated_intents"
        ]
        == 2
    )

    assert (
        report[
            "shadow_cycle"
        ][
            "counts"
        ][
            "completed_total"
        ]
        == 2
    )

    assert (
        report[
            "contract"
        ][
            "paper_only"
        ]
    )
