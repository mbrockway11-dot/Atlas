"""Canonical broker contracts for Atlas G.18.

These contracts are provider-neutral and paper-only by default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


SCHEMA_VERSION = "g18.broker.contracts.v1"


class BrokerSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class BrokerOrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class BrokerTimeInForce(str, Enum):
    DAY = "DAY"
    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


class BrokerOrderStatus(str, Enum):
    NEW = "NEW"
    ACCEPTED = "ACCEPTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    REPLACED = "REPLACED"


class BrokerHealthState(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class BrokerCapabilities:
    provider: str
    paper_only: bool = True
    live_trading: bool = False
    supports_market_orders: bool = True
    supports_limit_orders: bool = True
    supports_stop_orders: bool = False
    supports_stop_limit_orders: bool = False
    supports_cancel: bool = True
    supports_replace: bool = True
    supports_fractional_quantity: bool = True
    supports_shorting: bool = False
    supported_asset_classes: tuple[str, ...] = ("GENERIC",)
    supported_time_in_force: tuple[str, ...] = (
        BrokerTimeInForce.DAY.value,
        BrokerTimeInForce.GTC.value,
    )


@dataclass(frozen=True)
class BrokerOrderRequest:
    client_order_id: str
    symbol: str
    side: BrokerSide
    order_type: BrokerOrderType
    quantity: float
    time_in_force: BrokerTimeInForce = BrokerTimeInForce.DAY
    limit_price: float | None = None
    stop_price: float | None = None
    reduce_only: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrokerOrderResponse:
    broker_order_id: str
    client_order_id: str
    symbol: str
    side: BrokerSide
    order_type: BrokerOrderType
    quantity: float
    filled_quantity: float
    status: BrokerOrderStatus
    average_fill_price: float | None
    submitted_at: str
    updated_at: str
    paper_only: bool = True
    live_execution: bool = False
    raw: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BrokerPosition:
    symbol: str
    quantity: float
    average_price: float
    market_value: float
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass(frozen=True)
class BrokerAccountSnapshot:
    account_id: str
    currency: str
    cash: float
    equity: float
    buying_power: float
    gross_exposure: float
    net_exposure: float
    paper_only: bool = True
    live_execution: bool = False


@dataclass(frozen=True)
class BrokerExecutionReport:
    broker_order_id: str
    client_order_id: str
    symbol: str
    status: BrokerOrderStatus
    filled_quantity: float
    remaining_quantity: float
    average_fill_price: float | None
    fees: float
    timestamp: str
    paper_only: bool = True
    live_execution: bool = False


@dataclass(frozen=True)
class BrokerHealthStatus:
    provider: str
    state: BrokerHealthState
    checked_at: str
    message: str = ""
    latency_ms: int = 0
    paper_only: bool = True
    live_execution: bool = False


__all__ = [
    "SCHEMA_VERSION",
    "BrokerAccountSnapshot",
    "BrokerCapabilities",
    "BrokerExecutionReport",
    "BrokerHealthState",
    "BrokerHealthStatus",
    "BrokerOrderRequest",
    "BrokerOrderResponse",
    "BrokerOrderStatus",
    "BrokerOrderType",
    "BrokerPosition",
    "BrokerSide",
    "BrokerTimeInForce",
]
