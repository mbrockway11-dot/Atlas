"""Characterize winners' entry and exit states into optimal-state distributions.

This is the payload: turn teachers' realized legs into the two features the
research targets -- price-vs-recent-range at entry, holding time at exit -- and
aggregate them into distributions, contrasting winning legs against losing ones.

The contrast is the whole point. A distribution of winners' entry range-position
means nothing on its own; it is informative only if winners entered *differently*
from losers (e.g. winners bought deeper pullbacks, or held a distinct window).
Where winners and losers overlap, there is no learnable edge on that axis, and
saying so is a result, not a failure.

Only winning, entry-observed legs feed the "optimal state" summary, because a
leg whose open predated the fill window has no real entry price to place in a
range. Legs whose coin lacks candle coverage contribute to holding-time stats
(which need no candles) but not to range-position stats; the counts are reported
separately so a thin range sample is never silently treated as a thick one.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from atlas.investment.hyper_copytrade.basis_reconstruction import RealizedLeg
from atlas.investment.hyper_copytrade.market_context import CandleSeries


DEFAULT_RANGE_LOOKBACK_HOURS = 24.0

# A coin -> its CandleSeries (or None if no coverage was fetched).
CandleProvider = Callable[[str], "CandleSeries | None"]


@dataclass(frozen=True, slots=True)
class LegFeature:
    """One realized leg with its entry-state and exit-state features.

    ``range_position`` and ``momentum`` are independent entry-state features
    computed from the same candles; either is ``None`` without coverage. New
    entry features are added here and selected by the strategy, so the OOS
    harness stays feature-agnostic.
    """

    coin: str
    direction: str
    is_win: bool
    closed_pnl: float
    holding_minutes: float
    range_position: float | None  # None if no candle coverage
    momentum: float | None = None  # leading return into entry; None if no coverage
    leg_return: float | None = None  # notional return of the leg; None if no exit px

    def to_dict(self) -> dict[str, Any]:
        return {
            "coin": self.coin,
            "direction": self.direction,
            "is_win": self.is_win,
            "closed_pnl": self.closed_pnl,
            "holding_minutes": self.holding_minutes,
            "range_position": self.range_position,
            "momentum": self.momentum,
            "leg_return": self.leg_return,
        }


@dataclass(frozen=True, slots=True)
class Distribution:
    """A robust summary of one metric's distribution."""

    count: int
    median: float
    p25: float
    p75: float
    mean: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": self.count,
            "median": self.median,
            "p25": self.p25,
            "p75": self.p75,
            "mean": self.mean,
        }


def _distribution(values: Sequence[float]) -> Distribution | None:
    ordered = sorted(values)
    if not ordered:
        return None
    quantiles = (
        statistics.quantiles(ordered, n=4) if len(ordered) >= 2 else [ordered[0]] * 3
    )
    return Distribution(
        count=len(ordered),
        median=statistics.median(ordered),
        p25=quantiles[0],
        p75=quantiles[2],
        mean=statistics.fmean(ordered),
    )


@dataclass(frozen=True, slots=True)
class OptimalStateReport:
    """Winner vs loser entry/exit-state distributions, the research output."""

    winning_legs: int
    losing_legs: int
    winner_range_position: Distribution | None
    loser_range_position: Distribution | None
    winner_hold_minutes: Distribution | None
    loser_hold_minutes: Distribution | None

    def to_dict(self) -> dict[str, Any]:
        def dump(dist: Distribution | None) -> dict[str, Any] | None:
            return dist.to_dict() if dist is not None else None

        return {
            "winning_legs": self.winning_legs,
            "losing_legs": self.losing_legs,
            "winner_range_position": dump(self.winner_range_position),
            "loser_range_position": dump(self.loser_range_position),
            "winner_hold_minutes": dump(self.winner_hold_minutes),
            "loser_hold_minutes": dump(self.loser_hold_minutes),
        }


def leg_features(
    legs: Sequence[RealizedLeg],
    candle_provider: CandleProvider,
    *,
    range_lookback_hours: float = DEFAULT_RANGE_LOOKBACK_HOURS,
) -> list[LegFeature]:
    """Compute entry/exit features for entry-observed legs.

    Legs whose entry was not observed within the window are skipped: they carry
    no real entry price to position in a range or to time a hold from.
    """
    lookback_ms = int(range_lookback_hours * 3_600_000)
    features: list[LegFeature] = []
    for leg in legs:
        if not leg.entry_observed:
            continue
        series = candle_provider(leg.coin)
        if series is not None:
            range_position = series.range_position(
                leg.entry_price, leg.entry_time_ms, lookback_ms
            )
            momentum = series.momentum_before(leg.entry_time_ms, lookback_ms)
        else:
            range_position = None
            momentum = None
        features.append(
            LegFeature(
                coin=leg.coin,
                direction=leg.direction,
                is_win=leg.is_win,
                closed_pnl=leg.closed_pnl,
                holding_minutes=leg.holding_ms / 60000.0,
                range_position=range_position,
                momentum=momentum,
                leg_return=_leg_return(leg),
            )
        )
    return features


def _leg_return(leg: RealizedLeg) -> float | None:
    """Notional return of the leg (signed by direction), or None without prices."""
    if leg.entry_price <= 0.0 or leg.exit_price <= 0.0:
        return None
    if leg.direction == "SHORT":
        return (leg.entry_price - leg.exit_price) / leg.entry_price
    return (leg.exit_price - leg.entry_price) / leg.entry_price


def summarize_states(features: Sequence[LegFeature]) -> OptimalStateReport:
    """Aggregate leg features into winner-vs-loser state distributions."""
    winners = [f for f in features if f.is_win]
    losers = [f for f in features if not f.is_win]

    def range_values(group: Sequence[LegFeature]) -> list[float]:
        return [f.range_position for f in group if f.range_position is not None]

    return OptimalStateReport(
        winning_legs=len(winners),
        losing_legs=len(losers),
        winner_range_position=_distribution(range_values(winners)),
        loser_range_position=_distribution(range_values(losers)),
        winner_hold_minutes=_distribution([f.holding_minutes for f in winners]),
        loser_hold_minutes=_distribution([f.holding_minutes for f in losers]),
    )


@dataclass(frozen=True, slots=True)
class PerTeacherStates:
    """Per-teacher medians summarized across teachers (each teacher counts once).

    The pooled view lets a hyperactive wallet with thousands of legs dominate.
    This collapses each teacher to their own median first, then summarizes those
    per-teacher medians -- so the reported gap reflects agreement *across
    traders*, not the volume of any one.
    """

    n_teachers: int
    winner_range_position: Distribution | None
    loser_range_position: Distribution | None
    winner_hold_minutes: Distribution | None
    loser_hold_minutes: Distribution | None

    def to_dict(self) -> dict[str, Any]:
        def dump(dist: Distribution | None) -> dict[str, Any] | None:
            return dist.to_dict() if dist is not None else None

        return {
            "n_teachers": self.n_teachers,
            "winner_range_position": dump(self.winner_range_position),
            "loser_range_position": dump(self.loser_range_position),
            "winner_hold_minutes": dump(self.winner_hold_minutes),
            "loser_hold_minutes": dump(self.loser_hold_minutes),
        }


def per_teacher_states(
    teacher_features: Mapping[str, Sequence[LegFeature]],
) -> PerTeacherStates:
    """Summarize each teacher's own winner/loser medians across teachers."""
    winner_range: list[float] = []
    loser_range: list[float] = []
    winner_hold: list[float] = []
    loser_hold: list[float] = []

    for feats in teacher_features.values():
        wins = [f for f in feats if f.is_win]
        losses = [f for f in feats if not f.is_win]
        win_range = [f.range_position for f in wins if f.range_position is not None]
        los_range = [f.range_position for f in losses if f.range_position is not None]
        if win_range:
            winner_range.append(statistics.median(win_range))
        if los_range:
            loser_range.append(statistics.median(los_range))
        if wins:
            winner_hold.append(statistics.median([f.holding_minutes for f in wins]))
        if losses:
            loser_hold.append(statistics.median([f.holding_minutes for f in losses]))

    return PerTeacherStates(
        n_teachers=len(teacher_features),
        winner_range_position=_distribution(winner_range),
        loser_range_position=_distribution(loser_range),
        winner_hold_minutes=_distribution(winner_hold),
        loser_hold_minutes=_distribution(loser_hold),
    )
