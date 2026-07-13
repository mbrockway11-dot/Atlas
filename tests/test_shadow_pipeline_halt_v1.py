"""Failure-boundary tests for the G.12 shadow portfolio pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.investment.execution.shadow_pipeline import (
    run_shadow_pipeline,
)


def test_live_market_snapshot_is_rejected(
    tmp_path: Path,
):
    targets = (
        tmp_path / "targets.json"
    )

    snapshot = (
        tmp_path / "snapshot.json"
    )

    targets.write_text(
        json.dumps({
            "BTC-USD": 0.10,
            "CASH": 0.90,
        }),
        encoding="utf-8",
    )

    snapshot.write_text(
        json.dumps({
            "success": True,
            "snapshot_id": "LIVE",
            "reference_prices": {
                "BTC-USD": 50_000.0,
            },
            "contract": {
                "live_execution": True,
                "credentials_used": False,
            },
        }),
        encoding="utf-8",
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "LIVE_EXECUTION_FORBIDDEN"
        ),
    ):
        run_shadow_pipeline(
            targets_path=targets,
            snapshot_path=snapshot,
            account_path=(
                tmp_path / "account.json"
            ),
            intent_plan_path=(
                tmp_path / "intent.json"
            ),
            report_path=(
                tmp_path / "report.json"
            ),
            history_path=(
                tmp_path / "history.jsonl"
            ),
            checkpoint_path=(
                tmp_path / "checkpoint.json"
            ),
            write_outputs=False,
        )
