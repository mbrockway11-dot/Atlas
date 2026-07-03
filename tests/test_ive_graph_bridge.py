"""Tests for IVE graph bridge."""

from __future__ import annotations

from atlas.core.compiler import compile_profile
from atlas.fingerprint import build_structural_fingerprint
from atlas.graph import (
    build_graph_activation,
    build_temporal_graph,
    compute_graph_metrics,
    propagate_activation,
)
from atlas.ive import (
    build_graph_backed_identity_vector,
    graph_backed_identity_vector_to_dict,
)
from atlas.services.single_profile_intelligence_service import (
    build_single_profile_intelligence_payload,
)


def _graph_stack(profile_key: str):
    css = compile_profile(profile_key).to_dict()
    graph = build_temporal_graph(profile_key=profile_key, css=css)
    metrics = compute_graph_metrics(graph)
    activation = build_graph_activation(graph)
    propagation = propagate_activation(graph=graph, activation=activation)
    fingerprint = build_structural_fingerprint(
        profile_key=profile_key,
        metrics=metrics,
        activation=activation,
        propagation=propagation,
    )
    return metrics, activation, propagation, fingerprint


def test_build_graph_backed_identity_vector():
    metrics, activation, propagation, fingerprint = _graph_stack("nikola_tesla")

    vector = build_graph_backed_identity_vector(
        profile_key="nikola_tesla",
        metrics=metrics,
        activation=activation,
        propagation=propagation,
        fingerprint=fingerprint,
    )

    payload = graph_backed_identity_vector_to_dict(vector)

    assert payload["metadata"]["status"] == "integrated"
    assert payload["profile_key"] == "nikola_tesla"
    assert payload["quality"]["legacy_acf_vector"] is False
    assert payload["quality"]["feature_count"] > 0
    assert payload["global_features"]["structural_complexity_index"] >= 0
    assert payload["global_features"]["structural_stability_index"] >= 0
    assert payload["diagnostics"]["structural_hash"] == fingerprint.structural_hash


def test_single_profile_service_includes_graph_backed_ive():
    payload = build_single_profile_intelligence_payload(
        "nikola_tesla",
        evaluation_date="2026-07-02",
        forecast_days=3,
    )

    ive = payload["ive"]

    assert ive["metadata"]["status"] == "integrated"
    assert ive["quality"]["source"] == "graph_intelligence"
    assert ive["source_fingerprint"]["structural_hash"] == (
        payload["structural_fingerprint"]["structural_hash"]
    )
