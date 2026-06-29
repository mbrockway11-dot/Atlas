"""Atlas Population Statistics Engine.

Build statistical baselines across every Identity Stack in the
Atlas Profile Library.

This module intentionally performs NO calibration.

It only measures the population.

Later engines consume these measurements:

    baseline_library.py
    zscore_engine.py
    rarity_engine.py
    confidence_engine.py
    similarity_calibration.py
    health_score.py
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from atlas.calibration.models import (
    MetricDistribution,
    PopulationStatistics,
    ProfileMetrics,
)


POPULATION_STATISTICS_VERSION = "1.0"

DEFAULT_PROFILE_FILENAME = "identity_stack.json"
LEGACY_PROFILE_FILENAME = "profile.acf.json"


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------


def build_population_statistics(
    profile_library: Path,
) -> PopulationStatistics:
    """Build statistical distributions across every profile."""
    metrics = load_population_metrics(profile_library)

    distributions = compute_distributions(metrics)

    return PopulationStatistics(
        version=POPULATION_STATISTICS_VERSION,
        profile_count=len(metrics),
        metrics=distributions,
    )


def load_population_metrics(
    profile_library: Path,
) -> list[ProfileMetrics]:
    """Load every profile and extract standardized metrics."""

    profile_metrics: list[ProfileMetrics] = []

    if not profile_library.exists():
        return profile_metrics

    import json

    for directory in sorted(profile_library.iterdir()):

        if not directory.is_dir():
            continue
        stack_file = directory / DEFAULT_PROFILE_FILENAME

        if not stack_file.exists():
            stack_file = directory / LEGACY_PROFILE_FILENAME

        if not stack_file.exists():
            continue

        try:
            stack = json.loads(
                stack_file.read_text(
                    encoding="utf-8",
                )
            )

            profile_metrics.append(
                extract_profile_metrics(
                    stack,
                )
            )

        except Exception:
            continue

    return profile_metrics


def compute_distributions(
    metrics: list[ProfileMetrics],
) -> dict[str, MetricDistribution]:
    """Compute every numeric distribution in the population."""

    buckets: dict[str, list[float]] = defaultdict(list)

    for profile in metrics:
        values = profile_metrics_to_numeric_dict(profile)

        for metric_name, value in values.items():
            numeric = float(value)

            if math.isnan(numeric):
                continue

            buckets[metric_name].append(numeric)

    distributions: dict[str, MetricDistribution] = {}

    for metric_name, values in buckets.items():
        distributions[metric_name] = build_distribution(
            metric_name,
            values,
        )

    return distributions


# ------------------------------------------------------------
# Metric Extraction
# ------------------------------------------------------------

def extract_profile_metrics(
    stack: dict[str, Any],
) -> ProfileMetrics:
    """Extract standardized measurements from one Identity Stack."""

    cig = stack.get("cig", {})
    stg = stack.get("stg", {})
    motifs = stack.get("motifs", {})
    genome = stack.get("genome", {})
    topology = stack.get("topology", {})
    resonance = stack.get("resonance", {})

    analyzed_graph = cig.get("analyzed_graph", {})

    nodes = analyzed_graph.get("nodes", {})
    edges = analyzed_graph.get("edges", {})

    node_count = len(nodes)
    edge_count = len(edges)

    density = graph_density(
        node_count=node_count,
        edge_count=edge_count,
    )

    average_degree = graph_average_degree(
        node_count=node_count,
        edge_count=edge_count,
    )

    analysis = analyzed_graph.get("analysis", {})

    hub_ratio = safe_ratio(
        analysis.get("hub_count", 0),
        node_count,
    )

    bridge_ratio = safe_ratio(
        analysis.get("bridge_count", 0),
        edge_count,
    )

    articulation_ratio = safe_ratio(
        analysis.get(
            "articulation_point_count",
            0,
        ),
        node_count,
    )

    leaf_ratio = safe_ratio(
        analysis.get("leaf_count", 0),
        node_count,
    )

    node_truth = mean_truth_score(
        stg.get("nodes", {}),
    )

    node_coherence = mean_coherence_score(
        nodes,
    )

    edge_coherence = mean_coherence_score(
        edges,
    )

    reduction_ratio = compute_reduction_ratio(
        cig,
        stg,
    )

    return ProfileMetrics(
        identity=stack.get("name", "Unknown"),

        node_count=node_count,
        edge_count=edge_count,

        density=density,
        average_degree=average_degree,

        hub_ratio=hub_ratio,
        bridge_ratio=bridge_ratio,
        articulation_ratio=articulation_ratio,
        leaf_ratio=leaf_ratio,

        chain_count=motifs.get(
            "chain_count",
            0,
        ),

        triangle_count=motifs.get(
            "triangle_count",
            0,
        ),

        star_count=motifs.get(
            "star_count",
            0,
        ),

        bottleneck_count=motifs.get(
            "bottleneck_count",
            0,
        ),

        cycle_count=motifs.get(
            "cycle_like_count",
            0,
        ),

        hierarchy_score=genome.get(
            "hierarchy_score",
            0.0,
        ),

        branching_score=genome.get(
            "branching_score",
            0.0,
        ),

        cyclicity_score=genome.get(
            "cyclicity_score",
            0.0,
        ),

        bottleneck_score=genome.get(
            "bottleneck_score",
            0.0,
        ),

        persistence_score=genome.get(
            "persistence_score",
            0.0,
        ),

        truth_ratio=node_truth,

        mean_node_coherence=node_coherence,
        mean_edge_coherence=edge_coherence,

        reduction_ratio=reduction_ratio,

        topology_class=topology.get(
            "topology_class",
            "unknown",
        ),

        resonance_class=resonance.get(
            "resonance_class",
            "unknown",
        ),
    )


def profile_metrics_to_numeric_dict(
    metrics: ProfileMetrics,
) -> dict[str, float]:
    """Convert ProfileMetrics into numeric metrics only."""

    return {
        "node_count": metrics.node_count,
        "edge_count": metrics.edge_count,

        "density": metrics.density,
        "average_degree": metrics.average_degree,

        "hub_ratio": metrics.hub_ratio,
        "bridge_ratio": metrics.bridge_ratio,
        "articulation_ratio": metrics.articulation_ratio,
        "leaf_ratio": metrics.leaf_ratio,

        "chain_count": metrics.chain_count,
        "triangle_count": metrics.triangle_count,
        "star_count": metrics.star_count,
        "bottleneck_count": metrics.bottleneck_count,
        "cycle_count": metrics.cycle_count,

        "hierarchy_score": metrics.hierarchy_score,
        "branching_score": metrics.branching_score,
        "cyclicity_score": metrics.cyclicity_score,
        "bottleneck_score": metrics.bottleneck_score,
        "persistence_score": metrics.persistence_score,

        "truth_ratio": metrics.truth_ratio,

        "mean_node_coherence": metrics.mean_node_coherence,
        "mean_edge_coherence": metrics.mean_edge_coherence,

        "reduction_ratio": metrics.reduction_ratio,
    }


# ------------------------------------------------------------
# Distribution Calculations
# ------------------------------------------------------------

def compute_distributions(
    metrics: list[ProfileMetrics],
) -> dict[str, MetricDistribution]:
    """Compute every numeric distribution in the population."""

    buckets: dict[str, list[float]] = defaultdict(list)

    for profile in metrics:
        values = profile_metrics_to_numeric_dict(profile)

        for metric_name, value in values.items():
            numeric = float(value)

            if math.isnan(numeric):
                continue

            buckets[metric_name].append(numeric)

    distributions: dict[str, MetricDistribution] = {}

    for metric_name, values in buckets.items():
        distributions[metric_name] = build_distribution(
            metric_name,
            values,
        )

    return distributions


def build_distribution(
    metric: str,
    values: list[float],
) -> MetricDistribution:
    """Build descriptive statistics for one metric."""

    if not values:
        return MetricDistribution(
            metric=metric,
            count=0,
            minimum=0.0,
            maximum=0.0,
            mean=0.0,
            median=0.0,
            variance=0.0,
            standard_deviation=0.0,
            first_quartile=0.0,
            third_quartile=0.0,
            percentile_95=0.0,
        )

    ordered = sorted(values)

    variance = (
        statistics.variance(ordered)
        if len(ordered) > 1
        else 0.0
    )

    standard_deviation = (
        statistics.stdev(ordered)
        if len(ordered) > 1
        else 0.0
    )

    return MetricDistribution(
        metric=metric,
        count=len(ordered),
        minimum=min(ordered),
        maximum=max(ordered),
        mean=statistics.mean(ordered),
        median=statistics.median(ordered),
        variance=variance,
        standard_deviation=standard_deviation,
        first_quartile=percentile(ordered, 25.0),
        third_quartile=percentile(ordered, 75.0),
        percentile_95=percentile(ordered, 95.0),
    )


def percentile(
    values: list[float],
    percent: float,
) -> float:
    """Compute a percentile using linear interpolation."""

    if not values:
        return 0.0

    if len(values) == 1:
        return values[0]

    index = (len(values) - 1) * (percent / 100.0)

    lower = math.floor(index)
    upper = math.ceil(index)

    if lower == upper:
        return values[lower]

    weight = index - lower

    return (
        values[lower] * (1.0 - weight)
        + values[upper] * weight
    )

# ------------------------------------------------------------
# Graph Helpers
# ------------------------------------------------------------

def safe_ratio(
    numerator: float,
    denominator: float,
) -> float:
    """Safely compute a ratio."""

    if denominator <= 0:
        return 0.0

    return min(
        1.0,
        max(
            0.0,
            float(numerator) / float(denominator),
        ),
    )


def graph_density(
    *,
    node_count: int,
    edge_count: int,
) -> float:
    """Compute graph density."""

    if node_count < 2:
        return 0.0

    maximum_edges = node_count * (node_count - 1) / 2

    if maximum_edges <= 0:
        return 0.0

    return edge_count / maximum_edges


def graph_average_degree(
    *,
    node_count: int,
    edge_count: int,
) -> float:
    """Compute average node degree."""

    if node_count <= 0:
        return 0.0

    return (2.0 * edge_count) / node_count


def mean_truth_score(
    nodes: dict[str, Any],
) -> float:
    """Average truth score across STG nodes."""

    if not nodes:
        return 0.0

    scores = [
        node.get(
            "truth_score",
            node.get("weight", 0.0),
        )
        for node in nodes.values()
    ]

    return statistics.mean(scores)


def mean_coherence_score(
    records: dict[str, Any],
) -> float:
    """Average coherence score."""

    if not records:
        return 0.0

    scores = [
        record.get(
            "coherence",
            {},
        ).get(
            "score",
            0.0,
        )
        for record in records.values()
    ]

    return statistics.mean(scores)


def compute_reduction_ratio(
    cig: dict[str, Any],
    stg: dict[str, Any],
) -> float:
    """Compute graph reduction ratio."""

    analyzed = cig.get(
        "analyzed_graph",
        {},
    )

    original_nodes = len(
        analyzed.get(
            "nodes",
            {},
        )
    )

    reduced_nodes = len(
        stg.get(
            "nodes",
            {},
        )
    )

    if original_nodes == 0:
        return 0.0

    return reduced_nodes / original_nodes

# ------------------------------------------------------------
# Serialization
# ------------------------------------------------------------


def population_statistics_to_dict(
    population: PopulationStatistics,
) -> dict[str, Any]:
    """Serialize a PopulationStatistics object."""

    return {
        "version": population.version,
        "profile_count": population.profile_count,
        "metrics": {
            name: {
                "metric": distribution.metric,
                "count": distribution.count,
                "minimum": distribution.minimum,
                "maximum": distribution.maximum,
                "mean": distribution.mean,
                "median": distribution.median,
                "variance": distribution.variance,
                "standard_deviation": distribution.standard_deviation,
                "first_quartile": distribution.first_quartile,
                "third_quartile": distribution.third_quartile,
                "percentile_95": distribution.percentile_95,
            }
            for name, distribution in population.metrics.items()
        },
    }