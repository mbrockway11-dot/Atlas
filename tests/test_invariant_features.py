from atlas.invariant.features import (
    extract_invariant_features,
    invariant_features_to_dict,
)


def test_extract_invariant_features_basic():
    path = [(0, 0), (1, 1), (2, 2)]
    features = extract_invariant_features(path, 3)

    assert features.node_weights
    assert features.node_ranking
    assert features.edge_weights
    assert features.entropy >= 0.0
    assert features.entropy <= 1.0
    assert features.axis_strength >= 0.0
    assert features.axis_strength <= 1.0


def test_extract_invariant_features_self_loop():
    path = [(0, 0), (0, 0), (1, 1)]
    features = extract_invariant_features(path, 3)

    assert features.self_loops > 0


def test_invariant_features_to_dict():
    path = [(0, 0), (1, 1), (2, 2)]
    features = extract_invariant_features(path, 3)
    data = invariant_features_to_dict(features)

    assert "node_weights" in data
    assert "node_ranking" in data
    assert "edge_weights" in data
    assert "self_loops" in data
    assert "degrees" in data
    assert "density" in data
    assert "clusters" in data
    assert "entropy" in data
    assert "axis_strength" in data