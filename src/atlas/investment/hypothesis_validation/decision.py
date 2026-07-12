"""Hypothesis validation decision governance."""

from __future__ import annotations

import pandas as pd

from atlas.investment.hypothesis_validation.config import (
    MINIMUM_DRAWDOWN_IMPROVEMENT,
    MINIMUM_FOLD_WIN_RATE,
    MINIMUM_MEAN_RETURN_ADVANTAGE,
    MINIMUM_PROFIT_FACTOR_ADVANTAGE,
    MINIMUM_RETENTION_RATIO,
    MINIMUM_SHARPE_ADVANTAGE,
    MINIMUM_TOTAL_CANDIDATE_TRADES,
    MINIMUM_VALID_FOLDS,
    REJECTION_FOLD_WIN_RATE,
    REJECTION_MEAN_ADVANTAGE,
)


def build_validation_decision(
    hypothesis: dict,
    folds: pd.DataFrame,
) -> dict:
    """Return VALIDATE, REJECT, EXTEND_RESEARCH, or INSUFFICIENT_DATA."""
    base = {
        "hypothesis_id": hypothesis.get(
            "hypothesis_id"
        ),
        "hypothesis_type": hypothesis.get(
            "hypothesis_type"
        ),
        "engine_id": hypothesis.get(
            "engine_id"
        ),
        "family": hypothesis.get(
            "family"
        ),
        "feature": hypothesis.get(
            "feature"
        ),
        "state": hypothesis.get(
            "state"
        ),
    }

    if folds is None or folds.empty:
        return {
            **base,
            "decision": (
                "INSUFFICIENT_DATA"
            ),
            "reason": (
                "No valid walk-forward folds "
                "were produced."
            ),
            "validation_score": 0.0,
            "valid_fold_count": 0,
            "candidate_trade_count": 0,
            "retention_ratio": 0.0,
            "fold_win_rate": 0.0,
            "mean_return_advantage": 0.0,
            "profit_factor_advantage": 0.0,
            "sharpe_advantage": 0.0,
            "drawdown_improvement": 0.0,
            "conditions_passed": "",
            "hard_failures": (
                "NO_VALID_FOLDS"
            ),
            "execution_instruction": False,
        }

    fold_count = int(
        len(folds)
    )

    baseline_trades = int(
        folds[
            "baseline_trade_count"
        ].sum()
    )

    candidate_trades = int(
        folds[
            "candidate_trade_count"
        ].sum()
    )

    retention_ratio = (
        candidate_trades
        / baseline_trades
        if baseline_trades > 0
        else 0.0
    )

    fold_win_rate = float(
        folds[
            "fold_winner"
        ].astype(bool).mean()
    )

    mean_advantage = weighted_average(
        folds,
        "mean_return_advantage",
        "baseline_trade_count",
    )

    factor_advantage = weighted_average(
        folds,
        "profit_factor_advantage",
        "baseline_trade_count",
    )

    sharpe_advantage = weighted_average(
        folds,
        "sharpe_advantage",
        "baseline_trade_count",
    )

    drawdown_improvement = (
        weighted_average(
            folds,
            "drawdown_improvement",
            "baseline_trade_count",
        )
    )

    hard_failures = []

    if fold_count < MINIMUM_VALID_FOLDS:
        hard_failures.append(
            "INSUFFICIENT_FOLDS"
        )

    if (
        candidate_trades
        < MINIMUM_TOTAL_CANDIDATE_TRADES
    ):
        hard_failures.append(
            "INSUFFICIENT_CANDIDATE_TRADES"
        )

    if (
        retention_ratio
        < MINIMUM_RETENTION_RATIO
    ):
        hard_failures.append(
            "EXCESSIVE_SAMPLE_REDUCTION"
        )

    conditions = {
        "mean_return_improved": (
            mean_advantage
            >= MINIMUM_MEAN_RETURN_ADVANTAGE
        ),
        "profit_factor_improved": (
            factor_advantage
            >= MINIMUM_PROFIT_FACTOR_ADVANTAGE
        ),
        "sharpe_improved": (
            sharpe_advantage
            >= MINIMUM_SHARPE_ADVANTAGE
        ),
        "drawdown_not_worse": (
            drawdown_improvement
            >= MINIMUM_DRAWDOWN_IMPROVEMENT
        ),
        "fold_consistency": (
            fold_win_rate
            >= MINIMUM_FOLD_WIN_RATE
        ),
        "sample_retained": (
            retention_ratio
            >= MINIMUM_RETENTION_RATIO
        ),
    }

    passed = sum(
        bool(value)
        for value in conditions.values()
    )

    validation_score = (
        passed
        / len(conditions)
    )

    if hard_failures:
        decision = "INSUFFICIENT_DATA"

        reason = (
            "The gated variant lacks sufficient "
            "walk-forward evidence or retains too "
            "little of the original sample."
        )

    elif all(
        conditions.values()
    ):
        decision = "VALIDATE"

        reason = (
            "The gated variant improved expectancy, "
            "profit factor, Sharpe, drawdown, and "
            "fold consistency while retaining an "
            "acceptable trade sample."
        )

    elif (
        mean_advantage
        <= REJECTION_MEAN_ADVANTAGE
        and fold_win_rate
        <= REJECTION_FOLD_WIN_RATE
    ):
        decision = "REJECT"

        reason = (
            "The gated variant failed to improve "
            "out-of-sample expectancy and lost in "
            "most walk-forward folds."
        )

    else:
        decision = "EXTEND_RESEARCH"

        reason = (
            "The hypothesis showed mixed evidence "
            "and requires additional observations "
            "or revised gating logic."
        )

    return {
        **base,
        "decision": decision,
        "reason": reason,
        "validation_score": round(
            validation_score,
            8,
        ),
        "valid_fold_count": fold_count,
        "baseline_trade_count": (
            baseline_trades
        ),
        "candidate_trade_count": (
            candidate_trades
        ),
        "retention_ratio": round(
            retention_ratio,
            8,
        ),
        "fold_win_rate": round(
            fold_win_rate,
            8,
        ),
        "mean_return_advantage": round(
            mean_advantage,
            8,
        ),
        "profit_factor_advantage": round(
            factor_advantage,
            8,
        ),
        "sharpe_advantage": round(
            sharpe_advantage,
            8,
        ),
        "drawdown_improvement": round(
            drawdown_improvement,
            8,
        ),
        "conditions_passed": "|".join(
            name
            for name, value in (
                conditions.items()
            )
            if value
        ),
        "hard_failures": "|".join(
            hard_failures
        ),
        "execution_instruction": False,
    }


def weighted_average(
    frame: pd.DataFrame,
    value_column: str,
    weight_column: str,
) -> float:
    values = pd.to_numeric(
        frame[value_column],
        errors="coerce",
    )

    weights = pd.to_numeric(
        frame[weight_column],
        errors="coerce",
    ).fillna(0.0).clip(
        lower=0.0,
    )

    valid = values.notna() & weights.gt(
        0.0
    )

    if not valid.any():
        return 0.0

    return float(
        (
            values[valid]
            * weights[valid]
        ).sum()
        / weights[valid].sum()
    )
