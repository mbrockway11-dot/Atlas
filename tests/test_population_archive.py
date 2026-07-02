"""Tests for population archive persistence."""

from __future__ import annotations

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
    load_population_index,
    population_index_from_json,
    population_index_to_json,
    save_population_index,
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


def test_population_index_json_round_trip():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    text = population_index_to_json(index)
    loaded = population_index_from_json(text)

    assert loaded.count == 1
    assert loaded.profile_keys() == ("nikola_tesla",)
    assert loaded.metadata["loaded_from_archive"] is True
    assert loaded.find_profile("nikola_tesla") is not None


def test_population_index_file_round_trip(tmp_path):
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    path = tmp_path / "population_index.json"

    save_population_index(
        index=index,
        path=path,
    )

    loaded = load_population_index(path)

    assert loaded.count == 1
    assert loaded.profile_keys() == ("nikola_tesla",)
    assert loaded.metadata["loaded_from_archive"] is True
    assert path.exists()


def test_loaded_population_index_can_be_searched():
    fingerprint = _fingerprint("nikola_tesla")
    index = build_population_index([fingerprint])

    text = population_index_to_json(index)
    loaded = population_index_from_json(text)

    result = search_population(
        index=loaded,
        fingerprint=fingerprint,
        minimum_similarity=0.9,
    )

    assert result.count == 1
    assert result.matches[0].profile_key == "nikola_tesla"
    assert result.matches[0].similarity == 1.0
