"""Atlas empirical baseline builder."""

from __future__ import annotations

from typing import Any

from atlas.research.population import build_population_statistics


def build_population_baselines(
    rows: list[dict[str, Any]],
) -> dict[tuple[str, str], dict[str, Any]]:
    """
    Build deterministic empirical baselines.

    Parameters
    ----------
    rows
        Output of build_research_matrix()

    Returns
    -------
    dict

        {
            ("ordinal","Saturn"):
            {
                "cipher": "...",
                "planet": "...",
                "sample_size": 100,
                "metrics":
                {
                    ...
                }
            }
        }
    """

    statistics = build_population_statistics(rows)

    baselines = {}

    for key, value in statistics.items():

        baselines[key] = {
            "cipher": value["cipher"],
            "planet": value["planet"],
            "sample_size": value["sample_size"],
            "metrics": value["metrics"],
        }

    return baselines


def get_metric_baseline(
    baselines: dict,
    cipher: str,
    planet: str,
    metric: str,
) -> dict[str, float]:
    """
    Lookup one metric baseline.

    Returns

    {
        mean
        std
        minimum
        maximum
    }
    """

    layer = baselines[
        (
            cipher,
            planet,
        )
    ]

    return layer["metrics"][metric]