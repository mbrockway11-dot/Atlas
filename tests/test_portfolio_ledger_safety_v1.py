from __future__ import annotations

from pathlib import Path

import pytest

from atlas.investment.ledger import (
    DuplicateFillError,
    FillEvent,
    InsufficientPositionError,
    LedgerSide,
    LedgerValidationError,
    PortfolioLedger,
)


def make_fill(
    *,
    fill_id: str = "fill-1",
    side: LedgerSide = LedgerSide.BUY,
    quantity: float = 1,
    price: float = 100,
    paper_only: bool = True,
    live_execution: bool = False,
) -> FillEvent:
    return FillEvent(
        fill_id=fill_id,
        broker_order_id="broker-1",
        client_order_id="client-1",
        symbol="ETH-USD",
        side=side,
        quantity=quantity,
        price=price,
        fee=0,
        timestamp="2026-01-01T00:00:00+00:00",
        paper_only=paper_only,
        live_execution=live_execution,
    )


def test_duplicate_fill_is_rejected(tmp_path: Path) -> None:
    ledger = PortfolioLedger(
        portfolio_id="portfolio",
        output_dir=tmp_path,
    )
    fill = make_fill()
    ledger.apply_fill(fill)

    with pytest.raises(DuplicateFillError):
        ledger.apply_fill(fill)


def test_sell_cannot_exceed_long_position(tmp_path: Path) -> None:
    ledger = PortfolioLedger(
        portfolio_id="portfolio",
        output_dir=tmp_path,
    )

    with pytest.raises(InsufficientPositionError):
        ledger.apply_fill(
            make_fill(side=LedgerSide.SELL, quantity=1)
        )


def test_live_fill_is_rejected(tmp_path: Path) -> None:
    ledger = PortfolioLedger(
        portfolio_id="portfolio",
        output_dir=tmp_path,
    )

    with pytest.raises(LedgerValidationError, match="paper-only"):
        ledger.apply_fill(
            make_fill(paper_only=False, live_execution=True)
        )


@pytest.mark.parametrize("quantity,price", [(0, 100), (-1, 100), (1, 0), (1, -1)])
def test_invalid_fill_values_are_rejected(
    tmp_path: Path,
    quantity: float,
    price: float,
) -> None:
    ledger = PortfolioLedger(
        portfolio_id="portfolio",
        output_dir=tmp_path,
    )

    with pytest.raises(LedgerValidationError):
        ledger.apply_fill(
            make_fill(quantity=quantity, price=price)
        )
