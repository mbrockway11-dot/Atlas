"""Corpus export utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def export_corpus_rows(
    rows: list[dict],
    output_directory: str | Path,
    metadata: dict,
) -> dict[str, Path]:
    """Export corpus rows to CSV, optional Parquet, and metadata JSON."""
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataframe = pd.DataFrame(rows)

    csv_path = output_dir / "vectors.csv"
    parquet_path = output_dir / "vectors.parquet"
    metadata_path = output_dir / "metadata.json"

    dataframe.to_csv(csv_path, index=False)

    try:
        dataframe.to_parquet(parquet_path, index=False)
    except Exception:
        parquet_path = None

    metadata_path.write_text(
        json.dumps(metadata, indent=2),
        encoding="utf-8",
    )

    return {
        "csv": csv_path,
        "parquet": parquet_path,
        "metadata": metadata_path,
    }