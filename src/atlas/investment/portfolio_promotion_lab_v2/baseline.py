"""Walk-forward reconstruction of Alpha Portfolio v3.1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.portfolio_promotion_lab_v2.config import (
    BASELINE_CASH_FLOOR,
    MAX_ASSET_WEIGHT,
)


def reconstruct_baseline_portfolio(
    historical_features: pd.DataFrame,
    *,
    rebalance_date: pd.Timestamp,
) -> pd.Series:
    """Rebuild legacy Alpha Portfolio using only contemporaneous data."""
    snapshot = historical_features[
        historical_features["date"]
        == rebalance_date
    ].copy()

    if snapshot.empty:
        return pd.Series(
            {
                "CASH": 1.0,
            }
        )

    score_column = find_score_column(
        snapshot
    )

    if score_column is None:
        return pd.Series(
            {
                "CASH": 1.0,
            }
        )

    snapshot["portfolio_score"] = pd.to_numeric(
        snapshot[score_column],
        errors="coerce",
    ).fillna(0.0)

    snapshot = snapshot[
        snapshot["portfolio_score"] > 0
    ].sort_values(
        [
            "portfolio_score",
            "asset",
        ],
        ascending=[
            False,
            True,
        ],
        kind="stable",
    ).head(5)

    if snapshot.empty:
        return pd.Series(
            {
                "CASH": 1.0,
            }
        )

    investable = (
        1.0
        - BASELINE_CASH_FLOOR
    )

    risky = (
        snapshot.set_index(
            "asset"
        )[
            "portfolio_score"
        ]
    )

    risky = (
        risky
        / float(
            risky.sum()
        )
        * investable
    )

    risky = apply_asset_cap(
        risky,
        max_weight=MAX_ASSET_WEIGHT,
        target_total=investable,
    )

    weights = risky.copy()

    weights.loc["CASH"] = max(
        BASELINE_CASH_FLOOR,
        1.0
        - float(
            risky.sum()
        ),
    )

    return normalize(
        weights
    )


def find_score_column(
    snapshot: pd.DataFrame,
) -> str | None:
    for candidate in [
        "cross_sectional_score",
        "cross_sectional_percentile",
        "momentum_30d",
        "return_30d",
    ]:
        if candidate in snapshot.columns:
            return candidate

    return None


def apply_asset_cap(
    weights: pd.Series,
    *,
    max_weight: float,
    target_total: float,
) -> pd.Series:
    result = normalize(
        weights
    ) * target_total

    for _ in range(20):
        over = result > max_weight

        if not over.any():
            break

        excess = float(
            (
                result[over]
                - max_weight
            ).sum()
        )

        result.loc[over] = max_weight

        under = ~over

        capacity = (
            max_weight
            - result[under]
        ).clip(lower=0.0)

        total_capacity = float(
            capacity.sum()
        )

        if (
            excess <= 1e-12
            or total_capacity <= 1e-12
        ):
            break

        result.loc[under] += (
            capacity
            / total_capacity
            * min(
                excess,
                total_capacity,
            )
        )

    return result


def normalize(
    weights: pd.Series,
) -> pd.Series:
    result = pd.to_numeric(
        weights,
        errors="coerce",
    ).fillna(0.0).clip(
        lower=0.0,
    )

    total = float(
        result.sum()
    )

    if total <= 1e-12:
        return pd.Series(
            {
                "CASH": 1.0,
            }
        )

    return result / total
