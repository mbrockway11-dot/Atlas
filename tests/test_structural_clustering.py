from pathlib import Path

from atlas.calibration.population_graph import PopulationGraph
from atlas.calibration.structural_clustering import (
    STRUCTURAL_CLUSTERING_VERSION,
    build_adjacency,
    build_structural_clusters,
    connected_components,
    export_structural_clusters_json,
    structural_clustering_result_to_dict,
)


def _graph() -> PopulationGraph:
    nodes = {
        "A": {"id": "A", "label": "A"},
        "B": {"id": "B", "label": "B"},
        "C": {"id": "C", "label": "C"},
        "D": {"id": "D", "label": "D"},
    }

    edges = {
        "A::B": {
            "id": "A::B",
            "source": "A",
            "target": "B",
            "similarity": 0.95,
            "distance": 0.05,
            "weight": 0.95,
            "metric_count": 20,
        },
        "B::C": {
            "id": "B::C",
            "source": "B",
            "target": "C",
            "similarity": 0.9,
            "distance": 0.1,
            "weight": 0.9,
            "metric_count": 20,
        },
    }

    return PopulationGraph(
        version="1.0",
        node_count=len(nodes),
        edge_count=len(edges),
        threshold=0.85,
        nodes=nodes,
        edges=edges,
        summary={},
    )


def test_build_adjacency():
    adjacency = build_adjacency(_graph())

    assert adjacency["A"] == {"B"}
    assert adjacency["B"] == {"A", "C"}
    assert adjacency["C"] == {"B"}
    assert adjacency["D"] == set()


def test_connected_components():
    adjacency = build_adjacency(_graph())
    components = connected_components(adjacency)

    assert ["A", "B", "C"] in components
    assert ["D"] in components


def test_build_structural_clusters():
    result = build_structural_clusters(_graph())

    assert result.version == STRUCTURAL_CLUSTERING_VERSION
    assert result.cluster_count == 2
    assert result.clustered_identity_count == 4
    assert result.singleton_count == 1

    largest = result.clusters[0]

    assert largest.member_count == 3
    assert largest.members == ["A", "B", "C"]
    assert largest.internal_edge_count == 2
    assert largest.strongest_pair["identity_a"] == "A"
    assert largest.strongest_pair["identity_b"] == "B"


def test_structural_clustering_result_to_dict():
    result = build_structural_clusters(_graph())
    data = structural_clustering_result_to_dict(result)

    assert data["version"] == STRUCTURAL_CLUSTERING_VERSION
    assert data["cluster_count"] == 2
    assert "clusters" in data
    assert "summary" in data


def test_export_structural_clusters_json(tmp_path: Path):
    result = build_structural_clusters(_graph())
    output_path = tmp_path / "structural_clusters.json"

    export_structural_clusters_json(
        result,
        output_path,
    )

    assert output_path.exists()
    assert "clusters" in output_path.read_text(encoding="utf-8")