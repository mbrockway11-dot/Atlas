
"""Prediction challenge train/test splitter."""

from __future__ import annotations

from typing import Any


def split_records(
    records: list[dict[str, Any]],
    *,
    holdout_ratio: float = 0.20,
) -> dict[str, Any]:
    """Deterministically split records into train and holdout sets."""
    if not records:
        return {"train": [], "holdout": []}

    ratio = max(0.05, min(0.50, float(holdout_ratio)))
    holdout_count = max(1, int(round(len(records) * ratio)))

    sorted_records = sorted(records, key=lambda item: str(item.get("profile_key", "")))

    holdout = sorted_records[-holdout_count:]
    train = sorted_records[:-holdout_count]

    return {
        "train": train,
        "holdout": holdout,
        "train_count": len(train),
        "holdout_count": len(holdout),
    }
