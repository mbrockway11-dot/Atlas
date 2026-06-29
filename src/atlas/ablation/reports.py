"""Ablation report utilities."""

from __future__ import annotations

from typing import Any

from atlas.ablation.harness import AblationResult


def summarize_ablation_results(
    results: list[AblationResult],
) -> dict[str, Any]:
    """Summarize multiple ablation results."""
    rows = [
        result.summary
        for result in results
    ]

    ranked_by_rank_shift = sorted(
        rows,
        key=lambda row: row["mean_rank_shift"],
        reverse=True,
    )

    ranked_by_similarity_delta = sorted(
        rows,
        key=lambda row: row["mean_absolute_similarity_delta"],
        reverse=True,
    )

    return {
        "experiment_count": len(results),
        "ranked_by_rank_shift": ranked_by_rank_shift,
        "ranked_by_similarity_delta": ranked_by_similarity_delta,
    }


def render_ablation_report_text(
    results: list[AblationResult],
) -> str:
    """Render plain-text ablation report."""
    summary = summarize_ablation_results(results)

    lines = [
        "Atlas Ablation Report",
        "=" * 56,
        f"Experiments: {summary['experiment_count']}",
        "",
        "Most disruptive by rank shift:",
    ]

    for row in summary["ranked_by_rank_shift"][:10]:
        lines.append(
            f"- {row['experiment_name']}: "
            f"mean_rank_shift={row['mean_rank_shift']:.4f}, "
            f"changed_profiles={row['changed_profiles']}"
        )

    lines.extend(
        [
            "",
            "Most disruptive by similarity delta:",
        ]
    )

    for row in summary["ranked_by_similarity_delta"][:10]:
        lines.append(
            f"- {row['experiment_name']}: "
            f"mean_abs_delta={row['mean_absolute_similarity_delta']:.4f}, "
            f"removed_columns={row['removed_column_count']}"
        )

    return "\n".join(lines)