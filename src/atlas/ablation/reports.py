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


def summarize_global_ablation_results(results) -> dict[str, Any]:
    """Summarize corpus-wide ablation results."""
    rows = [
        result.summary
        for result in results
    ]

    ranked_by_importance = sorted(
        rows,
        key=lambda row: row["importance_score"],
        reverse=True,
    )

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
        "ranked_by_importance": ranked_by_importance,
        "ranked_by_rank_shift": ranked_by_rank_shift,
        "ranked_by_similarity_delta": ranked_by_similarity_delta,
    }


def render_global_ablation_report_text(results) -> str:
    """Render plain-text global ablation report."""
    summary = summarize_global_ablation_results(results)

    lines = [
        "Atlas Global Ablation Report",
        "=" * 56,
        f"Experiments: {summary['experiment_count']}",
        "",
        "Most important experiments:",
    ]

    for row in summary["ranked_by_importance"][:10]:
        lines.append(
            f"- {row['experiment_name']}: "
            f"importance={row['importance_score']:.4f}, "
            f"mean_rank_shift={row['mean_rank_shift']:.4f}, "
            f"mean_changed_profiles={row['mean_changed_profiles']:.4f}, "
            f"mean_abs_delta={row['mean_absolute_similarity_delta']:.4f}"
        )

    lines.extend(
        [
            "",
            "Most disruptive by corpus-wide rank shift:",
        ]
    )

    for row in summary["ranked_by_rank_shift"][:10]:
        lines.append(
            f"- {row['experiment_name']}: "
            f"mean_rank_shift={row['mean_rank_shift']:.4f}, "
            f"mean_max_rank_shift={row['mean_max_rank_shift']:.4f}"
        )

    lines.extend(
        [
            "",
            "Most disruptive by corpus-wide similarity delta:",
        ]
    )

    for row in summary["ranked_by_similarity_delta"][:10]:
        lines.append(
            f"- {row['experiment_name']}: "
            f"mean_abs_delta={row['mean_absolute_similarity_delta']:.4f}, "
            f"max_abs_delta={row['max_absolute_similarity_delta']:.4f}"
        )

    return "\n".join(lines)