"""Tests for persistent paper account state."""

from __future__ import annotations

from pathlib import Path

from atlas.investment.execution import (
    AccountSnapshot,
    PositionSnapshot,
)
from atlas.investment.execution.account_store import (
    load_paper_account,
    write_paper_account,
)


def test_missing_account_uses_initial_cash(
    tmp_path: Path,
):
    account = load_paper_account(
        path=tmp_path / "account.json",
        initial_cash=25_000.0,
    )

    assert account.cash == 25_000.0
    assert account.positions == {}


def test_account_round_trip(
    tmp_path: Path,
):
    path = tmp_path / "account.json"

    original = AccountSnapshot(
        cash=9_000.0,
        positions={
            "BTC-USD": PositionSnapshot(
                asset="BTC-USD",
                quantity=0.02,
                average_price=50_000.0,
                mark_price=51_000.0,
            )
        },
        realized_pnl=25.0,
        daily_pnl=10.0,
    )

    write_paper_account(
        original,
        path=path,
        source_execution_id="EXEC-1",
    )

    loaded = load_paper_account(
        path=path
    )

    assert (
        loaded.to_dict()
        == original.to_dict()
    )
