"""Variant Review Board v1 evidence aggregation."""

from __future__ import annotations

import math

import pandas as pd


def build_supporting_maps(
    *,
    validation_folds: pd.DataFrame,
    research_priorities: pd.DataFrame,
    learning_memory: pd.DataFrame,
    governance_snapshots: pd.DataFrame,
    engine_performance: pd.DataFrame,
    conflicts: pd.DataFrame,
) -> dict:
    """Build deterministic lookup maps for board scoring."""
    return {
        "folds": build_fold_map(
            validation_folds
        ),
        "priorities": build_priority_map(
            research_priorities
        ),
        "learning": build_learning_map(
            learning_memory
        ),
        "governance": build_governance_map(
            governance_snapshots
        ),
        "performance": build_performance_map(
            engine_performance
        ),
        "conflicts": build_conflict_set(
            conflicts
        ),
    }


def build_fold_map(
    frame: pd.DataFrame,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "hypothesis_id" not in frame.columns
    ):
        return {}

    rows = {}

    for hypothesis_id, group in frame.groupby(
        "hypothesis_id",
        sort=True,
    ):
        fold_winners = truth_series(
            group.get(
                "fold_winner",
                pd.Series(
                    False,
                    index=group.index,
                ),
            )
        )

        mean_advantage = numeric_series(
            group,
            "mean_return_advantage",
        )

        sharpe_advantage = numeric_series(
            group,
            "sharpe_advantage",
        )

        drawdown_improvement = numeric_series(
            group,
            "drawdown_improvement",
        )

        candidate_counts = numeric_series(
            group,
            "candidate_trade_count",
        )

        rows[str(hypothesis_id)] = {
            "fold_count": int(
                len(group)
            ),
            "fold_win_rate": round(
                float(
                    fold_winners.mean()
                ),
                8,
            ),
            "fold_mean_advantage_std": round(
                float(
                    mean_advantage.std(
                        ddof=0
                    )
                )
                if not mean_advantage.empty
                else 0.0,
                8,
            ),
            "positive_mean_folds": int(
                (
                    mean_advantage > 0
                ).sum()
            ),
            "positive_sharpe_folds": int(
                (
                    sharpe_advantage > 0
                ).sum()
            ),
            "nonnegative_drawdown_folds": int(
                (
                    drawdown_improvement >= 0
                ).sum()
            ),
            "total_candidate_trades": int(
                candidate_counts.sum()
            ),
        }

    return rows


def build_priority_map(
    frame: pd.DataFrame,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "source_id" not in frame.columns
    ):
        return {}

    return {
        str(row["source_id"]): {
            "meta_priority_score": number(
                row.get(
                    "priority_score"
                )
            ),
            "research_rank": integer(
                row.get(
                    "research_rank"
                )
            ),
        }
        for _, row in frame.iterrows()
    }


def build_learning_map(
    frame: pd.DataFrame,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "engine_id" not in frame.columns
    ):
        return {}

    return {
        str(row["engine_id"]): {
            "learning_reliability": number(
                row.get(
                    "recency_weighted_reliability"
                )
            ),
            "decision_stability": number(
                row.get(
                    "decision_stability"
                )
            ),
            "learning_observations": integer(
                row.get(
                    "observation_count"
                )
            ),
        }
        for _, row in frame.iterrows()
    }


def build_governance_map(
    frame: pd.DataFrame,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "engine_id" not in frame.columns
    ):
        return {}

    working = frame.copy()

    if "effective_at" in working.columns:
        working[
            "effective_at"
        ] = pd.to_datetime(
            working["effective_at"],
            errors="coerce",
            utc=True,
        )

        latest = working[
            "effective_at"
        ].max()

        if not pd.isna(latest):
            working = working[
                working["effective_at"]
                .eq(latest)
            ]

    return {
        str(row["engine_id"]): {
            "governance_eligible": boolean(
                row.get("eligible")
            ),
            "governance_weight": number(
                row.get(
                    "final_governance_weight"
                )
            ),
            "regime_suitability": number(
                row.get(
                    "regime_suitability"
                )
            ),
            "fusion_modifier": number(
                row.get(
                    "fusion_modifier",
                    1.0,
                ),
                default=1.0,
            ),
        }
        for _, row in working.iterrows()
    }


def build_performance_map(
    frame: pd.DataFrame,
) -> dict[str, dict]:
    if (
        frame is None
        or frame.empty
        or "engine_id" not in frame.columns
    ):
        return {}

    return {
        str(row["engine_id"]): {
            "parent_profit_factor": number(
                row.get(
                    "profit_factor"
                )
            ),
            "parent_mean_return": number(
                row.get(
                    "mean_return"
                )
            ),
            "parent_win_rate": number(
                row.get(
                    "win_rate"
                )
            ),
            "parent_trade_count": integer(
                row.get(
                    "trade_count"
                )
            ),
        }
        for _, row in frame.iterrows()
    }


def build_conflict_set(
    frame: pd.DataFrame,
) -> set[str]:
    if (
        frame is None
        or frame.empty
        or "variant_id" not in frame.columns
    ):
        return set()

    return set(
        frame[
            "variant_id"
        ].dropna().astype(str)
    )


def numeric_series(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(
            dtype=float
        )

    return pd.to_numeric(
        frame[column],
        errors="coerce",
    ).dropna()


def truth_series(
    values: pd.Series,
) -> pd.Series:
    if values.dtype == bool:
        return values

    return (
        values.astype(str)
        .str.lower()
        .isin([
            "true",
            "1",
            "yes",
        ])
    )


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


def integer(
    value,
    *,
    default: int = 0,
) -> int:
    try:
        return int(
            float(value)
        )
    except (
        TypeError,
        ValueError,
    ):
        return default


def boolean(
    value,
) -> bool:
    if isinstance(
        value,
        bool,
    ):
        return value

    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
    }
