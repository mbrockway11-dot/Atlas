"""Corpus statistics."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_corpus_statistics(
    rows: list[dict],
    output_directory: str | Path | None = None,
) -> dict:
    """Build summary statistics for corpus rows."""
    dataframe = pd.DataFrame(rows)

    numeric = dataframe.select_dtypes(include=["number"])

    statistics = {
        "profile_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "numeric_column_count": int(len(numeric.columns)),
        "numeric_means": numeric.mean().to_dict(),
        "numeric_std": numeric.std(ddof=0).fillna(0.0).to_dict(),
        "numeric_min": numeric.min().to_dict(),
        "numeric_max": numeric.max().to_dict(),
    }

    if output_directory is not None:
        output_dir = Path(output_directory)
        output_dir.mkdir(parents=True, exist_ok=True)

        path = output_dir / "statistics.json"
        path.write_text(
            json.dumps(statistics, indent=2),
            encoding="utf-8",
        )

    return statistics