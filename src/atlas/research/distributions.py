"""Distribution analysis for Atlas research."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, median, pstdev
from typing import Any

from atlas.research.population import RESEARCH_METRICS


def build_metric_distributions(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Analyze metric distributions for each (cipher, planet) group."""
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        grouped[
            (
                row["cipher"],
                row["planet"],
            )
        ].append(row)

    output = {}

    for key, group in grouped.items():
        cipher, planet = key

        metrics = {}

        for metric in RESEARCH_METRICS:
            values = sorted(
                float(row[metric])
                for row in group
            )

            metrics[metric] = summarize_distribution(values)

        output[key] = {
            "cipher": cipher,
            "planet": planet,
            "sample_size": len(group),
            "metrics": metrics,
        }

    return output


def summarize_distribution(
    values: list[float],
) -> dict[str, Any]:
    """Summarize one numeric distribution."""
    if not values:
        return {}

    std = 0.0 if len(values) == 1 else pstdev(values)

    q1 = percentile(values, 25)
    q2 = percentile(values, 50)
    q3 = percentile(values, 75)

    iqr = q3 - q1

    return {
        "count": len(values),
        "mean": mean(values),
        "median": median(values),
        "std": std,
        "minimum": values[0],
        "maximum": values[-1],
        "q1": q1,
        "q2": q2,
        "q3": q3,
        "iqr": iqr,
        "range": values[-1] - values[0],
    }


def percentile(
    values: list[float],
    percent: float,
) -> float:
    """Return percentile using linear interpolation."""
    if not values:
        return 0.0

    index = (len(values) - 1) * (percent / 100)

    lower = int(index)
    upper = min(lower + 1, len(values) - 1)

    weight = index - lower

    return (
        values[lower] * (1 - weight)
        + values[upper] * weight
    )