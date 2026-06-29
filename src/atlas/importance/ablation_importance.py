"""Feature importance derived from global ablation results."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class AblationImportanceRow:
    """One ablation-derived importance row."""

    experiment_name: str
    description: str
    importance_score: float
    mean_rank_shift: float
    mean_changed_profiles: float
    mean_absolute_similarity_delta: float
    max_absolute_similarity_delta: float
    mean_removed_column_count: float
    mean_remaining_feature_count: float


def load_global_ablation_report(
    path: str | Path = "research/corpus/global_ablation_report.json",
) -> dict[str, Any]:
    """Load global ablation JSON report."""
    report_path = Path(path)

    if not report_path.exists():
        raise FileNotFoundError(f"Global ablation report not found: {report_path}")

    return json.loads(report_path.read_text(encoding="utf-8"))


def build_importance_from_global_ablation(
    report: dict[str, Any],
) -> list[AblationImportanceRow]:
    """Build ranked importance rows from global ablation report."""
    rows = []

    for result in report.get("results", []):
        summary = result.get("summary", {})

        rows.append(
            AblationImportanceRow(
                experiment_name=str(summary.get("experiment_name", "")),
                description=str(summary.get("description", "")),
                importance_score=float(summary.get("importance_score", 0.0)),
                mean_rank_shift=float(summary.get("mean_rank_shift", 0.0)),
                mean_changed_profiles=float(
                    summary.get("mean_changed_profiles", 0.0)
                ),
                mean_absolute_similarity_delta=float(
                    summary.get("mean_absolute_similarity_delta", 0.0)
                ),
                max_absolute_similarity_delta=float(
                    summary.get("max_absolute_similarity_delta", 0.0)
                ),
                mean_removed_column_count=float(
                    summary.get("mean_removed_column_count", 0.0)
                ),
                mean_remaining_feature_count=float(
                    summary.get("mean_remaining_feature_count", 0.0)
                ),
            )
        )

    return sorted(
        rows,
        key=lambda row: row.importance_score,
        reverse=True,
    )


def importance_rows_to_dicts(
    rows: list[AblationImportanceRow],
) -> list[dict[str, Any]]:
    """Convert importance rows to dictionaries."""
    return [
        {
            "experiment_name": row.experiment_name,
            "description": row.description,
            "importance_score": row.importance_score,
            "mean_rank_shift": row.mean_rank_shift,
            "mean_changed_profiles": row.mean_changed_profiles,
            "mean_absolute_similarity_delta": row.mean_absolute_similarity_delta,
            "max_absolute_similarity_delta": row.max_absolute_similarity_delta,
            "mean_removed_column_count": row.mean_removed_column_count,
            "mean_remaining_feature_count": row.mean_remaining_feature_count,
        }
        for row in rows
    ]


def export_importance_report(
    rows: list[AblationImportanceRow],
    output_directory: str | Path = "research/corpus",
) -> dict[str, Path]:
    """Export importance rows to CSV and JSON."""
    output_dir = Path(output_directory)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = importance_rows_to_dicts(rows)
    dataframe = pd.DataFrame(data)

    csv_path = output_dir / "feature_importance.csv"
    json_path = output_dir / "feature_importance.json"

    dataframe.to_csv(csv_path, index=False)
    json_path.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8",
    )

    return {
        "csv": csv_path,
        "json": json_path,
    }


def render_importance_report_text(
    rows: list[AblationImportanceRow],
    top_n: int = 10,
) -> str:
    """Render human-readable importance report."""
    lines = [
        "Atlas Feature Importance Report",
        "=" * 56,
        f"Rows: {len(rows)}",
        "",
        "Top importance rows:",
    ]

    for index, row in enumerate(rows[:top_n], start=1):
        lines.append(
            f"{index:>2}. {row.experiment_name:<20} "
            f"importance={row.importance_score:.4f} "
            f"rank_shift={row.mean_rank_shift:.4f} "
            f"changed={row.mean_changed_profiles:.4f} "
            f"mean_abs_delta={row.mean_absolute_similarity_delta:.4f}"
        )

    return "\n".join(lines)