"""Place a trade's entry within its coin's recent price range.

The entry-state feature the research targets is *price vs recent range*: when a
winner opened, was price near the low of the recent range (a pullback / dip
entry) or near the high (a breakout / momentum entry)? This module answers that
by joining a leg's entry price and time against the coin's OHLCV candles.

``range_position`` is ``(entry - low) / (high - low)`` over the lookback window
of candles strictly *before* the entry:

    0.0  entered at the recent low        (deep pullback)
    1.0  entered at the recent high
    <0   entered below the prior low      (breakdown)
    >1   entered above the prior high     (breakout)

It is deliberately left unclamped -- a breakout beyond the prior range is real
information, not noise to be squashed to 1.0 -- and the aggregation uses medians
and quartiles, which absorb the occasional extreme without distortion. Only
candles that closed before the entry are used, so the feature never peeks at the
bar the entry itself occurred in.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from typing import Any, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class Candle:
    """One OHLCV candle."""

    open_time_ms: int
    high: float
    low: float
    close: float

    @classmethod
    def from_raw(cls, raw: Mapping[str, Any]) -> "Candle":
        return cls(
            open_time_ms=int(raw["t"]),
            high=float(raw["h"]),
            low=float(raw["l"]),
            close=float(raw["c"]),
        )


class CandleSeries:
    """A coin's candles, sorted by open time, queryable by a pre-entry window."""

    __slots__ = ("_candles", "_open_times")

    def __init__(self, candles: Sequence[Candle]) -> None:
        ordered = sorted(candles, key=lambda candle: candle.open_time_ms)
        self._candles = ordered
        self._open_times = [candle.open_time_ms for candle in ordered]

    def __len__(self) -> int:
        return len(self._candles)

    @classmethod
    def from_raw(cls, raw_candles: Sequence[Mapping[str, Any]]) -> "CandleSeries":
        parsed: list[Candle] = []
        for raw in raw_candles:
            try:
                parsed.append(Candle.from_raw(raw))
            except (KeyError, ValueError, TypeError):
                continue
        return cls(parsed)

    def range_before(
        self, time_ms: int, lookback_ms: int, *, minimum_candles: int = 3
    ) -> tuple[float, float] | None:
        """Return ``(low, high)`` over candles that opened in the lookback window.

        The window is ``[time_ms - lookback_ms, time_ms)`` -- strictly before
        ``time_ms`` -- so the entry's own bar never contributes. Returns
        ``None`` if fewer than ``minimum_candles`` candles fall in the window or
        the range is degenerate (high == low).
        """
        start = time_ms - lookback_ms
        left = bisect_left(self._open_times, start)
        right = bisect_left(self._open_times, time_ms)
        window = self._candles[left:right]
        if len(window) < minimum_candles:
            return None
        low = min(candle.low for candle in window)
        high = max(candle.high for candle in window)
        if high <= low:
            return None
        return (low, high)

    def range_position(
        self, price: float, time_ms: int, lookback_ms: int
    ) -> float | None:
        """Return where ``price`` sits in the recent range (see module docstring)."""
        bounds = self.range_before(time_ms, lookback_ms)
        if bounds is None:
            return None
        low, high = bounds
        return (price - low) / (high - low)

    def momentum_before(
        self, time_ms: int, lookback_ms: int, *, minimum_candles: int = 3
    ) -> float | None:
        """Return the close-to-close return over the window before ``time_ms``.

        Positive means price trended up into the entry, negative down. Uses only
        candles that opened before ``time_ms``, so the entry's own bar never
        contributes. ``None`` when the window is too thin or the base price is
        non-positive. This is a leading-momentum feature, independent of where
        the entry sits in the range.
        """
        start = time_ms - lookback_ms
        left = bisect_left(self._open_times, start)
        right = bisect_left(self._open_times, time_ms)
        window = self._candles[left:right]
        if len(window) < minimum_candles:
            return None
        base = window[0].close
        if base <= 0.0:
            return None
        return (window[-1].close - base) / base
