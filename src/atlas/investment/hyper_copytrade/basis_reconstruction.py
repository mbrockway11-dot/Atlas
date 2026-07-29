"""Average-cost-basis leg accounting over a Hyperliquid fill stream.

Round-trip reconstruction (``trade_reconstruction.py``) needs a position to
return to flat, which persistent and mixed-style traders rarely do -- so it
under-counts their activity badly. This module takes the other view: every
*closing fill* is one realized entry->exit observation, priced against the
position's running **average cost basis**, which is also how Hyperliquid itself
computes ``closedPnl``. A wallet that never flattens still emits one leg per
close, turning an "insufficient_data" round-trip wallet into hundreds of
learnable observations.

Ground truth is the fill's ``dir`` and ``closedPnl``, not inferred sign math.
The fill window routinely starts mid-position (the wallet held size before its
oldest visible fill), so accumulating a signed position from zero desynchronises
and mislabels closes as opens. Instead: ``Open Long``/``Open Short`` blend into
the basis; ``Close Long``/``Close Short`` and the flips ``Long > Short`` /
``Short > Long`` emit a realized leg carrying the fill's ``closedPnl`` verbatim.
Win/loss is therefore exact even when the opening leg predates the window.

``entry_observed`` records whether the closed size was fully opened *within* the
window. Only entry-observed legs have a real average-basis entry price and time;
legs closing a pre-window position are still emitted (their PnL is real) but
flagged, so entry-state feature extraction can exclude them rather than read a
fabricated basis.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Mapping

from atlas.investment.hyper_copytrade.trade_reconstruction import Fill


_ZERO_EPSILON = 1e-9


@dataclass(frozen=True, slots=True)
class RealizedLeg:
    """One realized close, priced against the position's average cost basis."""

    coin: str
    direction: str  # LONG or SHORT (the position being closed)
    entry_price: float
    entry_time_ms: int
    exit_price: float
    exit_time_ms: int
    size: float
    closed_pnl: float
    entry_observed: bool

    @property
    def holding_ms(self) -> int:
        return max(0, self.exit_time_ms - self.entry_time_ms)

    @property
    def is_win(self) -> bool:
        return self.closed_pnl > 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "coin": self.coin,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_time_ms": self.entry_time_ms,
            "exit_price": self.exit_price,
            "exit_time_ms": self.exit_time_ms,
            "holding_ms": self.holding_ms,
            "size": self.size,
            "closed_pnl": self.closed_pnl,
            "entry_observed": self.entry_observed,
            "is_win": self.is_win,
        }


class _Basis:
    """Observed average-cost basis for one coin's current position."""

    __slots__ = ("size", "price", "time_ms")

    def __init__(self) -> None:
        self.size = 0.0  # magnitude opened *within the window*
        self.price = 0.0
        self.time_ms = 0.0

    def add(self, size: float, price: float, time_ms: int) -> None:
        total = self.size + size
        if total <= _ZERO_EPSILON:
            return
        self.price = (self.size * self.price + size * price) / total
        self.time_ms = (self.size * self.time_ms + size * time_ms) / total
        self.size = total

    def reduce(self, size: float) -> float:
        """Reduce observed size by ``size``; return the observed portion removed."""
        removed = min(self.size, size)
        self.size = max(0.0, self.size - size)
        if self.size <= _ZERO_EPSILON:
            self.size = 0.0
        return removed

    def reset(self) -> None:
        self.size = 0.0
        self.price = 0.0
        self.time_ms = 0.0


def _closed_direction(dir_text: str) -> str:
    """The direction of the position a close/flip fill closes."""
    if dir_text.startswith("Close "):
        return "LONG" if dir_text.endswith("Long") else "SHORT"
    # Flip: "Long > Short" closes the Long; "Short > Long" closes the Short.
    return "LONG" if dir_text.startswith("Long") else "SHORT"


def reconstruct_realized_legs(
    raw_fills: Iterable[Mapping[str, Any]],
) -> list[RealizedLeg]:
    """Reconstruct realized entry->exit legs via dir-driven basis accounting."""
    by_coin: dict[str, list[Fill]] = defaultdict(list)
    for raw in raw_fills:
        try:
            fill = Fill.from_raw(raw)
        except (KeyError, ValueError, TypeError):
            continue
        by_coin[fill.coin].append(fill)

    legs: list[RealizedLeg] = []
    for coin, fills in by_coin.items():
        fills.sort(key=lambda f: (f.time_ms, f.dir))
        legs.extend(_legs_for_coin(coin, fills))

    legs.sort(key=lambda leg: leg.exit_time_ms)
    return legs


def _legs_for_coin(coin: str, fills: list[Fill]) -> list[RealizedLeg]:
    legs: list[RealizedLeg] = []
    basis = _Basis()

    for fill in fills:
        dir_text = fill.dir
        size = abs(fill.signed_size)

        if dir_text.startswith("Open "):
            basis.add(size, fill.price, fill.time_ms)
            continue

        is_close = dir_text.startswith("Close ")
        is_flip = ">" in dir_text
        if not (is_close or is_flip):
            continue  # spot / unknown dir: no perp leg

        direction = _closed_direction(dir_text)
        # A flip closes the whole current position and opens the remainder.
        close_size = basis.size if is_flip and basis.size > 0 else size
        entry_observed = basis.size + _ZERO_EPSILON >= close_size and basis.size > 0

        legs.append(
            RealizedLeg(
                coin=coin,
                direction=direction,
                entry_price=basis.price if entry_observed else 0.0,
                entry_time_ms=int(basis.time_ms) if entry_observed else fill.time_ms,
                exit_price=fill.price,
                exit_time_ms=fill.time_ms,
                size=close_size,
                closed_pnl=fill.closed_pnl,
                entry_observed=entry_observed,
            )
        )

        removed = basis.reduce(close_size)
        if is_flip:
            # Whatever the fill moved beyond the closed position opens anew.
            residual = size - removed
            basis.reset()
            if residual > _ZERO_EPSILON:
                basis.add(residual, fill.price, fill.time_ms)

    return legs
