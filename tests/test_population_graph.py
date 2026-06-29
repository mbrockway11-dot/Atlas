from pathlib import Path

from atlas.calibration.models import ProfileMetrics
from atlas.calibration.population_graph import (
    POPULATION_GRAPH_VERSION,
    build_edge_id,
    build_population_graph,
    compute_degrees,
    export_population_graph_json,
    graph_density,
    population_graph_to_dict,
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
    profiles = [
        _metrics("A", 10, 20, 0.5),
        _metrics("B", 11, 21, 0.55),
        _metrics("C", 40, 80, 1.0),
    ]

    return build_similarity_matrix(profiles)


def test_build_edge_id_is_stable():
    assert build_edge_id("B", "A") == "A::B"
    assert build_edge_id("A", "B") == "A::B"


def test_graph_density_empty_or_singleton():
    assert graph_density(node_count=0, edge_count=0) == 0.0
    assert graph_density(node_count=1, edge_count=0) == 0.0


def test_graph_density_regular_graph():
    assert graph_density(node_count=3, edge_count=3) == 1.0


def test_build_population_graph():
    graph = build_population_graph(
        _matrix(),
        threshold=0.5,
    )

    assert graph.version == POPULATION_GRAPH_VERSION
    assert graph.node_count == 3
    assert graph.edge_count >= 1
    assert graph.threshold == 0.5
    assert "A" in graph.nodes
    assert graph.summary["node_count"] == 3


def test_build_population_graph_threshold_filters_edges():
    loose = build_population_graph(
        _matrix(),
        threshold=0.0,
    )

    strict = build_population_graph(
        _matrix(),
        threshold=0.99,
    )

    assert loose.edge_count >= strict.edge_count


def test_compute_degrees():
    graph = build_population_graph(
        _matrix(),
        threshold=0.0,
    )

    degrees = compute_degrees(
        nodes=graph.nodes,
        edges=graph.edges,
    )

    assert set(degrees.keys()) == {"A", "B", "C"}
    assert sum(degrees.values()) == graph.edge_count * 2


def test_population_graph_to_dict():
    graph = build_population_graph(
        _matrix(),
        threshold=0.5,
    )

    data = population_graph_to_dict(graph)

    assert data["version"] == POPULATION_GRAPH_VERSION
    assert data["node_count"] == 3
    assert "nodes" in data
    assert "edges" in data


def test_export_population_graph_json(tmp_path: Path):
    graph = build_population_graph(
        _matrix(),
        threshold=0.5,
    )

    output_path = tmp_path / "population_graph.json"

    export_population_graph_json(
        graph,
        output_path,
    )

    assert output_path.exists()
    assert "nodes" in output_path.read_text(encoding="utf-8")