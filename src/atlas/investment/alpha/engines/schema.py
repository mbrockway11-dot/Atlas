"""Canonical schemas for Atlas Alpha Engine Framework v1."""

from __future__ import annotations

from typing import Final

import pandas as pd


ENGINE_SIGNAL_COLUMNS: Final[list[str]] = [
    "timestamp",
    "date",
    "asset",
    "engine_id",
    "engine_version",
    "family",
    "direction",
    "signal",
    "raw_score",
    "normalized_score",
    "confidence",
    "conviction",
    "holding_period",
    "regime",
    "reason_codes",
    "source",
]


def empty_signal_frame() -> pd.DataFrame:
    """Return an empty canonical engine-signal frame."""
    return pd.DataFrame(columns=ENGINE_SIGNAL_COLUMNS)


def normalize_signal_output(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize engine output to the canonical signal contract."""
    if frame is None or frame.empty:
        return empty_signal_frame()

    result = frame.copy()

    for column in ENGINE_SIGNAL_COLUMNS:
        if column not in result.columns:
            result[column] = None

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        errors="coerce",
        utc=True,
    )
    result["date"] = result["timestamp"]

    result["asset"] = result["asset"].astype(str)
    result["engine_id"] = result["engine_id"].astype(str)
    result["engine_version"] = result[
        "engine_version"
    ].astype(str)
    result["family"] = result["family"].astype(str)

    for column in [
        "raw_score",
        "normalized_score",
        "confidence",
        "conviction",
    ]:
        result[column] = pd.to_numeric(
            result[column],
            errors="coerce",
        )

    result["holding_period"] = pd.to_numeric(
        result["holding_period"],
        errors="coerce",
    ).fillna(0).astype(int)

    result = result.dropna(
        subset=[
            "timestamp",
            "asset",
            "engine_id",
            "normalized_score",
        ]
    )

    result["normalized_score"] = result[
        "normalized_score"
    ].clip(0.0, 1.0)

    result["confidence"] = result[
        "confidence"
    ].fillna(0.0).clip(0.0, 1.0)

    result["conviction"] = (
        result["normalized_score"]
        * result["confidence"]
    ).clip(0.0, 1.0)

    result = result.sort_values(
        [
            "timestamp",
            "engine_id",
            "asset",
        ],
        kind="stable",
    ).drop_duplicates(
        subset=[
            "timestamp",
            "engine_id",
            "asset",
        ],
        keep="last",
    )

    return result[
        ENGINE_SIGNAL_COLUMNS
    ].reset_index(drop=True)
