"""Canonical contracts for the Hyperliquid copy-trading tracker.

All money and size values are parsed from Hyperliquid's string-encoded JSON
into floats once, at ingest, so the rest of the package never re-parses raw
API payloads. Every dataclass is frozen and slotted, with a ``to_dict`` that
round-trips to sorted JSON.

Sign convention, fixed here and relied on downstream: ``signed_size`` is
positive for a long and negative for a short, exactly as Hyperliquid's ``szi``
field encodes it. ``direction`` is the human-readable projection of that sign.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping


HYPER_COPYTRADE_CONTRACT_VERSION = "atlas.investment.hyper-copytrade.v1"

VALID_WINDOWS = (
    "day",
    "week",
    "month",
    "allTime",
)

VALID_METRICS = (
    "pnl",
    "roi",
)


def _finite(value: Any, *, name: str) -> float:
    """Parse a Hyperliquid string/number into a finite float."""
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite, got {value!r}.")
    return number


@dataclass(frozen=True, slots=True)
class WindowPerformance:
    """One trader's performance over one leaderboard window."""

    window: str
    pnl: float
    roi: float
    volume: float

    def __post_init__(self) -> None:
        if self.window not in VALID_WINDOWS:
            raise ValueError(f"Unknown window {self.window!r}.")

    def metric(self, metric: str) -> float:
        """Return the value of a rankable metric (``pnl`` or ``roi``)."""
        if metric == "pnl":
            return self.pnl
        if metric == "roi":
            return self.roi
        raise ValueError(f"Unknown metric {metric!r}.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "window": self.window,
            "pnl": self.pnl,
            "roi": self.roi,
            "volume": self.volume,
        }


@dataclass(frozen=True, slots=True)
class LeaderboardEntry:
    """One row of the Hyperliquid leaderboard, normalized.

    ``performances`` is keyed by window name so a ranker can select a window
    without re-scanning the raw list.
    """

    address: str
    account_value: float
    display_name: str
    performances: Mapping[str, WindowPerformance]

    def performance(self, window: str) -> WindowPerformance:
        try:
            return self.performances[window]
        except KeyError as error:
            raise ValueError(
                f"{self.address}: no performance for window {window!r}."
            ) from error

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "LeaderboardEntry":
        """Build an entry from one raw ``leaderboardRows`` element."""
        address = str(row["ethAddress"]).strip().lower()
        if not address.startswith("0x") or len(address) != 42:
            raise ValueError(f"Malformed address {address!r}.")

        performances: dict[str, WindowPerformance] = {}
        for window, stats in row.get("windowPerformances", ()):
            performances[str(window)] = WindowPerformance(
                window=str(window),
                pnl=_finite(stats["pnl"], name="pnl"),
                roi=_finite(stats["roi"], name="roi"),
                volume=_finite(stats["vlm"], name="vlm"),
            )

        display = row.get("displayName")
        return cls(
            address=address,
            account_value=_finite(row["accountValue"], name="accountValue"),
            display_name=str(display) if display else "",
            performances=performances,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "account_value": self.account_value,
            "display_name": self.display_name,
            "performances": {
                window: perf.to_dict()
                for window, perf in sorted(self.performances.items())
            },
        }


@dataclass(frozen=True, slots=True)
class TraderRanking:
    """A leaderboard entry with its rank under a specific policy."""

    rank: int
    address: str
    account_value: float
    display_name: str
    window: str
    metric: str
    metric_value: float
    pnl: float
    roi: float
    volume: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "rank": self.rank,
            "address": self.address,
            "account_value": self.account_value,
            "display_name": self.display_name,
            "window": self.window,
            "metric": self.metric,
            "metric_value": self.metric_value,
            "pnl": self.pnl,
            "roi": self.roi,
            "volume": self.volume,
        }


@dataclass(frozen=True, slots=True)
class LeaderPosition:
    """One open perpetual position held by a tracked wallet.

    ``signed_size`` follows Hyperliquid's ``szi``: positive long, negative
    short. ``position_value`` is the notional in USD; ``leverage`` is the
    position's leverage multiplier.
    """

    coin: str
    signed_size: float
    leverage: float
    entry_price: float
    position_value: float
    unrealized_pnl: float
    return_on_equity: float

    @property
    def direction(self) -> str:
        return "LONG" if self.signed_size >= 0 else "SHORT"

    @classmethod
    def from_asset_position(
        cls, asset_position: Mapping[str, Any]
    ) -> "LeaderPosition":
        position = asset_position["position"]
        leverage = position.get("leverage", {})
        return cls(
            coin=str(position["coin"]).strip().upper(),
            signed_size=_finite(position["szi"], name="szi"),
            leverage=_finite(leverage.get("value", 1), name="leverage"),
            entry_price=_finite(position.get("entryPx", 0.0), name="entryPx"),
            position_value=_finite(
                position.get("positionValue", 0.0), name="positionValue"
            ),
            unrealized_pnl=_finite(
                position.get("unrealizedPnl", 0.0), name="unrealizedPnl"
            ),
            return_on_equity=_finite(
                position.get("returnOnEquity", 0.0), name="returnOnEquity"
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "coin": self.coin,
            "signed_size": self.signed_size,
            "direction": self.direction,
            "leverage": self.leverage,
            "entry_price": self.entry_price,
            "position_value": self.position_value,
            "unrealized_pnl": self.unrealized_pnl,
            "return_on_equity": self.return_on_equity,
        }


@dataclass(frozen=True, slots=True)
class WalletState:
    """A tracked wallet's account value and open positions at a point in time."""

    address: str
    account_value: float
    total_notional_position: float
    total_margin_used: float
    positions: tuple[LeaderPosition, ...]

    @property
    def leverage_ratio(self) -> float:
        """Account-level notional-to-equity leverage, 0.0 if no equity."""
        if self.account_value <= 0.0:
            return 0.0
        return self.total_notional_position / self.account_value

    @classmethod
    def from_clearinghouse_state(
        cls, address: str, state: Mapping[str, Any]
    ) -> "WalletState":
        margin = state.get("marginSummary", {})
        positions = tuple(
            LeaderPosition.from_asset_position(asset_position)
            for asset_position in state.get("assetPositions", ())
        )
        return cls(
            address=str(address).strip().lower(),
            account_value=_finite(
                margin.get("accountValue", 0.0), name="accountValue"
            ),
            total_notional_position=_finite(
                margin.get("totalNtlPos", 0.0), name="totalNtlPos"
            ),
            total_margin_used=_finite(
                margin.get("totalMarginUsed", 0.0), name="totalMarginUsed"
            ),
            positions=positions,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "account_value": self.account_value,
            "total_notional_position": self.total_notional_position,
            "total_margin_used": self.total_margin_used,
            "leverage_ratio": self.leverage_ratio,
            "positions": [position.to_dict() for position in self.positions],
        }
