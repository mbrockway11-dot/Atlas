"""Classify a wallet's trading style, to keep only learnable teachers.

The top-PnL leaderboard is dominated by HFT / market-making wallets whose
"entry" is a blur of hundreds of scalps around a shifting average. For learning
*price-vs-range entries* and *holding-time exits*, those wallets teach nothing:
their edge is microstructure, not timing. A discrete swing trader -- one who
takes a directional position at a single price and later flattens it -- is the
teacher we want.

Style is separable from a single fill page, cheaply, without full history: the
discriminator is **fills per closed round trip**. A swing trader closes a round
trip in a handful of fills; an HFT wallet needs hundreds because it is almost
never flat. Median holding time and closed-trade count refine the call.

This gate is deliberately conservative: a wallet with too few closed round
trips is ``INSUFFICIENT_DATA``, not forced into a class, because a confident
style label on three trades would be noise dressed as signal.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence

from atlas.investment.hyper_copytrade.basis_reconstruction import RealizedLeg
from atlas.investment.hyper_copytrade.trade_reconstruction import (
    ReconstructedTrade,
)


class TraderStyle(str, Enum):
    DISCRETE_SWING = "discrete_swing"
    PERSISTENT_HFT = "persistent_hft"
    MIXED = "mixed"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True, slots=True)
class StyleThresholds:
    """Tunable cutoffs for the style call."""

    minimum_closed_trades: int = 8
    swing_max_fills_per_trade: float = 12.0
    hft_min_fills_per_trade: float = 40.0
    swing_min_median_hold_minutes: float = 5.0
    hft_max_median_hold_minutes: float = 2.0


@dataclass(frozen=True, slots=True)
class TraderStyleProfile:
    """A wallet's style call plus the metrics behind it."""

    style: TraderStyle
    fill_count: int
    closed_trade_count: int
    open_trade_count: int
    fills_per_closed_trade: float
    median_hold_minutes: float
    win_rate: float

    @property
    def is_teacher(self) -> bool:
        """A discrete swing trader is a usable entry/exit teacher."""
        return self.style is TraderStyle.DISCRETE_SWING

    def to_dict(self) -> dict[str, Any]:
        return {
            "style": self.style.value,
            "fill_count": self.fill_count,
            "closed_trade_count": self.closed_trade_count,
            "open_trade_count": self.open_trade_count,
            "fills_per_closed_trade": self.fills_per_closed_trade,
            "median_hold_minutes": self.median_hold_minutes,
            "win_rate": self.win_rate,
            "is_teacher": self.is_teacher,
        }


@dataclass(frozen=True, slots=True)
class LegTeacherThresholds:
    """Loosened teacher gate over realized legs (not round trips).

    Chosen to keep mixed and longer-hold traders as usable teachers -- more
    data at the cost of a blurrier entry-timing signal -- while still excluding
    pure scalpers, whose sub-minute average holds carry no learnable
    price-vs-range entry.
    """

    minimum_legs: int = 20
    minimum_median_hold_minutes: float = 5.0


@dataclass(frozen=True, slots=True)
class LegTeacherProfile:
    """A wallet's teacher assessment from realized legs."""

    is_teacher: bool
    leg_count: int
    median_hold_minutes: float
    win_rate: float
    reject_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_teacher": self.is_teacher,
            "leg_count": self.leg_count,
            "median_hold_minutes": self.median_hold_minutes,
            "win_rate": self.win_rate,
            "reject_reason": self.reject_reason,
        }


def profile_realized_legs(
    legs: Sequence[RealizedLeg],
    *,
    thresholds: LegTeacherThresholds | None = None,
) -> LegTeacherProfile:
    """Assess a wallet as a teacher from its realized legs (loosened bar).

    A teacher needs enough realized legs and a median holding time above the
    scalper floor. Mixed and slower-persistent wallets qualify; sub-minute HFT
    does not, because its average-basis entry is meaningless for price-vs-range.
    """
    thresholds = thresholds or LegTeacherThresholds()
    # Only entry-observed legs are learnable: a leg that closes a pre-window
    # position has real PnL but no observed entry price or holding time.
    observed = [leg for leg in legs if leg.entry_observed]
    if len(observed) < thresholds.minimum_legs:
        return LegTeacherProfile(
            is_teacher=False,
            leg_count=len(observed),
            median_hold_minutes=0.0,
            win_rate=0.0,
            reject_reason="too_few_legs",
        )

    median_hold = statistics.median([leg.holding_ms / 60000.0 for leg in observed])
    win_rate = sum(1 for leg in observed if leg.is_win) / len(observed)

    if median_hold < thresholds.minimum_median_hold_minutes:
        return LegTeacherProfile(
            is_teacher=False,
            leg_count=len(observed),
            median_hold_minutes=median_hold,
            win_rate=win_rate,
            reject_reason="scalper_hold_too_short",
        )

    return LegTeacherProfile(
        is_teacher=True,
        leg_count=len(observed),
        median_hold_minutes=median_hold,
        win_rate=win_rate,
        reject_reason="",
    )


def classify_style(
    trades: Sequence[ReconstructedTrade],
    fill_count: int,
    *,
    thresholds: StyleThresholds | None = None,
) -> TraderStyleProfile:
    """Classify trading style from reconstructed trades and the raw fill count."""
    thresholds = thresholds or StyleThresholds()
    closed = [trade for trade in trades if trade.is_closed]
    open_count = len(trades) - len(closed)

    if len(closed) < thresholds.minimum_closed_trades:
        return TraderStyleProfile(
            style=TraderStyle.INSUFFICIENT_DATA,
            fill_count=fill_count,
            closed_trade_count=len(closed),
            open_trade_count=open_count,
            fills_per_closed_trade=(
                fill_count / len(closed) if closed else float(fill_count)
            ),
            median_hold_minutes=0.0,
            win_rate=0.0,
        )

    fills_per_trade = fill_count / len(closed)
    median_hold = statistics.median(
        [trade.duration_ms / 60000.0 for trade in closed]
    )
    win_rate = sum(1 for trade in closed if trade.is_win) / len(closed)

    is_swing = (
        fills_per_trade <= thresholds.swing_max_fills_per_trade
        and median_hold >= thresholds.swing_min_median_hold_minutes
    )
    is_hft = (
        fills_per_trade >= thresholds.hft_min_fills_per_trade
        or median_hold <= thresholds.hft_max_median_hold_minutes
    )

    if is_swing and not is_hft:
        style = TraderStyle.DISCRETE_SWING
    elif is_hft and not is_swing:
        style = TraderStyle.PERSISTENT_HFT
    else:
        style = TraderStyle.MIXED

    return TraderStyleProfile(
        style=style,
        fill_count=fill_count,
        closed_trade_count=len(closed),
        open_trade_count=open_count,
        fills_per_closed_trade=fills_per_trade,
        median_hold_minutes=median_hold,
        win_rate=win_rate,
    )
