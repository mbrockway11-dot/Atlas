"""Shared teacher-legs -> leg-features pipeline (candle join).

Both the descriptive analysis and the out-of-sample evaluation need the same
step: given each teacher's realized legs, fetch the coins' candles (once, span-
clamped to the venue's ~5000-candle cap) and compute per-leg entry/exit
features. Keeping it in one place means the registry-backed and live-scan paths
produce identical features, so a result never depends on which entry point
computed it.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from atlas.investment.hyper_copytrade.basis_reconstruction import RealizedLeg
from atlas.investment.hyper_copytrade.client import (
    HyperliquidClientError,
    HyperliquidReadClient,
)
from atlas.investment.hyper_copytrade.entry_exit_states import (
    LegFeature,
    leg_features,
)
from atlas.investment.hyper_copytrade.market_context import CandleSeries


# Hyperliquid returns at most ~5000 candles per request; at 1h that is ~208 days.
CANDLE_CAP_MS = 4900 * 3_600_000


def features_by_teacher(
    client: HyperliquidReadClient,
    teacher_legs: Mapping[str, Sequence[RealizedLeg]],
    *,
    range_lookback_hours: float = 24.0,
    candle_interval: str = "1h",
    progress: bool = False,
) -> dict[str, list[LegFeature]]:
    """Fetch candles per coin and compute per-teacher leg features.

    Candle spans are clamped to the venue cap ending at each coin's most recent
    exit, so legs with entries older than the covered window get no range
    position (rather than the fetch truncating and starving every leg).
    """
    lookback_ms = int(range_lookback_hours * 3_600_000)

    spans: dict[str, tuple[int, int]] = {}
    for legs in teacher_legs.values():
        for leg in legs:
            if not leg.entry_observed:
                continue
            lo, hi = leg.entry_time_ms - lookback_ms, leg.exit_time_ms
            prev = spans.get(leg.coin)
            spans[leg.coin] = (
                (min(prev[0], lo), max(prev[1], hi)) if prev else (lo, hi)
            )
    spans = {
        coin: (max(lo, hi - CANDLE_CAP_MS), hi) for coin, (lo, hi) in spans.items()
    }

    if progress:
        print(f"  Fetching {candle_interval} candles for {len(spans)} coins...")
    candles: dict[str, CandleSeries] = {}
    for coin, (start, end) in spans.items():
        try:
            candles[coin] = CandleSeries.from_raw(
                client.fetch_candles(coin, candle_interval, start, end)
            )
        except HyperliquidClientError:
            continue

    return {
        address: leg_features(
            legs, candles.get, range_lookback_hours=range_lookback_hours
        )
        for address, legs in teacher_legs.items()
    }
