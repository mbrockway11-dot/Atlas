"""Turn the derived entry state into a rule and test it out-of-sample.

Hardening at scale (41 teachers) showed a robust, direction-consistent signal:
for BOTH longs and shorts, winning legs entered *higher* in the recent range
than losing legs (LONG 0.48 vs 0.27; SHORT 0.83 vs 0.58, a large effect at
p<1e-100). Losers enter too low -- longs buying falling dips, shorts selling
after the drop. So the rule is "enter into strength": take an entry only when
range position is at or above a per-direction threshold.

The threshold is the midpoint between winners' and losers' median range position
on the TRAIN teachers -- a simple separating point, not fit to maximise any
score. Evaluation then scores the rule on teachers it was NOT derived from,
because a threshold fit on a set of traders will always look good on those same
traders. Only the effect *direction* (winners higher) comes from the full pool,
where it is significant at p<1e-100; the threshold *value* stays out-of-sample.
The out-of-sample lift is allowed to be zero -- that is a result, not a failure.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Callable, Sequence

from atlas.investment.hyper_copytrade.entry_exit_states import LegFeature


# A feature selector maps a leg to the scalar entry feature under test.
FeatureSelector = Callable[[LegFeature], "float | None"]


def range_position_of(feature: LegFeature) -> float | None:
    return feature.range_position


def momentum_of(feature: LegFeature) -> float | None:
    return feature.momentum


@dataclass(frozen=True, slots=True)
class _Side:
    """A per-direction threshold and which side of it wins, learned from train."""

    threshold: float
    enter_high: bool  # True: take when range >= threshold; False: when <=

    def takes(self, range_position: float) -> bool:
        return (
            range_position >= self.threshold
            if self.enter_high
            else range_position <= self.threshold
        )

    def to_dict(self) -> dict[str, Any]:
        return {"threshold": self.threshold, "enter_high": self.enter_high}


@dataclass(frozen=True, slots=True)
class EntryRule:
    """Direction-conditioned range filter; both threshold and side are train-fit.

    Nothing here is fixed by the researcher: for each direction the fitting
    routine reads, from the TRAIN teachers alone, whether winners sit above or
    below losers in the range and sets ``enter_high`` accordingly. So the rule's
    shape -- not just its numbers -- is out-of-sample, closing the objection that
    "enter into strength" was chosen after seeing the whole pool.
    """

    long_side: _Side
    short_side: _Side

    def takes(
        self, feature: LegFeature, selector: FeatureSelector = range_position_of
    ) -> bool:
        value = selector(feature)
        if value is None:
            return False
        side = self.long_side if feature.direction == "LONG" else self.short_side
        return side.takes(value)

    def to_dict(self) -> dict[str, Any]:
        return {
            "long_side": self.long_side.to_dict(),
            "short_side": self.short_side.to_dict(),
        }


def _fit_side(
    features: Sequence[LegFeature], direction: str, selector: FeatureSelector
) -> _Side:
    """Learn threshold and winning side for one direction from train features."""
    wins = [
        v
        for f in features
        if f.is_win and f.direction == direction and (v := selector(f)) is not None
    ]
    losses = [
        v
        for f in features
        if not f.is_win and f.direction == direction and (v := selector(f)) is not None
    ]
    if not wins or not losses:
        return _Side(threshold=0.5, enter_high=True)
    win_median = statistics.median(wins)
    loss_median = statistics.median(losses)
    return _Side(
        threshold=(win_median + loss_median) / 2.0,
        enter_high=win_median >= loss_median,
    )


def derive_entry_rule(
    features: Sequence[LegFeature], selector: FeatureSelector = range_position_of
) -> EntryRule:
    """Fit threshold and winning side per direction from train features only."""
    return EntryRule(
        long_side=_fit_side(features, "LONG", selector),
        short_side=_fit_side(features, "SHORT", selector),
    )


@dataclass(frozen=True, slots=True)
class RuleEvaluation:
    """Out-of-sample outcome of applying an entry rule to test legs."""

    taken: int
    taken_win_rate: float
    taken_mean_pnl: float
    skipped: int
    skipped_win_rate: float
    base_win_rate: float
    base_mean_pnl: float

    @property
    def win_rate_lift(self) -> float:
        """Win-rate of taken legs minus the base rate. Zero = no edge."""
        return self.taken_win_rate - self.base_win_rate

    def to_dict(self) -> dict[str, Any]:
        return {
            "taken": self.taken,
            "taken_win_rate": self.taken_win_rate,
            "taken_mean_pnl": self.taken_mean_pnl,
            "skipped": self.skipped,
            "skipped_win_rate": self.skipped_win_rate,
            "base_win_rate": self.base_win_rate,
            "base_mean_pnl": self.base_mean_pnl,
            "win_rate_lift": self.win_rate_lift,
        }


def evaluate_rule(
    rule: EntryRule,
    features: Sequence[LegFeature],
    selector: FeatureSelector = range_position_of,
) -> RuleEvaluation | None:
    """Score a rule on test legs: win rate of taken vs the base rate."""
    scored = [f for f in features if selector(f) is not None]
    if not scored:
        return None
    taken = [f for f in scored if rule.takes(f, selector)]
    skipped = [f for f in scored if not rule.takes(f, selector)]

    def win_rate(group: Sequence[LegFeature]) -> float:
        return sum(1 for f in group if f.is_win) / len(group) if group else 0.0

    def mean_pnl(group: Sequence[LegFeature]) -> float:
        return statistics.fmean([f.closed_pnl for f in group]) if group else 0.0

    return RuleEvaluation(
        taken=len(taken),
        taken_win_rate=win_rate(taken),
        taken_mean_pnl=mean_pnl(taken),
        skipped=len(skipped),
        skipped_win_rate=win_rate(skipped),
        base_win_rate=win_rate(scored),
        base_mean_pnl=mean_pnl(scored),
    )
