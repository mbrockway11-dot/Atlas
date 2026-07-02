"""Tests for population search."""

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
    search_population,
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


def test_search_population_returns_matches():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    result = search_population(
        index=index,
        fingerprint=fingerprint,
        minimum_similarity=0.9,
        top_k=10,
    )

    payload = result.to_dict()

    assert result.count == 1
    assert payload["version"] == "0.1"
    assert payload["query_profile_key"] == "nikola_tesla"
    assert payload["matches"][0]["profile_key"] == "nikola_tesla"
    assert payload["matches"][0]["similarity"] == 1.0


def test_search_population_can_exclude_self():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    result = search_population(
        index=index,
        fingerprint=fingerprint,
        exclude_self=True,
    )

    assert result.count == 0
    assert result.metadata["candidate_count"] == 0


def test_search_population_filters_by_fingerprint_type():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    result = search_population(
        index=index,
        fingerprint=fingerprint,
        fingerprint_type="structural_graph",
    )

    assert result.count == 1

    missing = search_population(
        index=index,
        fingerprint=fingerprint,
        fingerprint_type="missing_type",
    )

    assert missing.count == 0


def test_search_population_filters_by_metadata():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    result = search_population(
        index=index,
        fingerprint=fingerprint,
        metadata_filters={"source": "atlas.graph"},
    )

    assert result.count == 1

    missing = search_population(
        index=index,
        fingerprint=fingerprint,
        metadata_filters={"source": "missing"},
    )

    assert missing.count == 0


def test_search_population_rejects_invalid_inputs():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    with pytest.raises(ValueError, match="top_k"):
        search_population(
            index=index,
            fingerprint=fingerprint,
            top_k=0,
        )

    with pytest.raises(ValueError, match="minimum_similarity"):
        search_population(
            index=index,
            fingerprint=fingerprint,
            minimum_similarity=2.0,
        )
