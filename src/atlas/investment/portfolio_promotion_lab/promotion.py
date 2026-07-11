"""Portfolio comparison and promotion scoring."""

from __future__ import annotations

import math

import pandas as pd

from atlas.investment.portfolio_promotion_lab.thresholds import (
    MAX_ASSET_WEIGHT,
    MAX_CANDIDATE_DRAWDOWN,
    MAX_CANDIDATE_VOLATILITY,
    MAX_CONCENTRATION_HHI,
    MAX_PROMOTION_TURNOVER,
    MIN_CASH_WEIGHT,
    MIN_DRAWDOWN_IMPROVEMENT,
    MIN_EFFECTIVE_ASSET_COUNT,
    MIN_NET_RETURN_ADVANTAGE,
    MIN_SHARPE_ADVANTAGE,
    MIN_VALID_WINDOWS,
    MIN_WINDOW_WIN_RATE,
)


def compare_portfolios(
    baseline: pd.DataFrame,
    candidate: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """Compare baseline and candidate metrics window by window."""
    if (
        baseline is None
        or baseline.empty
        or candidate is None
        or candidate.empty
    ):
        return (
            pd.DataFrame(),
            insufficient_decision(
                "Missing portfolio evaluation rows."
            ),
        )

    merged = baseline.merge(
        candidate,
        on="window_days",
        suffixes=(
            "_baseline",
            "_candidate",
        ),
        how="inner",
    )

    rows = []

    for _, row in merged.iterrows():
        return_advantage = (
            number(
                row.get(
                    "net_return_candidate"
                )
            )
            - number(
                row.get(
                    "net_return_baseline"
                )
            )
        )

        sharpe_advantage = (
            number(
                row.get(
                    "sharpe_candidate"
                )
            )
            - number(
                row.get(
                    "sharpe_baseline"
                )
            )
        )

        drawdown_improvement = (
            abs(
                number(
                    row.get(
                        "maximum_drawdown_baseline"
                    )
                )
            )
            - abs(
                number(
                    row.get(
                        "maximum_drawdown_candidate"
                    )
                )
            )
        )

        volatility_improvement = (
            number(
                row.get(
                    "annualized_volatility_baseline"
                )
            )
            - number(
                row.get(
                    "annualized_volatility_candidate"
                )
            )
        )

        candidate_wins = (
            return_advantage > 0
            and sharpe_advantage >= 0
            and drawdown_improvement >= 0
        )

        rows.append({
            "window_days": int(
                row["window_days"]
            ),
            "baseline_net_return": number(
                row.get(
                    "net_return_baseline"
                )
            ),
            "candidate_net_return": number(
                row.get(
                    "net_return_candidate"
                )
            ),
            "net_return_advantage": round(
                return_advantage,
                8,
            ),
            "baseline_sharpe": number(
                row.get(
                    "sharpe_baseline"
                )
            ),
            "candidate_sharpe": number(
                row.get(
                    "sharpe_candidate"
                )
            ),
            "sharpe_advantage": round(
                sharpe_advantage,
                8,
            ),
            "baseline_drawdown": number(
                row.get(
                    "maximum_drawdown_baseline"
                )
            ),
            "candidate_drawdown": number(
                row.get(
                    "maximum_drawdown_candidate"
                )
            ),
            "drawdown_improvement": round(
                drawdown_improvement,
                8,
            ),
            "volatility_improvement": round(
                volatility_improvement,
                8,
            ),
            "candidate_wins": bool(
                candidate_wins
            ),
        })

    comparison = pd.DataFrame(rows)

    decision = build_promotion_decision(
        comparison,
        candidate,
    )

    return comparison, decision


def build_promotion_decision(
    comparison: pd.DataFrame,
    candidate_metrics: pd.DataFrame,
) -> dict:
    """Apply conservative deterministic promotion governance."""
    valid = comparison[
        comparison[
            "window_days"
        ].notna()
    ]

    if len(valid) < MIN_VALID_WINDOWS:
        return insufficient_decision(
            "Too few valid historical windows."
        )

    window_win_rate = float(
        valid[
            "candidate_wins"
        ].mean()
    )

    mean_return_advantage = float(
        valid[
            "net_return_advantage"
        ].mean()
    )

    mean_sharpe_advantage = float(
        valid[
            "sharpe_advantage"
        ].mean()
    )

    mean_drawdown_improvement = float(
        valid[
            "drawdown_improvement"
        ].mean()
    )

    latest_candidate = (
        candidate_metrics.sort_values(
            "window_days"
        ).iloc[-1]
    )

    hard_failures = []

    maximum_drawdown = abs(
        number(
            latest_candidate.get(
                "maximum_drawdown"
            )
        )
    )

    volatility = number(
        latest_candidate.get(
            "annualized_volatility"
        )
    )

    turnover = number(
        latest_candidate.get(
            "turnover"
        )
    )

    concentration = number(
        latest_candidate.get(
            "concentration_hhi"
        )
    )

    effective_assets = number(
        latest_candidate.get(
            "effective_asset_count"
        )
    )

    cash_weight = number(
        latest_candidate.get(
            "cash_weight"
        )
    )

    largest_weight = number(
        latest_candidate.get(
            "largest_asset_weight"
        )
    )

    if maximum_drawdown > MAX_CANDIDATE_DRAWDOWN:
        hard_failures.append(
            "EXCESSIVE_DRAWDOWN"
        )

    if volatility > MAX_CANDIDATE_VOLATILITY:
        hard_failures.append(
            "EXCESSIVE_VOLATILITY"
        )

    if turnover > MAX_PROMOTION_TURNOVER:
        hard_failures.append(
            "EXCESSIVE_TURNOVER"
        )

    if concentration > MAX_CONCENTRATION_HHI:
        hard_failures.append(
            "EXCESSIVE_CONCENTRATION"
        )

    if effective_assets < MIN_EFFECTIVE_ASSET_COUNT:
        hard_failures.append(
            "INSUFFICIENT_DIVERSIFICATION"
        )

    if cash_weight < MIN_CASH_WEIGHT:
        hard_failures.append(
            "CASH_FLOOR_VIOLATION"
        )

    if largest_weight > MAX_ASSET_WEIGHT:
        hard_failures.append(
            "ASSET_CAP_VIOLATION"
        )

    promotion_conditions = {
        "window_win_rate": (
            window_win_rate
            >= MIN_WINDOW_WIN_RATE
        ),
        "net_return_advantage": (
            mean_return_advantage
            >= MIN_NET_RETURN_ADVANTAGE
        ),
        "sharpe_advantage": (
            mean_sharpe_advantage
            >= MIN_SHARPE_ADVANTAGE
        ),
        "drawdown_improvement": (
            mean_drawdown_improvement
            >= MIN_DRAWDOWN_IMPROVEMENT
        ),
        "no_hard_failures": (
            len(hard_failures) == 0
        ),
    }

    passed_conditions = sum(
        bool(value)
        for value in promotion_conditions.values()
    )

    promotion_score = (
        passed_conditions
        / len(promotion_conditions)
    )

    if all(
        promotion_conditions.values()
    ):
        decision = "PROMOTE_CANDIDATE"
        reason = (
            "Candidate passed all performance, "
            "risk, diversification, and cost gates."
        )

    elif hard_failures:
        decision = "KEEP_BASELINE"
        reason = (
            "Candidate breached one or more "
            "hard portfolio-risk constraints."
        )

    elif passed_conditions >= 3:
        decision = "EXTEND_RESEARCH"
        reason = (
            "Candidate shows partial improvement "
            "but has not met every promotion threshold."
        )

    else:
        decision = "KEEP_BASELINE"
        reason = (
            "Candidate did not demonstrate sufficiently "
            "consistent net improvement."
        )

    return {
        "decision": decision,
        "reason": reason,
        "promotion_score": round(
            promotion_score,
            8,
        ),
        "window_win_rate": round(
            window_win_rate,
            8,
        ),
        "mean_net_return_advantage": round(
            mean_return_advantage,
            8,
        ),
        "mean_sharpe_advantage": round(
            mean_sharpe_advantage,
            8,
        ),
        "mean_drawdown_improvement": round(
            mean_drawdown_improvement,
            8,
        ),
        "promotion_conditions": (
            promotion_conditions
        ),
        "hard_failures": hard_failures,
        "candidate_remains_read_only": True,
        "execution_target_changed": False,
    }


def insufficient_decision(
    reason: str,
) -> dict:
    return {
        "decision": "INSUFFICIENT_DATA",
        "reason": reason,
        "promotion_score": 0.0,
        "window_win_rate": 0.0,
        "mean_net_return_advantage": 0.0,
        "mean_sharpe_advantage": 0.0,
        "mean_drawdown_improvement": 0.0,
        "promotion_conditions": {},
        "hard_failures": [
            "INSUFFICIENT_DATA"
        ],
        "candidate_remains_read_only": True,
        "execution_target_changed": False,
    }


def number(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )
