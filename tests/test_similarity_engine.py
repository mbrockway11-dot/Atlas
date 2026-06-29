from atlas.calibration.models import ProfileMetrics
from atlas.calibration.similarity_engine import (
    SIMILARITY_ENGINE_VERSION,
    compare_profile_metrics,
    metric_similarity,
    similarity_result_to_dict,
)


def _metrics(
    identity: str,
    node_count: int = 10,
    edge_count: int = 20,
    density: float = 0.5,
) -> ProfileMetrics:
    return ProfileMetrics(
        identity=identity,
        node_count=node_count,
        edge_count=edge_count,
        density=density,
        average_degree=4.0,
        hub_ratio=0.2,
        bridge_ratio=0.1,
        articulation_ratio=0.1,
        leaf_ratio=0.2,
        chain_count=3,
        triangle_count=2,
        star_count=1,
        bottleneck_count=1,
        cycle_count=0,
        hierarchy_score=0.3,
        branching_score=0.4,
        cyclicity_score=0.5,
        bottleneck_score=0.6,
        persistence_score=0.7,
        truth_ratio=0.8,
        mean_node_coherence=0.5,
        mean_edge_coherence=0.4,
        reduction_ratio=0.75,
        topology_class="branching_tree",
        resonance_class="low_resonance",
    )


def test_metric_similarity_identical_values():
    assert metric_similarity(10.0, 10.0) == 1.0


def test_metric_similarity_different_values():
    assert metric_similarity(10.0, 5.0) == 0.5


def test_metric_similarity_zero_safe():
    assert metric_similarity(0.0, 0.0) == 1.0


def test_compare_profile_metrics_identical_profiles():
    result = compare_profile_metrics(
        _metrics("A"),
        _metrics("B"),
    )

    assert result.version == SIMILARITY_ENGINE_VERSION
    assert result.identity_a == "A"
    assert result.identity_b == "B"
    assert result.similarity == 1.0
    assert result.distance == 0.0
    assert result.metric_count > 0


def test_compare_profile_metrics_different_profiles():
    result = compare_profile_metrics(
        _metrics("A", node_count=10, edge_count=20, density=0.5),
        _metrics("B", node_count=20, edge_count=40, density=1.0),
    )

    assert result.similarity < 1.0
    assert result.distance > 0.0
    assert "node_count" in result.component_scores


def test_similarity_result_to_dict():
    result = compare_profile_metrics(
        _metrics("A"),
        _metrics("B"),
    )

    data = similarity_result_to_dict(result)

    assert data["version"] == SIMILARITY_ENGINE_VERSION
    assert data["identity_a"] == "A"
    assert data["identity_b"] == "B"
    assert "component_scores" in data