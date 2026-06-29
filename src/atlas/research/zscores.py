"""Atlas calibration engine."""

from __future__ import annotations

from typing import Any

from atlas.research.baselines import get_metric_baseline
from atlas.research.population import RESEARCH_METRICS


CALIBRATED_METRICS = list(RESEARCH_METRICS)


def compute_layer_zscores(
    row: dict[str, Any],
    baselines: dict,
) -> dict[str, float]:
    """Compute z-scores for one planetary construction layer."""
    output = {}

    cipher = row["cipher"]
    planet = row["planet"]

    for metric in CALIBRATED_METRICS:
        baseline = get_metric_baseline(
            baselines,
            cipher,
            planet,
            metric,
        )

        mean = baseline["mean"]
        std = baseline["std"]

        value = float(row[metric])

        if std == 0:
            z = 0.0
        else:
            z = (value - mean) / std

        output[metric] = z

    return output


def compute_profile_zscores(
    rows: list[dict[str, Any]],
    baselines: dict,
) -> list[dict[str, Any]]:
    """Compute calibrated vectors for every layer."""
    calibrated = []

    for row in rows:
        calibrated.append(
            {
                **row,
                "zscores": compute_layer_zscores(
                    row,
                    baselines,
                ),
            }
        )

    return calibrated