"""Tests for structural graph fingerprints."""

from __future__ import annotations

from atlas.core.compiler import compile_profile
from atlas.fingerprint import build_structural_fingerprint
from atlas.graph import (
    build_graph_activation,
    build_temporal_graph,
    compute_graph_metrics,
    compute_graph_resonance,
    propagate_activation,
)


def test_build_structural_fingerprint_from_graph_intelligence():
    css = compile_profile("nikola_tesla").to_dict()
    graph = build_temporal_graph(
        profile_key="nikola_tesla",
        css=css,
    )

    metrics = compute_graph_metrics(graph)
    activation = build_graph_activation(graph)
    propagation = propagate_activation(
        graph=graph,
        activation=activation,
    )

    fingerprint = build_structural_fingerprint(
        profile_key="nikola_tesla",
        metrics=metrics,
        activation=activation,
        propagation=propagation,
    )

    payload = fingerprint.to_dict()

    assert payload["version"] == "0.1"
    assert payload["profile_key"] == "nikola_tesla"
    assert payload["metadata"]["fingerprint_type"] == "structural_graph"
    assert payload["vector"]["node_count"] > 0
    assert payload["vector"]["edge_count"] > 0
    assert len(payload["structural_hash"]) == 64
    assert payload["labels"]["propagation_top_node"] is not None


def test_structural_fingerprint_hash_is_deterministic():
    css = compile_profile("nikola_tesla").to_dict()
    graph = build_temporal_graph(
        profile_key="nikola_tesla",
        css=css,
    )

    metrics = compute_graph_metrics(graph)
    activation = build_graph_activation(graph)
    propagation = propagate_activation(
        graph=graph,
        activation=activation,
    )

    first = build_structural_fingerprint(
        profile_key="nikola_tesla",
        metrics=metrics,
        activation=activation,
        propagation=propagation,
    )
    second = build_structural_fingerprint(
        profile_key="nikola_tesla",
        metrics=metrics,
        activation=activation,
        propagation=propagation,
    )

    assert first.structural_hash == second.structural_hash


def test_structural_fingerprint_accepts_resonance():
    css = compile_profile("nikola_tesla").to_dict()
    graph = build_temporal_graph(
        profile_key="nikola_tesla",
        css=css,
    )

    metrics = compute_graph_metrics(graph)
    activation = build_graph_activation(graph)
    propagation = propagate_activation(
        graph=graph,
        activation=activation,
    )
    resonance = compute_graph_resonance(
        propagation,
        propagation,
    )

    fingerprint = build_structural_fingerprint(
        profile_key="nikola_tesla",
        metrics=metrics,
        activation=activation,
        propagation=propagation,
        resonance=resonance,
    )

    assert fingerprint.metadata["has_resonance"] is True
    assert fingerprint.vector["resonance_overall_score"] == 1.0
