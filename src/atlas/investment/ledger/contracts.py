"""Canonical portfolio ledger contracts for Atlas G.21."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping

SCHEMA_VERSION = "g21.portfolio_ledger.v1"


class LedgerSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(frozen=True)
class FillEvent:
    fill_id: str
    broker_order_id: str
    client_order_id: str
    symbol: str
    side: LedgerSide
    quantity: float
    price: float
    fee: float
    timestamp: str
    currency: str = "USD"
    paper_only: bool = True
    live_execution: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PositionState:
    symbol: str
    quantity: float
    average_cost: float
    market_price: float
    market_value: float
    realized_pnl: float
    unrealized_pnl: float
    total_fees: float


@dataclass(frozen=True)
class CashState:
    currency: str
    balance: float


@dataclass(frozen=True)
class PortfolioSnapshot:
    portfolio_id: str
    as_of: str
    cash: tuple[CashState, ...]
    positions: tuple[PositionState, ...]
    gross_exposure: float
    net_exposure: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    total_fees: float
    record_hash: str
    previous_record_hash: str
    paper_only: bool = True
    live_execution: bool = False


__all__ = [
    "SCHEMA_VERSION",
    "CashState",
    "FillEvent",
    "LedgerSide",
    "PortfolioSnapshot",
    "PositionState",
]
