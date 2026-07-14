from __future__ import annotations

from pathlib import Path

from atlas.investment.ledger import (
    FillEvent,
    LedgerSide,
    PortfolioLedger,
)


def fill(
    fill_id: str,
    side: LedgerSide,
    quantity: float,
    price: float,
    fee: float = 0.0,
) -> FillEvent:
    return FillEvent(
        fill_id=fill_id,
        broker_order_id=f"broker-{fill_id}",
        client_order_id=f"client-{fill_id}",
        symbol="BTC-USD",
        side=side,
        quantity=quantity,
        price=price,
        fee=fee,
        timestamp="2026-01-01T00:00:00+00:00",
    )


def test_buy_sell_cost_basis_and_realized_pnl(tmp_path: Path) -> None:
    ledger = PortfolioLedger(
        portfolio_id="portfolio-1",
        output_dir=tmp_path,
        starting_cash={"USD": 100000},
    )

    first = ledger.apply_fill(fill("1", LedgerSide.BUY, 1, 100, 1))
    second = ledger.apply_fill(fill("2", LedgerSide.BUY, 1, 120, 1))
    final = ledger.apply_fill(fill("3", LedgerSide.SELL, 1, 130, 1))

    assert round(first.average_cost, 6) == 101.0
    assert round(second.average_cost, 6) == 111.0
    assert final.quantity == 1
    assert round(final.realized_pnl, 6) == 18.0

    snapshot = ledger.snapshot()
    assert snapshot.paper_only is True
    assert snapshot.live_execution is False
    assert snapshot.total_fees == 3.0


def test_mark_to_market_updates_unrealized_pnl(tmp_path: Path) -> None:
    ledger = PortfolioLedger(
        portfolio_id="portfolio-2",
        output_dir=tmp_path,
        starting_cash={"USD": 1000},
    )
    ledger.apply_fill(fill("1", LedgerSide.BUY, 2, 100))
    ledger.mark_prices({"BTC-USD": 125})

    position = ledger.positions()[0]

    assert position.market_price == 125
    assert position.unrealized_pnl == 50
