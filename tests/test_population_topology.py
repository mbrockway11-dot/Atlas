import pandas as pd

from atlas.research.population_topology import (
    build_population_topology_graph,
    connected_components,
    cosine_similarity_matrix,
    deterministic_communities,
    topology_edges_dataframe,
    topology_nodes_dataframe,
)
from atlas.research.validation import build_profile_feature_matrix


def sample_matrix():
    rows = []
    profiles = [
        ("Alpha", 0.0),
        ("Beta", 0.1),
        ("Gamma", 5.0),
        ("Delta", 5.1),
    ]

    for name, offset in profiles:
        for cipher in ["ordinal", "hebrew_phonetic", "hebrew_literal"]:
            for planet in ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]:
                rows.append(
                    {
                        "name": name,
                        "cipher": cipher,
                        "planet": planet,
                        "kamea": planet,
                        "sequence_length": 10 + offset,
                        "unique_nodes": 5 + offset,
                        "density": 0.1 + offset,
                        "entropy": 1.0 + offset,
                    }
                )
    return pd.DataFrame(rows)


def sample_features():
    return build_profile_feature_matrix(sample_matrix())


def test_cosine_similarity_matrix_is_square():
    similarity = cosine_similarity_matrix(sample_features())

    assert similarity.shape == (4, 4)
    assert list(similarity.index) == ["Alpha", "Beta", "Delta", "Gamma"]
    assert similarity.loc["Alpha", "Alpha"] == 1.0


def test_build_population_topology_graph_keeps_top_k_edges():
    graph = build_population_topology_graph(sample_features(), threshold=0.99, top_k=1)

    assert graph["node_count"] == 4
    assert graph["edge_count"] >= 2
    assert graph["summary"]["component_count"] >= 1
    assert graph["summary"]["community_count"] >= 1


def test_nodes_and_edges_dataframe_available():
    graph = build_population_topology_graph(sample_features(), threshold=0.75, top_k=1)

    nodes = topology_nodes_dataframe(graph)
    edges = topology_edges_dataframe(graph)

    assert len(nodes) == 4
    assert {"id", "degree", "weighted_degree", "community"}.issubset(nodes.columns)
    assert {"source", "target", "similarity"}.issubset(edges.columns)


def test_connected_components_detects_isolates():
    nodes = {"A": {}, "B": {}, "C": {}}
    edges = {"A::B": {"source": "A", "target": "B", "weight": 1.0}}

    result = connected_components(nodes, edges)

    assert len(result["components"]) == 2
    assert result["node_component"]["A"] == result["node_component"]["B"]
    assert result["node_component"]["C"] != result["node_component"]["A"]


def test_deterministic_communities_assigns_all_nodes():
    nodes = {"A": {}, "B": {}, "C": {}}
    edges = {
        "A::B": {"source": "A", "target": "B", "weight": 1.0},
        "B::C": {"source": "B", "target": "C", "weight": 0.5},
    }

    result = deterministic_communities(nodes, edges)

    assert set(result["node_community"]) == {"A", "B", "C"}