"""Unit tests for the extended sigil-graph topology metrics.

These features feed the compiled identity vector, so they must be bounded to
[0, 1], deterministic, and safe on degenerate graphs.
"""

from __future__ import annotations

import pytest

from atlas.research.topology_metrics import build_layer_topology_metrics


def _layer(node_weights, edges, coordinates=None):
    return {
        "features": {
            "path_views": {
                "analysis_path": {
                    "node_weights": node_weights,
                    "edge_weights": {edge: 1 for edge in edges},
                    "coordinates": coordinates or [],
                }
            }
        }
    }


def test_triangle_is_fully_clustered_and_cyclic():
    metrics = build_layer_topology_metrics(
        _layer({"1": 1, "2": 1, "3": 1}, ["1->2", "2->3", "3->1"])
    )
    assert metrics["clustering_coefficient"] == pytest.approx(1.0)
    assert metrics["cycle_density"] == pytest.approx(1.0)  # one cycle = the max here
    assert metrics["diameter_ratio"] == pytest.approx(0.5)  # diameter 1 / (3 - 1)
    assert metrics["spectral_radius_ratio"] == pytest.approx(1.0)  # rho 2 / degree 2
    assert all(0.0 <= value <= 1.0 for value in metrics.values())


def test_path_graph_has_no_triangles_but_spans_its_diameter():
    metrics = build_layer_topology_metrics(
        _layer({"1": 1, "2": 1, "3": 1, "4": 1}, ["1->2", "2->3", "3->4"])
    )
    assert metrics["clustering_coefficient"] == 0.0  # no closed triples
    assert metrics["diameter_ratio"] == pytest.approx(1.0)  # diameter 3 / (4 - 1)
    assert metrics["cycle_density"] == 0.0  # a tree has no independent cycles
    assert metrics["betweenness_centralization"] > 0.0  # the middle carries flow


def test_degenerate_graphs_are_zero_and_do_not_crash():
    empty = build_layer_topology_metrics(_layer({}, []))
    assert all(value == 0.0 for value in empty.values())
    single = build_layer_topology_metrics(_layer({"1": 1}, []))
    assert all(value == 0.0 for value in single.values())


def test_self_loops_are_excluded_from_structure():
    metrics = build_layer_topology_metrics(
        _layer({"1": 1, "2": 1}, ["1->1", "1->2"])
    )
    # the 1->1 self-loop must not manufacture a cycle or a triangle
    assert metrics["cycle_density"] == 0.0
    assert all(0.0 <= value <= 1.0 for value in metrics.values())


def test_metrics_are_deterministic():
    layer = _layer(
        {"1": 1, "2": 1, "3": 1},
        ["1->2", "2->3", "3->1"],
        [[0, 0], [1, 1], [2, 0]],
    )
    assert build_layer_topology_metrics(layer) == build_layer_topology_metrics(layer)


def test_fractal_dimension_is_bounded_on_a_real_path():
    coordinates = [[i, (i * i) % 5] for i in range(9)]
    layer = _layer(
        {str(i): 1 for i in range(9)},
        [f"{i}->{i + 1}" for i in range(8)],
        coordinates,
    )
    metrics = build_layer_topology_metrics(layer)
    assert 0.0 <= metrics["fractal_dimension"] <= 1.0
