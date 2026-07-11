"""Covariance and portfolio-risk calculations."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from atlas.investment.portfolio_optimizer.constraints import (
    COVARIANCE_LOOKBACK,
    COVARIANCE_SHRINKAGE,
    MIN_COVARIANCE_OBSERVATIONS,
)


def build_return_matrix(
    history: pd.DataFrame,
    assets: list[str],
) -> pd.DataFrame:
    """Build deterministic daily asset-return matrix."""
    if (
        history is None
        or history.empty
        or not assets
    ):
        return pd.DataFrame()

    frame = history.copy()

    temporal = find_temporal_column(
        frame
    )

    if (
        temporal is None
        or "asset" not in frame.columns
        or "close" not in frame.columns
    ):
        return pd.DataFrame()

    frame["timestamp"] = pd.to_datetime(
        frame[temporal],
        errors="coerce",
        utc=True,
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
    )

    frame["close"] = pd.to_numeric(
        frame["close"],
        errors="coerce",
    )

    frame = frame[
        frame["asset"].isin(assets)
    ].dropna(
        subset=[
            "timestamp",
            "asset",
            "close",
        ]
    )

    pivot = frame.pivot_table(
        index="timestamp",
        columns="asset",
        values="close",
        aggfunc="last",
    ).sort_index()

    pivot = pivot.tail(
        COVARIANCE_LOOKBACK + 1
    )

    returns = pivot.pct_change(
        fill_method=None
    )

    return returns.replace(
        [np.inf, -np.inf],
        np.nan,
    )


def build_covariance_matrix(
    returns: pd.DataFrame,
    assets: list[str],
) -> pd.DataFrame:
    """Build annualized shrinkage covariance matrix."""
    if not assets:
        return pd.DataFrame()

    available = [
        asset
        for asset in assets
        if asset in returns.columns
    ]

    if not available:
        return fallback_covariance(
            assets
        )

    sample = returns[
        available
    ].dropna(
        how="all"
    )

    if len(sample) < MIN_COVARIANCE_OBSERVATIONS:
        return fallback_covariance(
            assets,
            returns=sample,
        )

    sample_covariance = sample.cov(
        min_periods=MIN_COVARIANCE_OBSERVATIONS
    ) * 365.0

    sample_covariance = sample_covariance.reindex(
        index=assets,
        columns=assets,
    )

    variances = np.diag(
        sample_covariance.fillna(0.0)
        .to_numpy(dtype=float)
    )

    target = np.diag(
        np.maximum(
            variances,
            1e-8,
        )
    )

    sample_values = (
        sample_covariance
        .fillna(0.0)
        .to_numpy(dtype=float)
    )

    shrunk = (
        sample_values
        * (
            1.0
            - COVARIANCE_SHRINKAGE
        )
        + target
        * COVARIANCE_SHRINKAGE
    )

    shrunk = nearest_psd(
        shrunk
    )

    return pd.DataFrame(
        shrunk,
        index=assets,
        columns=assets,
    )


def calculate_portfolio_risk(
    weights: pd.Series,
    covariance: pd.DataFrame,
) -> dict:
    """Calculate annualized portfolio risk metrics."""
    assets = [
        asset
        for asset in weights.index
        if asset != "CASH"
        and asset in covariance.index
    ]

    if not assets:
        return {
            "annualized_volatility": 0.0,
            "diversification_ratio": 0.0,
            "effective_asset_count": 0.0,
            "largest_asset_weight": 0.0,
            "risk_contributions": {},
        }

    vector = (
        weights.reindex(assets)
        .fillna(0.0)
        .to_numpy(dtype=float)
    )

    matrix = covariance.loc[
        assets,
        assets,
    ].to_numpy(dtype=float)

    variance = float(
        vector.T @ matrix @ vector
    )

    volatility = math.sqrt(
        max(
            0.0,
            variance,
        )
    )

    asset_volatility = np.sqrt(
        np.maximum(
            np.diag(matrix),
            0.0,
        )
    )

    weighted_standalone = float(
        np.dot(
            vector,
            asset_volatility,
        )
    )

    diversification_ratio = (
        weighted_standalone
        / volatility
        if volatility > 1e-12
        else 0.0
    )

    effective_count = (
        1.0
        / float(
            np.sum(
                vector ** 2
            )
        )
        if np.sum(
            vector ** 2
        ) > 1e-12
        else 0.0
    )

    marginal = (
        matrix @ vector
        if volatility > 1e-12
        else np.zeros_like(vector)
    )

    risk_contributions = (
        vector
        * marginal
        / variance
        if variance > 1e-12
        else np.zeros_like(vector)
    )

    return {
        "annualized_volatility": round(
            volatility,
            8,
        ),
        "diversification_ratio": round(
            diversification_ratio,
            8,
        ),
        "effective_asset_count": round(
            effective_count,
            8,
        ),
        "largest_asset_weight": round(
            float(
                vector.max()
            ),
            8,
        ),
        "risk_contributions": {
            asset: round(
                float(value),
                8,
            )
            for asset, value in zip(
                assets,
                risk_contributions,
                strict=False,
            )
        },
    }


def fallback_covariance(
    assets: list[str],
    returns: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Build conservative diagonal covariance when history is sparse."""
    variances = []

    for asset in assets:
        volatility = 0.60

        if (
            returns is not None
            and asset in returns.columns
        ):
            observed = pd.to_numeric(
                returns[asset],
                errors="coerce",
            ).dropna()

            if len(observed) >= 5:
                volatility = max(
                    0.20,
                    float(
                        observed.std(
                            ddof=0
                        )
                        * math.sqrt(365.0)
                    ),
                )

        variances.append(
            volatility ** 2
        )

    return pd.DataFrame(
        np.diag(variances),
        index=assets,
        columns=assets,
    )


def nearest_psd(
    matrix: np.ndarray,
) -> np.ndarray:
    """Project numerical covariance errors onto PSD space."""
    symmetric = (
        matrix + matrix.T
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


def find_temporal_column(
    frame: pd.DataFrame,
) -> str | None:
    for candidate in [
        "timestamp",
        "date",
        "datetime",
        "time",
    ]:
        if candidate in frame.columns:
            return candidate

    return None
