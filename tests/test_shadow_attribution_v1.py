"""Tests for shadow portfolio valuation and attribution."""

from __future__ import annotations

from pathlib import Path

from atlas.investment.execution import (
    AccountSnapshot,
    PositionSnapshot,
)
from atlas.investment.execution.attribution import (
    build_shadow_attribution,
    value_account,
)


def test_account_mark_to_market():
    account = AccountSnapshot(
        cash=5_000.0,
        positions={
            "GLD": PositionSnapshot(
                asset="GLD",
                quantity=10.0,
                average_price=290.0,
                mark_price=290.0,
            )
        },
    )

    valuation = value_account(
        account,
        {
            "GLD": 300.0,
        },
    )

    assert valuation["success"]

    assert (
        valuation[
            "net_liquidation_value"
        ]
        == 8_000.0
    )

    assert (
        valuation["positions"][0][
            "unrealized_pnl"
        ]
        == 100.0
    )


def test_attribution_groups_asset_classes(
    tmp_path: Path,
):
    before = AccountSnapshot(
        cash=10_000.0
    )

    after = AccountSnapshot(
        cash=8_999.2,
        positions={
            "GLD": PositionSnapshot(
                asset="GLD",
                quantity=(
                    1000.0 / 300.0
                ),
                average_price=300.0,
                mark_price=300.0,
            )
        },
        realized_pnl=-0.8,
        daily_pnl=-0.8,
    )

    report = build_shadow_attribution(
        cycle_id="CYCLE-1",
        plan_id="PLAN-1",
        snapshot_id="SNAPSHOT-1",
        account_before=before,
        account_after=after,
        reference_prices={
            "GLD": 300.0,
        },
        execution_results=[],
        write_output=False,
    )

    assert report["success"]

    assert (
        report[
            "asset_class_attribution"
        ][0][
            "asset_class"
        ]
        == "METALS"
    )

    assert (
        report[
            "performance"
        ][
            "total_pnl"
        ]
        < 0
    )
