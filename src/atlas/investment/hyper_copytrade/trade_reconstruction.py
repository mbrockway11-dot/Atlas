"""Reconstruct round-trip trades from a Hyperliquid fill stream.

A fill is one execution; a *trade* is the full round trip from a position
leaving flat (first open) until it returns to flat (final close). The
leaderboard and clearinghouse tell you a wallet's *current* book; this module
recovers its *history* -- every entry and exit -- which is what lets us scan
winners' opening trades and their closing conditions.

Per coin, fills are walked in time order while tracking the signed running
position. ``side`` gives the sign (``B`` buy = +, ``A`` sell = -); each fill's
``startPosition`` is the signed position immediately before it. A trade opens
when the position leaves zero and closes when it returns to zero. A direction
flip (position crosses zero in one fill) closes the current trade and opens a
new one in the opposite direction.

Realized PnL is taken directly from Hyperliquid's ``closedPnl`` on closing
legs -- authoritative and already net of the venue's accounting -- rather than
re-derived from entry/exit prices, so a trade's win/loss label is exact.

Entry and exit prices are size-weighted across a trade's opening and closing
legs respectively, and are descriptive only; they never override ``closedPnl``.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


def _num(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"Non-finite fill value {value!r}.")
    return number


@dataclass(frozen=True, slots=True)
class Fill:
    """One normalized fill (execution leg)."""

    coin: str
    time_ms: int
    price: float
    signed_size: float
    start_position: float
    dir: str
    closed_pnl: float
    fee: float

    @property
    def is_open(self) -> bool:
        return self.dir.startswith("Open")

    @property
    def is_close(self) -> bool:
        return self.dir.startswith("Close")

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "Fill":
        size = _num(raw["sz"])
        side = str(raw["side"]).strip().upper()
        if side not in ("B", "A"):
            raise ValueError(f"Unknown fill side {side!r}.")
        signed = size if side == "B" else -size
        return cls(
            coin=str(raw["coin"]).strip().upper(),
            time_ms=int(raw["time"]),
            price=_num(raw["px"]),
            signed_size=signed,
            start_position=_num(raw.get("startPosition", 0.0)),
            dir=str(raw.get("dir", "")).strip(),
            closed_pnl=_num(raw.get("closedPnl", 0.0)),
            fee=_num(raw.get("fee", 0.0)),
        )


@dataclass(frozen=True, slots=True)
class ReconstructedTrade:
    """One round-trip trade recovered from a wallet's fills."""

    coin: str
    direction: str  # LONG or SHORT
    entry_time_ms: int
    exit_time_ms: int
    entry_price: float
    exit_price: float
    peak_size: float
    realized_pnl: float
    total_fees: float
    leg_count: int
    is_closed: bool

    @property
    def duration_ms(self) -> int:
        return max(0, self.exit_time_ms - self.entry_time_ms)

    @property
    def is_win(self) -> bool:
        return self.is_closed and self.realized_pnl > 0.0

    @property
    def net_pnl(self) -> float:
        return self.realized_pnl - self.total_fees

    def to_dict(self) -> dict[str, Any]:
        return {
            "coin": self.coin,
            "direction": self.direction,
            "entry_time_ms": self.entry_time_ms,
            "exit_time_ms": self.exit_time_ms,
            "duration_ms": self.duration_ms,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "peak_size": self.peak_size,
            "realized_pnl": self.realized_pnl,
            "total_fees": self.total_fees,
            "net_pnl": self.net_pnl,
            "leg_count": self.leg_count,
            "is_closed": self.is_closed,
            "is_win": self.is_win,
        }


class _OpenTrade:
    """Mutable accumulator for a trade still being built."""

    __slots__ = (
        "coin", "direction", "entry_time_ms", "entry_notional", "entry_size",
        "exit_notional", "exit_size", "exit_time_ms", "peak_size",
        "realized_pnl", "total_fees", "leg_count",
    )

    def __init__(self, coin: str, direction: str, time_ms: int) -> None:
        self.coin = coin
        self.direction = direction
        self.entry_time_ms = time_ms
        self.entry_notional = 0.0
        self.entry_size = 0.0
        self.exit_notional = 0.0
        self.exit_size = 0.0
        self.exit_time_ms = time_ms
        self.peak_size = 0.0
        self.realized_pnl = 0.0
        self.total_fees = 0.0
        self.leg_count = 0

    def add_open(self, price: float, size: float, time_ms: int) -> None:
        self.entry_notional += price * size
        self.entry_size += size
        self.leg_count += 1

    def add_close(
        self, price: float, size: float, closed_pnl: float, time_ms: int
    ) -> None:
        self.exit_notional += price * size
        self.exit_size += size
        self.exit_time_ms = time_ms
        self.realized_pnl += closed_pnl
        self.leg_count += 1

    def observe_position(self, position: float) -> None:
        self.peak_size = max(self.peak_size, abs(position))

    def finalize(self, is_closed: bool) -> ReconstructedTrade:
        entry_price = (
            self.entry_notional / self.entry_size if self.entry_size else 0.0
        )
        exit_price = (
            self.exit_notional / self.exit_size if self.exit_size else 0.0
        )
        return ReconstructedTrade(
            coin=self.coin,
            direction=self.direction,
            entry_time_ms=self.entry_time_ms,
            exit_time_ms=self.exit_time_ms,
            entry_price=entry_price,
            exit_price=exit_price,
            peak_size=self.peak_size,
            realized_pnl=self.realized_pnl,
            total_fees=self.total_fees,
            leg_count=self.leg_count,
            is_closed=is_closed,
        )


_ZERO_EPSILON = 1e-9


def reconstruct_trades(
    raw_fills: Iterable[Mapping[str, Any]],
) -> list[ReconstructedTrade]:
    """Reconstruct round-trip trades from raw Hyperliquid fills.

    Fills may arrive in any order (the API returns newest-first); they are
    grouped by coin and sorted ascending by time. A still-open trade at the end
    of the stream is returned with ``is_closed=False`` so callers can exclude
    unfinished trades from win/loss statistics.
    """
    by_coin: dict[str, list[Fill]] = defaultdict(list)
    for raw in raw_fills:
        try:
            fill = Fill.from_raw(raw)
        except (KeyError, ValueError, TypeError):
            continue
        by_coin[fill.coin].append(fill)

    trades: list[ReconstructedTrade] = []
    for coin, fills in by_coin.items():
        fills.sort(key=lambda f: (f.time_ms, f.dir))
        trades.extend(_reconstruct_coin(coin, fills))

    trades.sort(key=lambda t: t.entry_time_ms)
    return trades


def _reconstruct_coin(coin: str, fills: list[Fill]) -> list[ReconstructedTrade]:
    trades: list[ReconstructedTrade] = []
    current: _OpenTrade | None = None
    position = 0.0

    for fill in fills:
        position_before = position
        position_after = position_before + fill.signed_size

        # Open a trade when leaving flat.
        if current is None and abs(position_before) <= _ZERO_EPSILON:
            direction = "LONG" if fill.signed_size >= 0 else "SHORT"
            current = _OpenTrade(coin, direction, fill.time_ms)

        crossed_zero = (
            position_before * position_after < 0.0
            and abs(position_before) > _ZERO_EPSILON
        )

        if current is not None:
            current.total_fees += fill.fee
            if fill.signed_size * _direction_sign(current.direction) > 0:
                current.add_open(fill.price, abs(fill.signed_size), fill.time_ms)
            else:
                current.add_close(
                    fill.price, abs(fill.signed_size), fill.closed_pnl, fill.time_ms
                )
            current.observe_position(position_after)

        # Trade returns to flat -> close it.
        if current is not None and abs(position_after) <= _ZERO_EPSILON:
            trades.append(current.finalize(is_closed=True))
            current = None
        # Direction flip in a single fill -> close, then open the residual.
        elif crossed_zero and current is not None:
            trades.append(current.finalize(is_closed=True))
            direction = "LONG" if position_after >= 0 else "SHORT"
            current = _OpenTrade(coin, direction, fill.time_ms)
            current.add_open(fill.price, abs(position_after), fill.time_ms)
            current.observe_position(position_after)

        position = position_after

    if current is not None:
        trades.append(current.finalize(is_closed=False))
    return trades


def _direction_sign(direction: str) -> float:
    return 1.0 if direction == "LONG" else -1.0
