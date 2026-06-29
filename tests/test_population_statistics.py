import json
import math
from pathlib import Path

from atlas.calibration.models import ProfileMetrics
from atlas.calibration.population_statistics import (
    POPULATION_STATISTICS_VERSION,
    build_distribution,
    build_population_statistics,
    compute_distributions,
    extract_profile_metrics,
    graph_average_degree,
    graph_density,
    load_population_metrics,
    percentile,
    population_statistics_to_dict,
    profile_metrics_to_numeric_dict,
    safe_ratio,
)


def _stack(
    name: str = "Test Profile",
    node_count: int = 4,
    edge_count: int = 3,
) -> dict:
    nodes = {
        str(index): {
            "id": str(index),
            "weight": index,
            "coherence": {
                "score": index / 10,
            },
        }
        for index in range(1, node_count + 1)
    }

    edges = {
        f"{index}->{index + 1}": {
            "source": str(index),
            "target": str(index + 1),
            "weight": index,
            "coherence": {
                "score": index / 10,
            },
        }
        for index in range(1, edge_count + 1)
    }

    return {
        "name": name,
        "cig": {
            "analyzed_graph": {
                "nodes": nodes,
                "edges": edges,
                "analysis": {
                    "hub_count": 1,
                    "bridge_count": 1,
                    "articulation_point_count": 1,
                    "leaf_count": 1,
                },
            },
        },
        "stg": {
            "nodes": {
                "1": {
                    "truth_score": 0.75,
                    "weight": 3,
                },
                "2": {
                    "truth_score": 0.25,
                    "weight": 2,
                },
            },
            "edges": {
                "1->2": {
                    "truth_score": 0.5,
                    "weight": 1,
                },
            },
        },
        "motifs": {
            "chain_count": 2,
            "triangle_count": 1,
            "star_count": 1,
            "bottleneck_count": 1,
            "cycle_like_count": 0,
        },
        "genome": {
            "hierarchy_score": 0.2,
            "branching_score": 0.3,
            "cyclicity_score": 0.4,
            "bottleneck_score": 0.5,
            "persistence_score": 0.6,
        },
        "topology": {
            "topology_class": "branching_tree",
        },
        "resonance": {
            "resonance_class": "low_resonance",
        },
    }


def test_safe_ratio_handles_zero_denominator():
    assert safe_ratio(1, 0) == 0.0


def test_safe_ratio_clamps_to_one():
    assert safe_ratio(10, 2) == 1.0


def test_safe_ratio_returns_fraction():
    assert safe_ratio(1, 4) == 0.25


def test_graph_density_handles_small_graph():
    assert graph_density(node_count=1, edge_count=0) == 0.0


def test_graph_density_computes_density():
    assert graph_density(node_count=4, edge_count=3) == 0.5


def test_graph_average_degree_handles_empty_graph():
    assert graph_average_degree(node_count=0, edge_count=3) == 0.0


def test_graph_average_degree_computes_average_degree():
    assert graph_average_degree(node_count=4, edge_count=3) == 1.5


def test_percentile_empty_values():
    assert percentile([], 95.0) == 0.0


def test_percentile_single_value():
    assert percentile([7.0], 95.0) == 7.0


def test_percentile_interpolates():
    assert percentile([1.0, 2.0, 3.0, 4.0], 50.0) == 2.5


def test_build_distribution_empty_values():
    distribution = build_distribution("density", [])

    assert distribution.metric == "density"
    assert distribution.count == 0
    assert distribution.mean == 0.0
    assert distribution.standard_deviation == 0.0


def test_build_distribution_multiple_values():
    distribution = build_distribution(
        "node_count",
        [1.0, 2.0, 3.0],
    )

    assert distribution.metric == "node_count"
    assert distribution.count == 3
    assert distribution.minimum == 1.0
    assert distribution.maximum == 3.0
    assert distribution.mean == 2.0
    assert distribution.median == 2.0
    assert distribution.variance == 1.0
    assert distribution.standard_deviation == 1.0
    assert distribution.first_quartile == 1.5
    assert distribution.third_quartile == 2.5


def test_extract_profile_metrics():
    metrics = extract_profile_metrics(_stack())

    assert metrics.identity == "Test Profile"
    assert metrics.node_count == 4
    assert metrics.edge_count == 3
    assert metrics.density == 0.5
    assert metrics.average_degree == 1.5
    assert metrics.hub_ratio == 0.25
    assert metrics.bridge_ratio == 1 / 3
    assert metrics.articulation_ratio == 0.25
    assert metrics.leaf_ratio == 0.25
    assert metrics.chain_count == 2
    assert metrics.triangle_count == 1
    assert metrics.star_count == 1
    assert metrics.bottleneck_count == 1
    assert metrics.cycle_count == 0
    assert metrics.hierarchy_score == 0.2
    assert metrics.branching_score == 0.3
    assert metrics.cyclicity_score == 0.4
    assert metrics.bottleneck_score == 0.5
    assert metrics.persistence_score == 0.6
    assert metrics.truth_ratio == 0.5
    assert metrics.topology_class == "branching_tree"
    assert metrics.resonance_class == "low_resonance"


def test_profile_metrics_to_numeric_dict_excludes_classes():
    metrics = extract_profile_metrics(_stack())
    numeric = profile_metrics_to_numeric_dict(metrics)

    assert "topology_class" not in numeric
    assert "resonance_class" not in numeric
    assert numeric["node_count"] == 4
    assert numeric["edge_count"] == 3
    assert numeric["density"] == 0.5


def test_compute_distributions():
    metrics = [
        extract_profile_metrics(_stack("A", node_count=4, edge_count=3)),
        extract_profile_metrics(_stack("B", node_count=5, edge_count=4)),
    ]

    distributions = compute_distributions(metrics)

    assert "node_count" in distributions
    assert distributions["node_count"].count == 2
    assert distributions["node_count"].minimum == 4
    assert distributions["node_count"].maximum == 5
    assert distributions["edge_count"].minimum == 3
    assert distributions["edge_count"].maximum == 4


def test_compute_distributions_skips_nan():
    metrics = [
        ProfileMetrics(
            identity="NaN Test",
            node_count=1,
            edge_count=1,
            density=math.nan,
            average_degree=1.0,
            hub_ratio=0.0,
            bridge_ratio=0.0,
            articulation_ratio=0.0,
            leaf_ratio=0.0,
            chain_count=0,
            triangle_count=0,
            star_count=0,
            bottleneck_count=0,
            cycle_count=0,
            hierarchy_score=0.0,
            branching_score=0.0,
            cyclicity_score=0.0,
            bottleneck_score=0.0,
            persistence_score=0.0,
            truth_ratio=0.0,
            mean_node_coherence=0.0,
            mean_edge_coherence=0.0,
            reduction_ratio=0.0,
            topology_class="unknown",
            resonance_class="unknown",
        )
    ]

    distributions = compute_distributions(metrics)

    assert "density" not in distributions
    assert "average_degree" in distributions


def test_load_population_metrics_current_file(tmp_path: Path):
    profile_dir = tmp_path / "profile_a"
    profile_dir.mkdir()

    stack_file = profile_dir / "identity_stack.json"
    stack_file.write_text(
        json.dumps(_stack("Current Format")),
        encoding="utf-8",
    )

    metrics = load_population_metrics(tmp_path)

    assert len(metrics) == 1
    assert metrics[0].identity == "Current Format"


def test_load_population_metrics_legacy_file(tmp_path: Path):
    profile_dir = tmp_path / "profile_a"
    profile_dir.mkdir()

    stack_file = profile_dir / "profile.acf.json"
    stack_file.write_text(
        json.dumps(_stack("Legacy Format")),
        encoding="utf-8",
    )

    metrics = load_population_metrics(tmp_path)

    assert len(metrics) == 1
    assert metrics[0].identity == "Legacy Format"


def test_load_population_metrics_skips_bad_json(tmp_path: Path):
    profile_dir = tmp_path / "broken_profile"
    profile_dir.mkdir()

    stack_file = profile_dir / "identity_stack.json"
    stack_file.write_text(
        "{bad json",
        encoding="utf-8",
    )

    metrics = load_population_metrics(tmp_path)

    assert metrics == []


def test_build_population_statistics_empty_library(tmp_path: Path):
    population = build_population_statistics(tmp_path)

    assert population.version == POPULATION_STATISTICS_VERSION
    assert population.profile_count == 0
    assert population.metrics == {}


def test_build_population_statistics_multiple_profiles(tmp_path: Path):
    for name in ["Alpha", "Beta"]:
        profile_dir = tmp_path / name.lower()
        profile_dir.mkdir()

        stack_file = profile_dir / "identity_stack.json"
        stack_file.write_text(
            json.dumps(_stack(name)),
            encoding="utf-8",
        )

    population = build_population_statistics(tmp_path)

    assert population.version == POPULATION_STATISTICS_VERSION
    assert population.profile_count == 2
    assert "node_count" in population.metrics
    assert population.metrics["node_count"].count == 2


def test_population_statistics_to_dict(tmp_path: Path):
    profile_dir = tmp_path / "profile_a"
    profile_dir.mkdir()

    stack_file = profile_dir / "identity_stack.json"
    stack_file.write_text(
        json.dumps(_stack("Serializable")),
        encoding="utf-8",
    )

    population = build_population_statistics(tmp_path)
    data = population_statistics_to_dict(population)

    assert data["version"] == POPULATION_STATISTICS_VERSION
    assert data["profile_count"] == 1
    assert "metrics" in data
    assert "node_count" in data["metrics"]
    assert data["metrics"]["node_count"]["metric"] == "node_count"