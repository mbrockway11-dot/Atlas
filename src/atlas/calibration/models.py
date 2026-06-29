"""Atlas Calibration Models.

Shared immutable data models for the Atlas calibration subsystem.

Every calibration engine should exchange these dataclasses instead of raw
dictionaries wherever practical.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any


CALIBRATION_MODEL_VERSION = "1.0"


# ---------------------------------------------------------------------
# Individual Profile Metrics
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ProfileMetrics:
    """Numeric measurements extracted from one Identity Stack."""

    identity: str

    node_count: int
    edge_count: int

    density: float
    average_degree: float

    hub_ratio: float
    bridge_ratio: float
    articulation_ratio: float
    leaf_ratio: float

    chain_count: int
    triangle_count: int
    star_count: int
    bottleneck_count: int
    cycle_count: int

    hierarchy_score: float
    branching_score: float
    cyclicity_score: float
    bottleneck_score: float
    persistence_score: float

    truth_ratio: float

    mean_node_coherence: float
    mean_edge_coherence: float

    reduction_ratio: float

    topology_class: str
    resonance_class: str


# ---------------------------------------------------------------------
# Distribution Statistics
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class MetricDistribution:
    """Distribution statistics for one population metric."""

    metric: str

    count: int

    minimum: float
    maximum: float

    mean: float
    median: float

    variance: float
    standard_deviation: float

    first_quartile: float
    third_quartile: float

    percentile_95: float


# ---------------------------------------------------------------------
# Population Baseline
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class PopulationStatistics:
    """Population baseline across every stored profile."""

    version: str

    profile_count: int

    metrics: dict[str, MetricDistribution]


# ---------------------------------------------------------------------
# Z Scores
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ProfileZScores:
    """Population-normalized z-scores."""

    identity: str

    scores: dict[str, float]


# ---------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class ConfidenceReport:
    """Confidence estimates for one profile."""

    identity: str

    overall_confidence: float

    construction_confidence: float
    topology_confidence: float
    genome_confidence: float
    resonance_confidence: float
    reduction_confidence: float
    calibration_confidence: float


# ---------------------------------------------------------------------
# Health Score
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class HealthScore:
    """Overall structural health."""

    identity: str

    score: float

    construction_score: float
    topology_score: float
    genome_score: float
    resonance_score: float
    reduction_score: float
    calibration_score: float


# ---------------------------------------------------------------------
# Similarity Calibration
# ---------------------------------------------------------------------


@dataclass(frozen=True)
class CalibratedSimilarity:
    """Population-aware similarity result."""

    identity_a: str
    identity_b: str

    raw_similarity: float

    calibrated_similarity: float

    confidence: float


# ---------------------------------------------------------------------
# Serialization Helpers
# ---------------------------------------------------------------------


def profile_metrics_to_dict(
    metrics: ProfileMetrics,
) -> dict[str, Any]:
    """Convert ProfileMetrics to dict."""
    return asdict(metrics)


def metric_distribution_to_dict(
    distribution: MetricDistribution,
) -> dict[str, Any]:
    """Convert MetricDistribution to dict."""
    return asdict(distribution)


def population_statistics_to_dict(
    population: PopulationStatistics,
) -> dict[str, Any]:
    """Convert PopulationStatistics to dict."""
    return {
        "version": population.version,
        "profile_count": population.profile_count,
        "metrics": {
            metric: metric_distribution_to_dict(distribution)
            for metric, distribution in population.metrics.items()
        },
    }


def profile_zscores_to_dict(
    scores: ProfileZScores,
) -> dict[str, Any]:
    """Convert ProfileZScores to dict."""
    return asdict(scores)


def confidence_report_to_dict(
    report: ConfidenceReport,
) -> dict[str, Any]:
    """Convert ConfidenceReport to dict."""
    return asdict(report)


def health_score_to_dict(
    score: HealthScore,
) -> dict[str, Any]:
    """Convert HealthScore to dict."""
    return asdict(score)


def calibrated_similarity_to_dict(
    similarity: CalibratedSimilarity,
) -> dict[str, Any]:
    """Convert CalibratedSimilarity to dict."""
    return asdict(similarity)