"""Significance tests for the winner-vs-loser state gaps.

The entry/exit-state research produces two claims -- winners enter higher in the
range, and hold longer -- as differences in skewed, heavy-tailed distributions.
A median gap on its own could be sampling noise, so each gap is tested two ways,
both non-parametric because the distributions are nowhere near normal:

- **Mann-Whitney U** (rank-sum, tie-corrected, normal approximation): does one
  group stochastically dominate the other? Reported with a rank-biserial effect
  size, so a gap that is significant but tiny is visible as such.
- **Permutation test on the median difference**: a distribution-free check that
  makes no approximation at all -- shuffle the winner/loser labels many times
  and see how often chance reproduces the observed median gap.

Both are seeded/deterministic. Neither turns a distribution difference into a
validated trading edge; they only rule out "this gap is noise". The out-of-sample
paper evaluation is what tests whether the edge is real and usable.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np


def _normal_sf(z: float) -> float:
    """Upper-tail standard-normal survival function via erf."""
    return 0.5 * math.erfc(z / math.sqrt(2.0))


@dataclass(frozen=True, slots=True)
class SignificanceResult:
    """The outcome of testing one winner-vs-loser gap."""

    n_winners: int
    n_losers: int
    winner_median: float
    loser_median: float
    median_gap: float
    mann_whitney_u: float
    z_score: float
    p_value: float
    rank_biserial: float
    permutation_p_value: float

    @property
    def significant(self) -> bool:
        """Both tests agree the gap is unlikely under the null (p < 0.05)."""
        return self.p_value < 0.05 and self.permutation_p_value < 0.05

    def to_dict(self) -> dict[str, Any]:
        return {
            "n_winners": self.n_winners,
            "n_losers": self.n_losers,
            "winner_median": self.winner_median,
            "loser_median": self.loser_median,
            "median_gap": self.median_gap,
            "mann_whitney_u": self.mann_whitney_u,
            "z_score": self.z_score,
            "p_value": self.p_value,
            "rank_biserial": self.rank_biserial,
            "permutation_p_value": self.permutation_p_value,
            "significant": self.significant,
        }


def mann_whitney_u(winners: Sequence[float], losers: Sequence[float]) -> tuple[float, float, float, float]:
    """Return ``(U_winners, z, two-sided p, rank_biserial)`` with tie correction."""
    n1, n2 = len(winners), len(losers)
    combined = np.concatenate(
        [np.asarray(winners, dtype=np.float64), np.asarray(losers, dtype=np.float64)]
    )
    order = combined.argsort(kind="mergesort")
    ranks = np.empty(combined.size, dtype=np.float64)
    ranks[order] = np.arange(1, combined.size + 1, dtype=np.float64)

    # Average ranks within tie groups.
    sorted_vals = combined[order]
    i = 0
    tie_term = 0.0
    while i < sorted_vals.size:
        j = i
        while j + 1 < sorted_vals.size and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        if j > i:
            avg = (ranks[order[i]] + ranks[order[j]]) / 2.0
            for k in range(i, j + 1):
                ranks[order[k]] = avg
            t = j - i + 1
            tie_term += t**3 - t
        i = j + 1

    r1 = ranks[:n1].sum()
    u1 = r1 - n1 * (n1 + 1) / 2.0
    n = n1 + n2
    mu = n1 * n2 / 2.0
    sigma_sq = (n1 * n2 / 12.0) * ((n + 1) - tie_term / (n * (n - 1)))
    sigma = math.sqrt(sigma_sq) if sigma_sq > 0 else 0.0

    if sigma == 0.0:
        return u1, 0.0, 1.0, 0.0
    # Continuity-corrected z.
    z = (u1 - mu - math.copysign(0.5, u1 - mu)) / sigma
    p = 2.0 * _normal_sf(abs(z))
    rank_biserial = 1.0 - 2.0 * u1 / (n1 * n2)  # -1..1; sign = winners lower/higher
    return u1, z, min(1.0, p), -rank_biserial


def permutation_median_diff(
    winners: Sequence[float],
    losers: Sequence[float],
    *,
    iterations: int = 10_000,
    seed: int = 0,
) -> float:
    """Two-sided permutation p-value for the winner-minus-loser median gap."""
    a = np.asarray(winners, dtype=np.float64)
    b = np.asarray(losers, dtype=np.float64)
    observed = abs(float(np.median(a)) - float(np.median(b)))
    pooled = np.concatenate([a, b])
    n1 = a.size
    rng = np.random.default_rng(seed)

    hits = 0
    for _ in range(iterations):
        rng.shuffle(pooled)
        diff = abs(float(np.median(pooled[:n1])) - float(np.median(pooled[n1:])))
        if diff >= observed - 1e-12:
            hits += 1
    return (hits + 1) / (iterations + 1)  # add-one smoothing


def test_gap(
    winners: Sequence[float],
    losers: Sequence[float],
    *,
    permutation_iterations: int = 10_000,
    seed: int = 0,
) -> SignificanceResult | None:
    """Run both tests on a winner-vs-loser gap; ``None`` if a group is empty."""
    if len(winners) < 2 or len(losers) < 2:
        return None
    u, z, p, effect = mann_whitney_u(winners, losers)
    perm_p = permutation_median_diff(
        winners, losers, iterations=permutation_iterations, seed=seed
    )
    win_median = float(np.median(winners))
    los_median = float(np.median(losers))
    return SignificanceResult(
        n_winners=len(winners),
        n_losers=len(losers),
        winner_median=win_median,
        loser_median=los_median,
        median_gap=win_median - los_median,
        mann_whitney_u=u,
        z_score=z,
        p_value=p,
        rank_biserial=effect,
        permutation_p_value=perm_p,
    )
