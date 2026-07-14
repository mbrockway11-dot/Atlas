from __future__ import annotations

from pathlib import Path

from atlas.investment.brokers import (
    BrokerAccountSnapshot,
    BrokerPosition,
)
from atlas.investment.ledger import (
    FillEvent,
    LedgerSide,
    PortfolioLedger,
    reconcile_snapshot,
)


def test_reconciliation_passes_when_states_match(tmp_path: Path) -> None:
    ledger = PortfolioLedger(
        portfolio_id="portfolio",
        output_dir=tmp_path,
        starting_cash={"USD": 1000},
    )
    ledger.apply_fill(
        FillEvent(
            fill_id="fill-1",
            broker_order_id="broker-1",
            client_order_id="client-1",
            symbol="BTC-USD",
            side=LedgerSide.BUY,
            quantity=1,
            price=100,
            fee=0,
            timestamp="2026-01-01T00:00:00+00:00",
        )
    )
    snapshot = ledger.snapshot()

    account = BrokerAccountSnapshot(
        account_id="paper",
        currency="USD",
        cash=900,
        equity=1000,
        buying_power=900,
        gross_exposure=100,
        net_exposure=100,
        paper_only=True,
        live_execution=False,
    )
    positions = [
        BrokerPosition(
            symbol="BTC-USD",
            quantity=1,
            average_price=100,
            market_value=100,
        )
    ]

    report = reconcile_snapshot(snapshot, account, positions)

    assert report.status == "PASS"
    assert report.issues == []


def test_reconciliation_detects_mismatch(tmp_path: Path) -> None:
    ledger = PortfolioLedger(
        portfolio_id="portfolio",
        output_dir=tmp_path,
        starting_cash={"USD": 1000},
    )
    snapshot = ledger.snapshot()

    account = BrokerAccountSnapshot(
        account_id="paper",
        currency="USD",
        cash=900,
        equity=900,
        buying_power=900,
        gross_exposure=0,
        net_exposure=0,
        paper_only=True,
        live_execution=False,
    )

    report = reconcile_snapshot(snapshot, account, [])

    assert report.status == "FAIL"
    assert any(issue["code"] == "CASH_MISMATCH" for issue in report.issues)
