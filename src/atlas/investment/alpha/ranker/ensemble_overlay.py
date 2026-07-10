
"""Overlay Alpha Ensemble v4 confirmation onto cross-sectional ranks."""

from __future__ import annotations

import numpy as np
import pandas as pd


def overlay_ensemble_scores(
    ranked: pd.DataFrame,
    ensemble: pd.DataFrame,
) -> pd.DataFrame:
    """Apply ensemble confirmation without requiring dated signals.

    Market Features v2 produces dated cross-sectional ranks, while Alpha
    Ensemble v4 currently produces the latest asset-level signal snapshot.
    Asset-level signals are therefore joined by asset and applied to the
    latest ranked observation.
    """
    if ranked is None or ranked.empty:
        return ranked

    out = ranked.copy()
    out = normalize_ranked_frame(out)

    if ensemble is None or ensemble.empty:
        return add_no_ensemble_overlay(out)

    normalized = normalize_ensemble_frame(ensemble)

    if normalized.empty:
        return add_no_ensemble_overlay(out)

    merge_keys = ["asset"]

    if (
        "date" in normalized.columns
        and normalized["date"].notna().any()
        and "date" in out.columns
    ):
        merge_keys = ["date", "asset"]

    overlay_columns = [
        column
        for column in [
            *merge_keys,
            "total_weight",
            "net_long_score",
            "ensemble_confidence",
            "confidence_label",
            "strategy_count",
            "ensemble_status",
            "ensemble_direction",
        ]
        if column in normalized.columns
    ]

    normalized = normalized[
        overlay_columns
    ].drop_duplicates(
        subset=merge_keys,
        keep="last",
    )

    merged = out.merge(
        normalized,
        on=merge_keys,
        how="left",
    )

    merged["total_weight"] = numeric_column(
        merged,
        "total_weight",
        0.0,
    )
    merged["net_long_score"] = numeric_column(
        merged,
        "net_long_score",
        0.0,
    )
    merged["ensemble_confidence"] = numeric_column(
        merged,
        "ensemble_confidence",
        0.0,
    )
    merged["strategy_count"] = numeric_column(
        merged,
        "strategy_count",
        0.0,
    ).astype(int)

    merged["ensemble_confirmed"] = (
        merged["net_long_score"] > 0
    )

    merged["ensemble_bonus"] = (
        merged["ensemble_confidence"]
        * merged["net_long_score"]
        * 0.25
    )

    merged["final_alpha_score"] = (
        numeric_column(
            merged,
            "raw_alpha_score",
            0.0,
        )
        + merged["ensemble_bonus"]
    )

    group_column = (
        "date"
        if "date" in merged.columns
        else "timestamp"
        if "timestamp" in merged.columns
        else None
    )

    if group_column:
        merged["final_rank"] = (
            merged.groupby(group_column)[
                "final_alpha_score"
            ]
            .rank(
                ascending=False,
                method="min",
            )
        )
    else:
        merged["final_rank"] = (
            merged["final_alpha_score"]
            .rank(
                ascending=False,
                method="min",
            )
        )

    merged["final_rank_label"] = (
        merged["final_rank"].apply(label_final_rank)
    )

    return merged


def normalize_ranked_frame(
    ranked: pd.DataFrame,
) -> pd.DataFrame:
    result = ranked.copy()

    if "timestamp" in result.columns:
        result["timestamp"] = pd.to_datetime(
            result["timestamp"],
            errors="coerce",
            utc=True,
        )

    if "date" in result.columns:
        result["date"] = pd.to_datetime(
            result["date"],
            errors="coerce",
            utc=True,
        )
    elif "timestamp" in result.columns:
        result["date"] = result["timestamp"]

    if "asset" in result.columns:
        result["asset"] = result["asset"].astype(str)

    return result


def normalize_ensemble_frame(
    ensemble: pd.DataFrame,
) -> pd.DataFrame:
    result = ensemble.copy()

    if "asset" not in result.columns:
        return pd.DataFrame()

    result["asset"] = result["asset"].astype(str)

    if "timestamp" in result.columns:
        result["timestamp"] = pd.to_datetime(
            result["timestamp"],
            errors="coerce",
            utc=True,
        )

    if "date" in result.columns:
        result["date"] = pd.to_datetime(
            result["date"],
            errors="coerce",
            utc=True,
        )
    elif "timestamp" in result.columns:
        result["date"] = result["timestamp"]

    # Translate Alpha Ensemble v4 fields into the legacy overlay schema.
    if "ensemble_confidence" not in result.columns:
        if "confidence" in result.columns:
            result["ensemble_confidence"] = pd.to_numeric(
                result["confidence"],
                errors="coerce",
            ).fillna(0.0)
        elif "ensemble_score" in result.columns:
            result["ensemble_confidence"] = pd.to_numeric(
                result["ensemble_score"],
                errors="coerce",
            ).fillna(0.0)
        else:
            result["ensemble_confidence"] = 0.0

    if "net_long_score" not in result.columns:
        raw_score = pd.to_numeric(
            result.get(
                "raw_score",
                result.get("ensemble_score", 0.0),
            ),
            errors="coerce",
        )

        if not isinstance(raw_score, pd.Series):
            raw_score = pd.Series(
                raw_score,
                index=result.index,
                dtype=float,
            )

        direction = result.get(
            "direction",
            result.get("signal_direction", "NEUTRAL"),
        )

        if not isinstance(direction, pd.Series):
            direction = pd.Series(
                direction,
                index=result.index,
            )

        direction = direction.astype(str).str.upper()

        sign = np.select(
            [
                direction.isin(
                    ["LONG", "BUY", "BULLISH", "UP"]
                ),
                direction.isin(
                    ["SHORT", "SELL", "BEARISH", "DOWN"]
                ),
            ],
            [1.0, -1.0],
            default=0.0,
        )

        result["net_long_score"] = (
            raw_score.fillna(0.0)
            * sign
        )

    if "total_weight" not in result.columns:
        result["total_weight"] = result[
            "ensemble_confidence"
        ]

    if "strategy_count" not in result.columns:
        result["strategy_count"] = 1

    if "confidence_label" not in result.columns:
        result["confidence_label"] = result[
            "ensemble_confidence"
        ].apply(confidence_label)

    if "status" in result.columns:
        result["ensemble_status"] = result["status"]

    if "direction" in result.columns:
        result["ensemble_direction"] = result[
            "direction"
        ]

    return result


def add_no_ensemble_overlay(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    result = frame.copy()

    result["total_weight"] = 0.0
    result["net_long_score"] = 0.0
    result["ensemble_confidence"] = 0.0
    result["confidence_label"] = "NONE"
    result["strategy_count"] = 0
    result["ensemble_confirmed"] = False
    result["ensemble_bonus"] = 0.0
    result["final_alpha_score"] = numeric_column(
        result,
        "raw_alpha_score",
        0.0,
    )

    group_column = (
        "date"
        if "date" in result.columns
        else "timestamp"
        if "timestamp" in result.columns
        else None
    )

    if group_column:
        result["final_rank"] = (
            result.groupby(group_column)[
                "final_alpha_score"
            ]
            .rank(
                ascending=False,
                method="min",
            )
        )
    else:
        result["final_rank"] = (
            result["final_alpha_score"]
            .rank(
                ascending=False,
                method="min",
            )
        )

    result["final_rank_label"] = (
        result["final_rank"].apply(label_final_rank)
    )

    return result


def numeric_column(
    frame: pd.DataFrame,
    column: str,
    default: float,
) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(
            default,
            index=frame.index,
            dtype=float,
        )

    return pd.to_numeric(
        frame[column],
        errors="coerce",
    ).fillna(default)


def confidence_label(value) -> str:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return "NONE"

    if score >= 0.80:
        return "HIGH"
    if score >= 0.60:
        return "MODERATE"
    if score > 0.0:
        return "LIMITED"
    return "NONE"


def label_final_rank(rank) -> str:
    try:
        value = int(rank)
    except (TypeError, ValueError):
        return "unranked"

    if value == 1:
        return "highest_conviction"

    if value <= 3:
        return "portfolio_candidate"

    return "watchlist"
