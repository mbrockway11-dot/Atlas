"""Promotion policy for Atlas Alpha Research Lab v1."""

from __future__ import annotations

import math

import pandas as pd


DECISION_COLUMNS = [
    "engine_id",
    "family",
    "decision",
    "promotion_score",
    "performance_score",
    "stability_score",
    "risk_score",
    "independence_score",
    "sample_score",
    "trade_count",
    "mean_return",
    "profit_factor",
    "max_drawdown",
    "portfolio_cumulative_return",
    "portfolio_sharpe",
    "portfolio_recovery_factor",
    "positive_asset_ratio",
    "positive_year_ratio",
    "positive_regime_ratio",
    "average_independence",
    "hard_failures",
    "reason_codes",
]


def build_promotion_decisions(
    metrics: pd.DataFrame,
    independence: pd.DataFrame,
) -> pd.DataFrame:
    """Score and classify research engines."""
    if metrics is None or metrics.empty:
        return pd.DataFrame(
            columns=DECISION_COLUMNS
        )

    independence_map = (
        average_independence_by_engine(
            independence
        )
    )

    rows: list[dict] = []

    for _, metric in metrics.iterrows():
        engine_id = str(
            metric.get("engine_id")
        )

        trade_count = integer(
            metric.get("trade_count")
        )
        mean_return = number(
            metric.get("mean_return")
        )
        profit_factor = number(
            metric.get("profit_factor")
        )
        max_drawdown = number(
            metric.get("max_drawdown")
        )
        
        portfolio_cumulative_return = number(
            metric.get(
                "portfolio_cumulative_return"
            )
        )

        portfolio_sharpe = number(
            metric.get(
                "portfolio_sharpe"
            )
        )

        portfolio_recovery_factor = number(
            metric.get(
                "portfolio_recovery_factor"
            )
        )
        trade_sharpe = number(
            metric.get("trade_sharpe")
        )
        trade_sortino = number(
            metric.get("trade_sortino")
        )
        largest_asset_share = number(
            metric.get("largest_asset_share")
        )
        positive_asset_ratio = number(
            metric.get("positive_asset_ratio")
        )
        positive_year_ratio = number(
            metric.get("positive_year_ratio")
        )
        positive_regime_ratio = number(
            metric.get("positive_regime_ratio")
        )

        average_independence = number(
            independence_map.get(
                engine_id,
                0.50,
            )
        )

        sample_score = clamp(
            trade_count / 250.0
        )

        expectancy_score = scaled_score(
            mean_return,
            weak=0.0,
            strong=0.02,
        )

        profit_factor_score = scaled_score(
            profit_factor,
            weak=0.90,
            strong=1.50,
        )

        sharpe_score = scaled_score(
            trade_sharpe,
            weak=-0.05,
            strong=0.20,
        )

        sortino_score = scaled_score(
            trade_sortino,
            weak=-0.05,
            strong=0.20,
        )

        portfolio_return_score = scaled_score(
            portfolio_cumulative_return,
            weak=0.0,
            strong=0.50,
        )

        portfolio_sharpe_score = scaled_score(
            portfolio_sharpe,
            weak=0.0,
            strong=1.0,
        )

        portfolio_recovery_score = scaled_score(
            portfolio_recovery_factor,
            weak=0.0,
            strong=1.5,
        )

        performance_score = clamp(
            expectancy_score * 0.20
            + profit_factor_score * 0.20
            + sharpe_score * 0.10
            + sortino_score * 0.10
            + portfolio_return_score * 0.20
            + portfolio_sharpe_score * 0.10
            + portfolio_recovery_score * 0.10
        )

        stability_score = clamp(
            positive_asset_ratio * 0.40
            + positive_year_ratio * 0.35
            + positive_regime_ratio * 0.25
        )

        drawdown_score = clamp(
            1.0
            - abs(
                min(
                    max_drawdown,
                    0.0,
                )
            )
            / 0.60
        )

        concentration_score = clamp(
            1.0
            - max(
                0.0,
                largest_asset_share - 0.20
            )
            / 0.50
        )

        risk_score = clamp(
            drawdown_score * 0.65
            + concentration_score * 0.35
        )

        independence_score = clamp(
            average_independence
        )

        promotion_score = clamp(
            performance_score * 0.35
            + stability_score * 0.25
            + risk_score * 0.15
            + independence_score * 0.15
            + sample_score * 0.10
        )

        hard_failures: list[str] = []

        if trade_count < 50:
            hard_failures.append(
                "INSUFFICIENT_SAMPLE"
            )

        if mean_return <= 0:
            hard_failures.append(
                "NONPOSITIVE_EXPECTANCY"
            )

        if profit_factor < 1.0:
            hard_failures.append(
                "PROFIT_FACTOR_BELOW_ONE"
            )

        if max_drawdown <= -0.70:
            hard_failures.append(
                "EXCESSIVE_DRAWDOWN"
            )

        if portfolio_cumulative_return <= 0:
            hard_failures.append(
                "NONPOSITIVE_PORTFOLIO_RETURN"
            )

        if portfolio_sharpe <= 0:
            hard_failures.append(
                "NONPOSITIVE_PORTFOLIO_SHARPE"
            )

        if largest_asset_share >= 0.65:
            hard_failures.append(
                "ASSET_CONCENTRATION"
            )

        if (
            not hard_failures
            and promotion_score >= 0.72
            and profit_factor >= 1.20
            and positive_year_ratio >= 0.60
            and portfolio_cumulative_return > 0
            and portfolio_sharpe >= 0.50
            and portfolio_recovery_factor > 0
        ):
            decision = "PROMOTE"

        elif (
            promotion_score >= 0.55
            and mean_return > 0
            and profit_factor >= 1.05
        ):
            decision = "KEEP"

        elif (
            trade_count >= 50
            and (
                mean_return > 0
                or profit_factor >= 1.0
            )
        ):
            decision = "REVISE"

        else:
            decision = "RETIRE"

        reason_codes = build_reason_codes(
            decision=decision,
            promotion_score=promotion_score,
            performance_score=performance_score,
            stability_score=stability_score,
            independence_score=independence_score,
            hard_failures=hard_failures,
        )

        rows.append({
            "engine_id": engine_id,
            "family": str(
                metric.get(
                    "family",
                    "unknown",
                )
            ),
            "decision": decision,
            "promotion_score": round(
                promotion_score,
                8,
            ),
            "performance_score": round(
                performance_score,
                8,
            ),
            "stability_score": round(
                stability_score,
                8,
            ),
            "risk_score": round(
                risk_score,
                8,
            ),
            "independence_score": round(
                independence_score,
                8,
            ),
            "sample_score": round(
                sample_score,
                8,
            ),
            "trade_count": trade_count,
            "mean_return": mean_return,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "portfolio_cumulative_return": (
                portfolio_cumulative_return
            ),
            "portfolio_sharpe": portfolio_sharpe,
            "portfolio_recovery_factor": (
                portfolio_recovery_factor
            ),
            "positive_asset_ratio": (
                positive_asset_ratio
            ),
            "positive_year_ratio": (
                positive_year_ratio
            ),
            "positive_regime_ratio": (
                positive_regime_ratio
            ),
            "average_independence": (
                average_independence
            ),
            "hard_failures": "|".join(
                hard_failures
            ),
            "reason_codes": "|".join(
                reason_codes
            ),
        })

    return pd.DataFrame(
        rows,
        columns=DECISION_COLUMNS,
    ).sort_values(
        [
            "promotion_score",
            "engine_id",
        ],
        ascending=[
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def average_independence_by_engine(
    independence: pd.DataFrame,
) -> dict[str, float]:
    """Average pairwise independence for each engine."""
    if (
        independence is None
        or independence.empty
    ):
        return {}

    values: dict[str, list[float]] = {}

    for _, row in independence.iterrows():
        engine_a = str(
            row.get("engine_a")
        )
        engine_b = str(
            row.get("engine_b")
        )

        score = number(
            row.get(
                "independence_score"
            )
        )

        values.setdefault(
            engine_a,
            [],
        ).append(score)

        values.setdefault(
            engine_b,
            [],
        ).append(score)

    return {
        engine_id: float(
            sum(scores) / len(scores)
        )
        for engine_id, scores in values.items()
        if scores
    }


def build_reason_codes(
    *,
    decision: str,
    promotion_score: float,
    performance_score: float,
    stability_score: float,
    independence_score: float,
    hard_failures: list[str],
) -> list[str]:
    reasons = [
        f"DECISION_{decision}",
    ]

    if promotion_score >= 0.72:
        reasons.append(
            "HIGH_COMPOSITE_SCORE"
        )
    elif promotion_score >= 0.55:
        reasons.append(
            "MODERATE_COMPOSITE_SCORE"
        )
    else:
        reasons.append(
            "LOW_COMPOSITE_SCORE"
        )

    if performance_score >= 0.65:
        reasons.append(
            "STRONG_PERFORMANCE"
        )

    if stability_score >= 0.65:
        reasons.append(
            "BROAD_STABILITY"
        )

    if independence_score >= 0.60:
        reasons.append(
            "HIGH_DIVERSIFICATION_VALUE"
        )
    elif independence_score <= 0.30:
        reasons.append(
            "HIGH_REDUNDANCY"
        )

    reasons.extend(
        hard_failures
    )

    return reasons


def scaled_score(
    value: float,
    *,
    weak: float,
    strong: float,
) -> float:
    if strong <= weak:
        return 0.0

    return clamp(
        (value - weak)
        / (strong - weak)
    )


def number(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )


def integer(
    value,
    *,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def clamp(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            float(value),
        ),
    )



