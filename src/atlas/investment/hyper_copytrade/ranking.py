"""Rank Hyperliquid leaderboard entries to select traders worth copying.

The leaderboard exposes PnL, ROI and volume per window, but **not** leverage
(leverage is per-position, visible only in the wallet's clearinghouse state).
So ranking is by PnL or ROI over a window; the "leveraged shorts and longs"
detail is read afterward from the selected wallet's positions.

A note on the metric, because it decides who gets copied:

- ``pnl`` (absolute USD) rewards large accounts. A whale earning 0.5% outranks
  a small account earning 200%. Good if "best" means "moves the most money".
- ``roi`` rewards efficiency but is noisy and gameable on tiny accounts, so it
  is paired with ``minimum_account_value`` to drop dust.

Neither is universally correct, so both are supported and the choice is
explicit. The defaults rank by absolute PnL over the weekly window with a
$100k account floor: live probing showed ROI-ranked leaders are dominated by
tiny accounts that spiked then withdrew (highest ROI wallet: $0 balance, no
open positions -- uncopyable), whereas PnL-with-a-floor surfaces real, funded,
actively-leveraged traders. Callers should still set this deliberately;
copyability itself is enforced later in ``selection.py``.
"""

from __future__ import annotations

from collections.abc import Sequence

from atlas.investment.hyper_copytrade.contracts import (
    LeaderboardEntry,
    TraderRanking,
    VALID_METRICS,
    VALID_WINDOWS,
)


DEFAULT_WINDOW = "week"
DEFAULT_METRIC = "pnl"
DEFAULT_TOP_N = 50
DEFAULT_MINIMUM_ACCOUNT_VALUE = 100_000.0


def rank_traders(
    entries: list[LeaderboardEntry],
    *,
    window: str = DEFAULT_WINDOW,
    metric: str = DEFAULT_METRIC,
    top_n: int = DEFAULT_TOP_N,
    minimum_account_value: float = DEFAULT_MINIMUM_ACCOUNT_VALUE,
    minimum_volume: float = 0.0,
) -> list[TraderRanking]:
    """Return the top ``top_n`` traders under an explicit ranking policy.

    Entries are filtered by ``minimum_account_value`` (drop dust) and
    ``minimum_volume`` (drop inactive), then sorted by the chosen window's
    metric, descending. Ties break by account value so ranking is
    deterministic.
    """
    if window not in VALID_WINDOWS:
        raise ValueError(f"Unknown window {window!r}; expected {VALID_WINDOWS}.")
    if metric not in VALID_METRICS:
        raise ValueError(f"Unknown metric {metric!r}; expected {VALID_METRICS}.")
    if top_n < 1:
        raise ValueError("top_n must be at least 1.")

    eligible: list[tuple[LeaderboardEntry, float]] = []
    for entry in entries:
        if entry.account_value < minimum_account_value:
            continue
        try:
            performance = entry.performance(window)
        except ValueError:
            continue
        if performance.volume < minimum_volume:
            continue
        eligible.append((entry, performance.metric(metric)))

    eligible.sort(
        key=lambda pair: (pair[1], pair[0].account_value),
        reverse=True,
    )

    rankings: list[TraderRanking] = []
    for rank, (entry, metric_value) in enumerate(eligible[:top_n], start=1):
        performance = entry.performance(window)
        rankings.append(
            TraderRanking(
                rank=rank,
                address=entry.address,
                account_value=entry.account_value,
                display_name=entry.display_name,
                window=window,
                metric=metric,
                metric_value=metric_value,
                pnl=performance.pnl,
                roi=performance.roi,
                volume=performance.volume,
            )
        )
    return rankings


def best_trader(rankings: list[TraderRanking]) -> TraderRanking:
    """Return the top-ranked trader, or raise if the ranking is empty."""
    if not rankings:
        raise ValueError("No ranked traders to choose from.")
    return rankings[0]


def per_leg_sharpe(pnls: Sequence[float]) -> float:
    """Mean/stdev of a trader's per-leg realized PnL: a scale-invariant skill score.

    Validated on the teacher registry (152k reconstructed legs, 104 teachers with
    enough legs each side of an in-sample/out-of-sample time split): this metric
    persists across the split better than raw total PnL (Spearman rho 0.25 vs
    0.18), and its top quartile out-performs the field out-of-sample while raw-PnL
    selection does not. Because it is a ratio it is size-invariant -- a whale and
    a small account are judged on consistency, not on how much money moved. The
    leaderboard cannot supply it (it exposes only window PnL), so it is computed
    from a wallet's reconstructed legs and is the metric the registry-backed
    roster path should rank on.
    """
    values = [float(pnl) for pnl in pnls]
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    sd = variance ** 0.5
    return mean / sd if sd > 0.0 else 0.0


def rank_teachers_by_skill(
    teachers: Sequence[tuple[str, Sequence[float]]],
) -> list[tuple[str, float]]:
    """Rank ``(address, leg_pnls)`` teachers by per-leg Sharpe, highest first.

    The registry-backed selection should rank on this rather than leaderboard
    PnL: the validation showed raw-PnL selection does not beat the average
    teacher out-of-sample, while risk-adjusted, consistency-weighted selection
    does. Pair it with a wide roster and the concentration/net caps in
    ``mirror.blend_targets`` -- the copy-trade edge is breadth, not the top few.
    """
    scored = [(address, per_leg_sharpe(pnls)) for address, pnls in teachers]
    return sorted(scored, key=lambda item: item[1], reverse=True)
