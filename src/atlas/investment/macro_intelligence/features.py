"""Macroeconomic feature calculations."""

from __future__ import annotations

import math

import pandas as pd


def calculate_series_features(
    frame: pd.DataFrame,
    *,
    transform: str,
) -> dict:
    """Calculate observed and standardized features for one series."""
    if frame is None or frame.empty:
        return empty_features()

    data = frame.copy()

    data["value"] = pd.to_numeric(
        data["value"],
        errors="coerce",
    )

    data = data.dropna(
        subset=["value"]
    )

    if data.empty:
        return empty_features()

    transformed = apply_transform(
        data["value"],
        transform,
    )

    transformed = transformed.dropna()

    latest_value = finite(
        data["value"].iloc[-1]
    )

    latest_transformed = (
        finite(
            transformed.iloc[-1]
        )
        if not transformed.empty
        else 0.0
    )

    previous_transformed = (
        finite(
            transformed.iloc[-2]
        )
        if len(transformed) >= 2
        else latest_transformed
    )

    change = (
        latest_transformed
        - previous_transformed
    )

    trailing = transformed.tail(
        min(
            260,
            len(transformed),
        )
    )

    z_score = rolling_z_score(
        trailing
    )

    percentile = percentile_rank(
        trailing
    )

    return {
        "observation_date": (
            data["date"].iloc[-1].isoformat()
        ),
        "observation_count": int(
            len(data)
        ),
        "latest_value": round(
            latest_value,
            8,
        ),
        "transformed_value": round(
            latest_transformed,
            8,
        ),
        "transformed_change": round(
            change,
            8,
        ),
        "z_score": round(
            z_score,
            8,
        ),
        "percentile": round(
            percentile,
            8,
        ),
        "trend": classify_trend(
            change
        ),
    }


def apply_transform(
    values: pd.Series,
    transform: str,
) -> pd.Series:
    values = pd.to_numeric(
        values,
        errors="coerce",
    )

    if transform == "year_over_year":
        return values.pct_change(
            periods=12,
            fill_method=None,
        )

    if transform == "percent_change_13":
        return values.pct_change(
            periods=13,
            fill_method=None,
        )

    if transform == "percent_change_52":
        return values.pct_change(
            periods=52,
            fill_method=None,
        )

    if transform == "percent_change_63":
        return values.pct_change(
            periods=63,
            fill_method=None,
        )

    return values


def rolling_z_score(
    values: pd.Series,
) -> float:
    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if len(values) < 5:
        return 0.0

    mean = float(values.mean())
    standard_deviation = float(
        values.std(ddof=0)
    )

    if (
        not math.isfinite(
            standard_deviation
        )
        or standard_deviation <= 1e-12
    ):
        return 0.0

    return finite(
        (
            float(values.iloc[-1])
            - mean
        )
        / standard_deviation
    )


def percentile_rank(
    values: pd.Series,
) -> float:
    values = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if values.empty:
        return 0.5

    latest = float(
        values.iloc[-1]
    )

    return float(
        (values <= latest).mean()
    )


def classify_trend(
    change: float,
) -> str:
    if change > 1e-12:
        return "RISING"

    if change < -1e-12:
        return "FALLING"

    return "FLAT"


def empty_features() -> dict:
    return {
        "observation_date": None,
        "observation_count": 0,
        "latest_value": None,
        "transformed_value": None,
        "transformed_change": None,
        "z_score": None,
        "percentile": None,
        "trend": "NO_DATA",
    }


def finite(
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
