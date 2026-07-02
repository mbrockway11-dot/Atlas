"""Tests for population index."""

from __future__ import annotations

from atlas.core.compiler import compile_profile
from atlas.fingerprint import build_structural_fingerprint
from atlas.graph import (
    build_graph_activation,
    build_temporal_graph,
    compute_graph_metrics,
    propagate_activation,
)
from atlas.population import build_population_index


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


def test_build_population_index_from_structural_fingerprints():
    fingerprint = _fingerprint("nikola_tesla")

    index = build_population_index([fingerprint])
    payload = index.to_dict()

    assert index.count == 1
    assert index.profile_keys() == ("nikola_tesla",)
    assert payload["version"] == "0.1"
    assert payload["count"] == 1
    assert payload["records"][0]["profile_key"] == "nikola_tesla"


def test_population_index_find_profile():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    record = index.find_profile("nikola_tesla")

    assert record is not None
    assert record.profile_key == "nikola_tesla"
    assert len(record.structural_hash) == 64
    assert index.find_profile("missing_profile") is None
