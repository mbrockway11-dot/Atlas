"""Tests for population similarity search."""

from __future__ import annotations

import pytest

from atlas.core.compiler import compile_profile
from atlas.fingerprint import build_structural_fingerprint
from atlas.graph import (
    build_graph_activation,
    build_temporal_graph,
    compute_graph_metrics,
    propagate_activation,
)
from atlas.population import (
    build_population_index,
    find_similar_profiles,
    similarity_from_distance,
    vector_distance,
)


def _fingerprint(profile_key: str):
    css = compile_profile(profile_key).to_dict()
    graph = build_temporal_graph(profile_key=profile_key, css=css)
    metrics = compute_graph_metrics(graph)
    activation = build_graph_activation(graph)
    propagation = propagate_activation(graph=graph, activation=activation)

    return build_structural_fingerprint(
        profile_key=profile_key,
        metrics=metrics,
        activation=activation,
        propagation=propagation,
    )


def test_vector_distance_identical_vectors_is_zero():
    distance, shared = vector_distance(
        {"a": 1.0, "b": 2.0},
        {"a": 1.0, "b": 2.0},
    )

    assert distance == 0.0
    assert shared == {"a": 1.0, "b": 1.0}
    assert similarity_from_distance(distance) == 1.0


def test_vector_distance_handles_missing_shared_features():
    distance, shared = vector_distance(
        {"a": 1.0},
        {"b": 2.0},
    )

    assert distance == 1.0
    assert shared == {}


def test_find_similar_profiles_returns_ranked_results():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    results = find_similar_profiles(
        index=index,
        fingerprint=fingerprint,
        limit=10,
    )

    assert len(results) == 1
    assert results[0].profile_key == "nikola_tesla"
    assert results[0].similarity == 1.0
    assert results[0].distance == 0.0
    assert len(results[0].structural_hash) == 64


def test_find_similar_profiles_respects_limit():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint, fingerprint])

    results = find_similar_profiles(
        index=index,
        fingerprint=fingerprint,
        limit=1,
    )

    assert len(results) == 1


def test_find_similar_profiles_rejects_invalid_limit():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    with pytest.raises(ValueError, match="limit"):
        find_similar_profiles(
            index=index,
            fingerprint=fingerprint,
            limit=0,
        )
