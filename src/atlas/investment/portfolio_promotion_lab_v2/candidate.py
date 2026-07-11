"""Walk-forward Portfolio Optimizer v2 reconstruction."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from atlas.investment.portfolio_promotion_lab_v2.config import (
    CANDIDATE_CASH_FLOOR,
    COVARIANCE_LOOKBACK_DAYS,
    MAX_ASSET_WEIGHT,
    MAX_SELECTED_ASSETS,
    MINIMUM_COVARIANCE_DAYS,
)


def build_governance_map(
    governance: pd.DataFrame,
) -> dict[str, float]:
    """Build fixed approved-engine policy for walk-forward research."""
    if (
        governance is None
        or governance.empty
        or "engine_id" not in governance.columns
    ):
        return {}

    frame = governance.copy()

    if "eligible" in frame.columns:
        frame = frame[
            frame["eligible"]
            .astype(str)
            .str.lower()
            .isin([
                "true",
                "1",
                "yes",
            ])
        ]

    if "governance_weight" not in frame.columns:
        frame["governance_weight"] = 1.0

    frame["governance_weight"] = pd.to_numeric(
        frame["governance_weight"],
        errors="coerce",
    ).fillna(0.0).clip(
        lower=0.0,
    )

    frame = frame[
        frame["governance_weight"] > 0
    ]

    total = float(
        frame["governance_weight"].sum()
    )

    if total <= 1e-12:
        return {}

    return {
        str(row["engine_id"]): (
            float(
                row["governance_weight"]
            )
            / total
        )
        for _, row in frame.iterrows()
    }


def reconstruct_candidate_portfolio(
    *,
    rebalance_date: pd.Timestamp,
    signals: pd.DataFrame,
    returns: pd.DataFrame,
    governance_map: dict[str, float],
) -> pd.Series:
    """Rebuild candidate portfolio without future market data."""
    day_signals = signals[
        signals["date"]
        == rebalance_date
    ].copy()

    if (
        day_signals.empty
        or not governance_map
    ):
        return pd.Series(
            {
                "CASH": 1.0,
            }
        )

    day_signals = day_signals[
        day_signals[
            "engine_id"
        ].isin(
            governance_map
        )
    ]

    if day_signals.empty:
        return pd.Series(
            {
                "CASH": 1.0,
            }
        )

    day_signals[
        "governance_weight"
    ] = day_signals[
        "engine_id"
    ].map(
        governance_map
    ).fillna(0.0)

    day_signals[
        "weighted_signal"
    ] = (
        day_signals[
            "normalized_score"
        ]
        * day_signals[
            "confidence"
        ]
        * day_signals[
            "governance_weight"
        ]
    )

    candidates = (
        day_signals.groupby(
            "asset",
            sort=True,
        )
        .agg(
            weighted_signal=(
                "weighted_signal",
                "sum",
            ),
            available_weight=(
                "governance_weight",
                "sum",
            ),
            engine_count=(
                "engine_id",
                "nunique",
            ),
        )
        .reset_index()
    )

    candidates["ensemble_score"] = (
        candidates["weighted_signal"]
        / candidates[
            "available_weight"
        ].replace(
            0.0,
            np.nan,
        )
    ).fillna(0.0)

    candidates = candidates[
        candidates["ensemble_score"]
        > 0.50
    ].sort_values(
        [
            "ensemble_score",
            "asset",
        ],
        ascending=[
            False,
            True,
        ],
        kind="stable",
    ).head(
        MAX_SELECTED_ASSETS
    )

    if candidates.empty:
        return pd.Series(
            {
                "CASH": 1.0,
            }
        )

    assets = candidates[
        "asset"
    ].tolist()

    historical_returns = returns.loc[
        returns.index < rebalance_date,
        assets,
    ].tail(
        COVARIANCE_LOOKBACK_DAYS
    )

    covariance = build_covariance(
        historical_returns,
        assets,
    )

    volatility = pd.Series(
        {
            asset: math.sqrt(
                max(
                    1e-10,
                    float(
                        covariance.loc[
                            asset,
                            asset,
                        ]
                    ),
                )
            )
            for asset in assets
        }
    )

    inverse_volatility = (
        1.0
        / volatility.replace(
            0.0,
            np.nan,
        )
    ).fillna(0.0)

    inverse_volatility = normalize(
        inverse_volatility
    )

    alpha = candidates.set_index(
        "asset"
    )[
        "ensemble_score"
    ]

    alpha = normalize(
        alpha
    )

    diversification = (
        build_diversification_weights(
            covariance
        )
    )

    risky = (
        alpha * 0.55
        + inverse_volatility * 0.25
        + diversification * 0.20
    )

    investable = (
        1.0
        - CANDIDATE_CASH_FLOOR
    )

    risky = apply_asset_cap(
        risky,
        target_total=investable,
        max_weight=MAX_ASSET_WEIGHT,
    )

    weights = risky.copy()

    cash_weight = max(
        CANDIDATE_CASH_FLOOR,
        1.0
        - float(
            risky.sum()
        ),
    )

    risky_total = max(
        0.0,
        1.0 - cash_weight,
    )

    risky = normalize(
        risky
    ) * risky_total

    weights = risky.copy()
    weights.loc["CASH"] = round(
        cash_weight,
        12,
    )

    total = float(
        weights.sum()
    )

    if abs(
        total - 1.0
    ) > 1e-12:
        weights.loc["CASH"] += (
            1.0 - total
        )

    weights.loc["CASH"] = max(
        CANDIDATE_CASH_FLOOR,
        float(
            weights.loc["CASH"]
        ),
    )

    return weights


def build_covariance(
    returns: pd.DataFrame,
    assets: list[str],
) -> pd.DataFrame:
    if (
        returns.empty
        or len(returns) < MINIMUM_COVARIANCE_DAYS
    ):
        return pd.DataFrame(
            np.diag(
                [0.60 ** 2] * len(
                    assets
                )
            ),
            index=assets,
            columns=assets,
        )

    covariance = (
        returns.cov(
            min_periods=(
                MINIMUM_COVARIANCE_DAYS
            )
        )
        * 365.0
    )

    covariance = covariance.reindex(
        index=assets,
        columns=assets,
    ).fillna(0.0)

    values = covariance.to_numpy(
        dtype=float
    )

    diagonal = np.maximum(
        np.diag(values),
        1e-8,
    )

    target = np.diag(
        diagonal
    )

    values = (
        values * 0.75
        + target * 0.25
    )

    values = nearest_psd(
        values
    )

    return pd.DataFrame(
        values,
        index=assets,
        columns=assets,
    )


def build_diversification_weights(
    covariance: pd.DataFrame,
) -> pd.Series:
    assets = covariance.index.tolist()

    values = covariance.to_numpy(
        dtype=float
    )

    volatility = np.sqrt(
        np.maximum(
            np.diag(values),
            1e-12,
        )
    )

    denominator = np.outer(
        volatility,
        volatility,
    )

    correlation = values / denominator

    np.fill_diagonal(
        correlation,
        0.0,
    )

    average = np.nanmean(
        np.abs(correlation),
        axis=1,
    )

    scores = 1.0 / (
        1.0 + average
    )

    return normalize(
        pd.Series(
            scores,
            index=assets,
        )
    )


def apply_asset_cap(
    weights: pd.Series,
    *,
    target_total: float,
    max_weight: float,
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

        if total_capacity <= 1e-12:
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


def nearest_psd(
    values: np.ndarray,
) -> np.ndarray:
    symmetric = (
        values + values.T
    ) / 2.0

    eigenvalues, eigenvectors = (
        np.linalg.eigh(symmetric)
    )

    eigenvalues = np.maximum(
        eigenvalues,
        1e-10,
    )

    return (
        eigenvectors
        @ np.diag(eigenvalues)
        @ eigenvectors.T
    )


def normalize(
    values: pd.Series,
) -> pd.Series:
    result = pd.to_numeric(
        values,
        errors="coerce",
    ).fillna(0.0).clip(
        lower=0.0,
    )

    total = float(
        result.sum()
    )

    if total <= 1e-12:
        if result.empty:
            return result

        return pd.Series(
            1.0 / len(result),
            index=result.index,
        )

    return result / total

