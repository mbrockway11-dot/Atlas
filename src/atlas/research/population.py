"""Population statistics for Atlas research."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev
from typing import Any


RESEARCH_METRICS = [
    "node_coverage",
    "density",
    "entropy",
    "axis_strength",
    "unique_nodes",
    "unique_edges",
    "max_node_weight",
    "max_depth",
    "self_loops",
]


def build_population_statistics(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute descriptive statistics grouped by (cipher, planet)."""
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        key = (
            row["cipher"],
            row["planet"],
        )
        groups[key].append(row)

    output = {}

    for key, group in groups.items():
        cipher, planet = key

        output[key] = {
            "cipher": cipher,
            "planet": planet,
            "sample_size": len(group),
            "metrics": summarize_metrics(group),
        }

    return output


def summarize_metrics(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize structural research metrics."""
    summary = {}

    for metric in RESEARCH_METRICS:
        values = [
            float(row[metric])
            for row in rows
        ]

        std = 0.0 if len(values) == 1 else pstdev(values)

        summary[metric] = {
            "mean": mean(values),
            "std": std,
            "minimum": min(values),
            "maximum": max(values),
        }

    return summary