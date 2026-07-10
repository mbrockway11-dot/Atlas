
"""Cross-sectional market context for Investment Intelligence v2."""

from __future__ import annotations

import math

import pandas as pd


def build_market_context(
    features: pd.DataFrame,
    rankings: pd.DataFrame,
) -> dict:
    if features is None or features.empty:
        return empty_context()

    frame = features.copy()

    for column in [
        "return_1d",
        "return_7d",
        "return_30d",
        "momentum_30d",
        "momentum_90d",
        "volatility_30d",
        "cross_sectional_score",
        "cross_sectional_rank",
    ]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(
                frame[column],
                errors="coerce",
            )

    asset_count = len(frame)

    positive_1d = positive_ratio(
        frame,
        "return_1d",
    )
    positive_7d = positive_ratio(
        frame,
        "return_7d",
    )
    positive_30d = positive_ratio(
        frame,
        "return_30d",
    )

    leaders = top_assets(
        rankings
        if rankings is not None
        and not rankings.empty
        else frame,
        ascending=False,
    )

    laggards = top_assets(
        rankings
        if rankings is not None
        and not rankings.empty
        else frame,
        ascending=True,
    )

    dispersion = safe_std(
        frame.get("return_30d")
    )

    volatility_dispersion = safe_std(
        frame.get("volatility_30d")
    )

    concentration = rank_concentration(
        rankings
    )

    return {
        "asset_count": asset_count,
        "breadth": {
            "positive_1d_ratio": positive_1d,
            "positive_7d_ratio": positive_7d,
            "positive_30d_ratio": positive_30d,
        },
        "median_returns": {
            "return_1d": safe_median(
                frame.get("return_1d")
            ),
            "return_7d": safe_median(
                frame.get("return_7d")
            ),
            "return_30d": safe_median(
                frame.get("return_30d")
            ),
        },
        "dispersion": {
            "return_30d_std": dispersion,
            "volatility_30d_std": (
                volatility_dispersion
            ),
            "label": dispersion_label(
                dispersion
            ),
        },
        "leaders": leaders,
        "laggards": laggards,
        "rank_concentration": concentration,
        "market_state": classify_state(
            positive_30d,
            safe_median(
                frame.get("return_30d")
            ),
            dispersion,
        ),
    }


def top_assets(
    frame: pd.DataFrame,
    *,
    ascending: bool,
    limit: int = 3,
) -> list[dict]:
    if frame is None or frame.empty:
        return []

    working = frame.copy()

    score_column = None

    for candidate in [
        "final_alpha_score",
        "cross_sectional_score",
        "momentum_30d",
        "return_30d",
    ]:
        if candidate in working.columns:
            score_column = candidate
            break

    if score_column is None:
        return []

    working[score_column] = pd.to_numeric(
        working[score_column],
        errors="coerce",
    )

    working = working.dropna(
        subset=["asset", score_column],
    ).sort_values(
        score_column,
        ascending=ascending,
        kind="stable",
    )

    rows = []

    for _, row in working.head(limit).iterrows():
        rows.append({
            "asset": str(row.get("asset")),
            "score": finite(
                row.get(score_column)
            ),
            "score_field": score_column,
            "rank": finite(
                row.get(
                    "final_rank",
                    row.get(
                        "cross_sectional_rank",
                        0,
                    ),
                )
            ),
        })

    return rows


def rank_concentration(
    rankings: pd.DataFrame,
) -> dict:
    if rankings is None or rankings.empty:
        return {
            "top_two_score_share": 0.0,
            "label": "NO_DATA",
        }

    column = (
        "final_alpha_score"
        if "final_alpha_score"
        in rankings.columns
        else "cross_sectional_score"
        if "cross_sectional_score"
        in rankings.columns
        else None
    )

    if column is None:
        return {
            "top_two_score_share": 0.0,
            "label": "NO_SCORE",
        }

    scores = pd.to_numeric(
        rankings[column],
        errors="coerce",
    ).fillna(0.0).clip(lower=0.0)

    total = float(scores.sum())

    if total <= 0:
        return {
            "top_two_score_share": 0.0,
            "label": "UNDIFFERENTIATED",
        }

    share = float(
        scores.nlargest(2).sum()
        / total
    )

    if share >= 0.80:
        label = "HIGHLY_CONCENTRATED"
    elif share >= 0.55:
        label = "CONCENTRATED"
    else:
        label = "BROAD"

    return {
        "top_two_score_share": round(
            share,
            6,
        ),
        "label": label,
    }


def classify_state(
    breadth: float,
    median_return: float,
    dispersion: float,
) -> str:
    if (
        breadth >= 0.70
        and median_return > 0.05
    ):
        return "BROAD_RISK_ON"

    if (
        breadth <= 0.30
        and median_return < -0.05
    ):
        return "BROAD_RISK_OFF"

    if dispersion >= 0.15:
        return "HIGH_DISPERSION_SELECTION"

    if breadth >= 0.60:
        return "SELECTIVE_RISK_ON"

    if breadth <= 0.40:
        return "SELECTIVE_RISK_OFF"

    return "MIXED"


def positive_ratio(
    frame: pd.DataFrame,
    column: str,
) -> float:
    if column not in frame.columns:
        return 0.0

    values = pd.to_numeric(
        frame[column],
        errors="coerce",
    ).dropna()

    if values.empty:
        return 0.0

    return round(
        float((values > 0).mean()),
        6,
    )


def safe_median(values) -> float:
    if values is None:
        return 0.0

    series = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if series.empty:
        return 0.0

    return round(
        float(series.median()),
        6,
    )


def safe_std(values) -> float:
    if values is None:
        return 0.0

    series = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if series.empty:
        return 0.0

    return round(
        float(series.std(ddof=0)),
        6,
    )


def dispersion_label(value: float) -> str:
    if value >= 0.20:
        return "VERY_HIGH"
    if value >= 0.12:
        return "HIGH"
    if value >= 0.06:
        return "MODERATE"
    return "LOW"


def finite(value) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return 0.0

    return (
        result
        if math.isfinite(result)
        else 0.0
    )


def empty_context() -> dict:
    return {
        "asset_count": 0,
        "breadth": {},
        "median_returns": {},
        "dispersion": {},
        "leaders": [],
        "laggards": [],
        "rank_concentration": {},
        "market_state": "NO_DATA",
    }
