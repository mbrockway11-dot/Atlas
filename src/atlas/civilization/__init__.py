"""Atlas Z-Score Engine.

Convert raw profile metrics into population-normalized z-scores.

This module consumes:
    ProfileMetrics
    PopulationStatistics

It does not load files, save files, or build population baselines.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.calibration.models import (
    PopulationStatistics,
    ProfileMetrics,
)
from atlas.calibration.population_statistics import (
    profile_metrics_to_numeric_dict,
)


ZSCORE_ENGINE_VERSION = "1.0"


@dataclass(frozen=True)
class ProfileZScoreReport:
    """Z-score report for one profile."""

    version: str
    identity: str
    scores: dict[str, float]
    summary: dict[str, Any]


def compute_profile_zscores(
    metrics: ProfileMetrics,
    population: PopulationStatistics,
) -> ProfileZScoreReport:
    """Compute z-scores for one profile against population statistics."""
    raw_metrics = profile_metrics_to_numeric_dict(metrics)

    scores: dict[str, float] = {}

    for metric_name, value in raw_metrics.items():
        distribution = population.metrics.get(metric_name)

        if distribution is None:
            continue

        scores[metric_name] = compute_zscore(
            value=float(value),
            mean=distribution.mean,
            standard_deviation=distribution.standard_deviation,
        )

    summary = build_zscore_summary(scores)

    return ProfileZScoreReport(
        version=ZSCORE_ENGINE_VERSION,
        identity=metrics.identity,
        scores=scores,
        summary=summary,
    )


def compute_zscore(
    *,
    value: float,
    mean: float,
    standard_deviation: float,
) -> float:
    """Compute one bounded-safe z-score."""
    if standard_deviation == 0:
        return 0.0

    return (value - mean) / standard_deviation


def build_zscore_summary(
    scores: dict[str, float],
) -> dict[str, Any]:
    """Build summary metadata for a z-score report."""
    if not scores:
        return {
            "metric_count": 0,
            "max_abs_zscore": 0.0,
            "mean_abs_zscore": 0.0,
            "largest_positive_metric": None,
            "largest_negative_metric": None,
        }

    absolute_scores = {
        metric: abs(score)
        for metric, score in scores.items()
    }

    largest_positive_metric = max(
        scores,
        key=lambda metric: scores[metric],
    )

    largest_negative_metric = min(
        scores,
        key=lambda metric: scores[metric],
    )

    return {
        "metric_count": len(scores),
        "max_abs_zscore": max(absolute_scores.values()),
        "mean_abs_zscore": sum(absolute_scores.values()) / len(absolute_scores),
        "largest_positive_metric": largest_positive_metric,
        "largest_positive_zscore": scores[largest_positive_metric],
        "largest_negative_metric": largest_negative_metric,
        "largest_negative_zscore": scores[largest_negative_metric],
    }


def zscore_report_to_dict(
    report: ProfileZScoreReport,
) -> dict[str, Any]:
    """Convert z-score report to JSON-safe dictionary."""
    return asdict(report)
