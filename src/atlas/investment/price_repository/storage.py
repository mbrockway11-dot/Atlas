
"""Incremental segmented-price storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


def segment_path(
    root: Path,
    asset: str,
    timeframe: str,
) -> Path:
    return root / asset / f"{timeframe}.csv"


def read_segment(path: Path) -> pd.DataFrame:
    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return pd.DataFrame()

    try:
        frame = pd.read_csv(path)
    except (
        EmptyDataError,
        ParserError,
        UnicodeDecodeError,
    ):
        return pd.DataFrame()

    if "timestamp" in frame.columns:
        frame["timestamp"] = pd.to_datetime(
            frame["timestamp"],
            errors="coerce",
            utc=True,
        )

    return frame


def merge_segment(
    existing: pd.DataFrame,
    incoming: pd.DataFrame,
) -> pd.DataFrame:
    frames = [
        frame
        for frame in [existing, incoming]
        if frame is not None and not frame.empty
    ]

    if not frames:
        return pd.DataFrame()

    merged = pd.concat(
        frames,
        ignore_index=True,
    )

    merged["timestamp"] = pd.to_datetime(
        merged["timestamp"],
        errors="coerce",
        utc=True,
    )

    merged = merged.dropna(
        subset=["timestamp", "asset", "close"],
    )

    merged = merged.sort_values(
        ["timestamp"],
        kind="stable",
    ).drop_duplicates(
        subset=["asset", "timeframe", "timestamp"],
        keep="last",
    )

    return merged.reset_index(drop=True)


def write_segment(
    path: Path,
    frame: pd.DataFrame,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    frame.to_csv(path, index=False)


def write_manifest(
    root: Path,
    manifest: dict[str, Any],
) -> Path:
    root.mkdir(parents=True, exist_ok=True)

    target = root / "manifest.json"
    target.write_text(
        json.dumps(
            manifest,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    return target
