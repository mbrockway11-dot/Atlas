"""Canonical contracts for the Atlas paper execution plane."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Mapping


VALID_SIDES = {
    "BUY",
    "SELL",
}

VALID_ORDER_TYPES = {
    "MARKET",
    "LIMIT",
}

VALID_TIME_IN_FORCE = {
    "IOC",
    "GTC",
    "DAY",
}

TERMINAL_ORDER_STATES = {
    "FILLED",
    "CANCELLED",
    "REJECTED",
}


def utc_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def require_finite(
    value: float,
    name: str,
) -> float:
    number = float(value)

    if not math.isfinite(number):
        raise ValueError(
            f"{name} must be finite."
        )

    return number


@dataclass(frozen=True)
class OrderIntent:
    """One canonical request to change portfolio exposure."""

    asset: str
    side: str
    quantity: float
    reference_price: float
    strategy_id: str
    evidence_id: str
    order_type: str = "MARKET"
    limit_price: float | None = None
    time_in_force: str = "IOC"
    maximum_slippage_bps: float = 25.0
    reduce_only: bool = False
    expires_at: str = ""
    created_at: str = ""
    intent_id: str = ""

    def __post_init__(self) -> None:
        asset = self.asset.strip().upper()
        side = self.side.strip().upper()
        order_type = (
            self.order_type
            .strip()
            .upper()
        )
        time_in_force = (
            self.time_in_force
            .strip()
            .upper()
        )

        quantity = require_finite(
            self.quantity,
            "quantity",
        )

        reference_price = require_finite(
            self.reference_price,
            "reference_price",
        )

        slippage = require_finite(
            self.maximum_slippage_bps,
            "maximum_slippage_bps",
        )

        if not asset:
            raise ValueError(
                "asset is required."
            )

        if side not in VALID_SIDES:
            raise ValueError(
                f"Unsupported side: {side}"
            )

        if order_type not in (
            VALID_ORDER_TYPES
        ):
            raise ValueError(
                "Unsupported order type: "
                f"{order_type}"
            )

        if time_in_force not in (
            VALID_TIME_IN_FORCE
        ):
            raise ValueError(
                "Unsupported time in force: "
                f"{time_in_force}"
            )

        if quantity <= 0:
            raise ValueError(
                "quantity must be positive."
            )

        if reference_price <= 0:
            raise ValueError(
                "reference_price must be positive."
            )

        if slippage < 0:
            raise ValueError(
                "maximum_slippage_bps cannot be negative."
            )

        if (
            order_type == "LIMIT"
            and (
                self.limit_price is None
                or require_finite(
                    self.limit_price,
                    "limit_price",
                )
                <= 0
            )
        ):
            raise ValueError(
                "LIMIT orders require a positive limit_price."
            )

        if not self.strategy_id.strip():
            raise ValueError(
                "strategy_id is required."
            )

        if not self.evidence_id.strip():
            raise ValueError(
                "evidence_id is required."
            )

        created_at = (
            self.created_at
            or utc_now()
        )

        object.__setattr__(
            self,
            "asset",
            asset,
        )
        object.__setattr__(
            self,
            "side",
            side,
        )
        object.__setattr__(
            self,
            "order_type",
            order_type,
        )
        object.__setattr__(
            self,
            "time_in_force",
            time_in_force,
        )
        object.__setattr__(
            self,
            "quantity",
            quantity,
        )
        object.__setattr__(
            self,
            "reference_price",
            reference_price,
        )
        object.__setattr__(
            self,
            "maximum_slippage_bps",
            slippage,
        )
        object.__setattr__(
            self,
            "created_at",
            created_at,
        )

        if not self.intent_id:
            object.__setattr__(
                self,
                "intent_id",
                build_intent_id(self),
            )

    @property
    def notional(self) -> float:
        return (
            self.quantity
            * self.reference_price
        )

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["notional"] = (
            self.notional
        )
        return result


@dataclass(frozen=True)
class RiskLimits:
    """Hard paper-execution risk limits."""

    maximum_order_notional: float = 5_000.0
    maximum_asset_notional: float = 10_000.0
    maximum_gross_exposure: float = 20_000.0
    maximum_daily_loss: float = 500.0
    maximum_leverage: float = 1.0
    maximum_slippage_bps: float = 25.0
    allow_short_positions: bool = False

    def __post_init__(self) -> None:
        for name in (
            "maximum_order_notional",
            "maximum_asset_notional",
            "maximum_gross_exposure",
            "maximum_daily_loss",
            "maximum_leverage",
            "maximum_slippage_bps",
        ):
            value = require_finite(
                getattr(self, name),
                name,
            )

            if value < 0:
                raise ValueError(
                    f"{name} cannot be negative."
                )


@dataclass(frozen=True)
class PositionSnapshot:
    """One authoritative paper position."""

    asset: str
    quantity: float
    average_price: float
    mark_price: float

    @property
    def market_value(self) -> float:
        return (
            self.quantity
            * self.mark_price
        )

    @property
    def absolute_notional(self) -> float:
        return abs(
            self.market_value
        )

    @property
    def unrealized_pnl(self) -> float:
        return (
            self.mark_price
            - self.average_price
        ) * self.quantity

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["market_value"] = (
            self.market_value
        )
        result[
            "absolute_notional"
        ] = self.absolute_notional
        result["unrealized_pnl"] = (
            self.unrealized_pnl
        )
        return result


@dataclass(frozen=True)
class AccountSnapshot:
    """Current paper cash, positions, and loss state."""

    cash: float
    positions: Mapping[
        str,
        PositionSnapshot,
    ] = field(
        default_factory=dict
    )
    realized_pnl: float = 0.0
    daily_pnl: float = 0.0

    @property
    def gross_exposure(self) -> float:
        return sum(
            position.absolute_notional
            for position
            in self.positions.values()
        )

    @property
    def net_liquidation_value(self) -> float:
        return (
            self.cash
            + sum(
                position.market_value
                for position
                in self.positions.values()
            )
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "cash": float(
                self.cash
            ),
            "realized_pnl": float(
                self.realized_pnl
            ),
            "daily_pnl": float(
                self.daily_pnl
            ),
            "gross_exposure": (
                self.gross_exposure
            ),
            "net_liquidation_value": (
                self.net_liquidation_value
            ),
            "positions": {
                asset: position.to_dict()
                for asset, position
                in self.positions.items()
            },
        }


@dataclass(frozen=True)
class RiskDecision:
    """Deterministic pre-trade risk decision."""

    approved: bool
    reason_codes: tuple[str, ...]
    intent_id: str
    order_notional: float
    projected_asset_notional: float
    projected_gross_exposure: float
    projected_cash: float
    evaluated_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrderRecord:
    """Paper broker order lifecycle record."""

    order_id: str
    intent_id: str
    asset: str
    side: str
    requested_quantity: float
    filled_quantity: float
    remaining_quantity: float
    status: str
    submitted_at: str
    completed_at: str
    average_fill_price: float
    fee_paid: float
    rejection_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FillRecord:
    """One deterministic paper fill."""

    fill_id: str
    order_id: str
    intent_id: str
    asset: str
    side: str
    quantity: float
    price: float
    notional: float
    fee: float
    slippage_bps: float
    filled_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_intent_id(
    intent: OrderIntent,
) -> str:
    payload = {
        "asset": intent.asset,
        "side": intent.side,
        "quantity": intent.quantity,
        "reference_price": (
            intent.reference_price
        ),
        "strategy_id": (
            intent.strategy_id
        ),
        "evidence_id": (
            intent.evidence_id
        ),
        "order_type": (
            intent.order_type
        ),
        "limit_price": (
            intent.limit_price
        ),
        "time_in_force": (
            intent.time_in_force
        ),
        "maximum_slippage_bps": (
            intent.maximum_slippage_bps
        ),
        "reduce_only": (
            intent.reduce_only
        ),
        "expires_at": (
            intent.expires_at
        ),
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    return (
        "INTENT-"
        + hashlib.sha256(
            encoded
        ).hexdigest()[:24]
    )


def build_record_id(
    prefix: str,
    payload: Mapping[str, Any],
) -> str:
    encoded = json.dumps(
        dict(payload),
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return (
        prefix
        + "-"
        + hashlib.sha256(
            encoded
        ).hexdigest()[:24]
    )
