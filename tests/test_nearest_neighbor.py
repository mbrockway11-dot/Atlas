from atlas.calibration.models import ProfileMetrics
from atlas.calibration.nearest_neighbor import (
    NEAREST_NEIGHBOR_VERSION,
    collect_identities,
    find_all_nearest_neighbors,
    find_nearest_neighbors,
    neighbor_result_to_dict,
)
from atlas.calibration.similarity_matrix import build_similarity_matrix


def _metrics(
    identity: str,
    node_count: int,
    edge_count: int,
    density: float,
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


def _matrix():
    return build_similarity_matrix(
        [
            _metrics("A", 10, 20, 0.5),
            _metrics("B", 11, 21, 0.55),
            _metrics("C", 30, 60, 1.0),
        ]
    )


def test_collect_identities():
    matrix = _matrix()

    assert collect_identities(matrix) == ["A", "B", "C"]


def test_find_nearest_neighbors():
    matrix = _matrix()

    result = find_nearest_neighbors(
        matrix,
        "A",
        limit=2,
    )

    assert result.version == NEAREST_NEIGHBOR_VERSION
    assert result.query_identity == "A"
    assert result.neighbor_count == 2
    assert result.neighbors[0]["similarity"] >= result.neighbors[1]["similarity"]


def test_find_nearest_neighbors_limit():
    matrix = _matrix()

    result = find_nearest_neighbors(
        matrix,
        "A",
        limit=1,
    )

    assert result.neighbor_count == 1
    assert len(result.neighbors) == 1


def test_find_nearest_neighbors_missing_identity():
    matrix = _matrix()

    result = find_nearest_neighbors(
        matrix,
        "Missing",
        limit=10,
    )

    assert result.neighbor_count == 0
    assert result.summary["top_neighbor"] is None


def test_find_all_nearest_neighbors():
    matrix = _matrix()

    results = find_all_nearest_neighbors(
        matrix,
        limit=2,
    )

    assert sorted(results.keys()) == ["A", "B", "C"]
    assert results["A"].neighbor_count == 2


def test_neighbor_result_to_dict():
    matrix = _matrix()

    result = find_nearest_neighbors(
        matrix,
        "A",
        limit=2,
    )

    data = neighbor_result_to_dict(result)

    assert data["version"] == NEAREST_NEIGHBOR_VERSION
    assert data["query_identity"] == "A"
    assert "neighbors" in data
    assert "summary" in data