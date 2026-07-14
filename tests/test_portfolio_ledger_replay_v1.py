from __future__ import annotations

from pathlib import Path

from atlas.investment.ledger import (
    FillEvent,
    LedgerSide,
    PortfolioLedger,
    read_jsonl,
    validate_hash_chain,
)


def fills():
    return (
        FillEvent(
            fill_id="fill-1",
            broker_order_id="broker-1",
            client_order_id="client-1",
            symbol="SOL-USD",
            side=LedgerSide.BUY,
            quantity=2,
            price=50,
            fee=1,
            timestamp="2026-01-01T00:00:00+00:00",
        ),
        FillEvent(
            fill_id="fill-2",
            broker_order_id="broker-2",
            client_order_id="client-2",
            symbol="SOL-USD",
            side=LedgerSide.SELL,
            quantity=1,
            price=60,
            fee=1,
            timestamp="2026-01-02T00:00:00+00:00",
        ),
    )


def test_replay_is_deterministic(tmp_path: Path) -> None:
    one = PortfolioLedger.replay(
        portfolio_id="portfolio",
        output_dir=tmp_path / "one",
        fills=fills(),
        starting_cash={"USD": 1000},
    )
    two = PortfolioLedger.replay(
        portfolio_id="portfolio",
        output_dir=tmp_path / "two",
        fills=fills(),
        starting_cash={"USD": 1000},
    )

    one_snapshot = one.snapshot(as_of="2026-01-03T00:00:00+00:00")
    two_snapshot = two.snapshot(as_of="2026-01-03T00:00:00+00:00")

    assert one_snapshot.cash == two_snapshot.cash
    assert one_snapshot.positions == two_snapshot.positions
    assert one_snapshot.equity == two_snapshot.equity


def test_fill_and_snapshot_histories_validate(tmp_path: Path) -> None:
    ledger = PortfolioLedger.replay(
        portfolio_id="portfolio",
        output_dir=tmp_path,
        fills=fills(),
        starting_cash={"USD": 1000},
    )
    ledger.snapshot()

    fill_records = read_jsonl(tmp_path / "fill_history.jsonl")
    snapshot_records = read_jsonl(tmp_path / "snapshot_history.jsonl")

    validate_hash_chain(fill_records)
    validate_hash_chain(snapshot_records)

    assert len(fill_records) == 2
    assert len(snapshot_records) == 1
