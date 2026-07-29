from atlas.acf.builder import build_acf_profile
from atlas.ive import (
    PLANET_ORDER,
    build_composite_planet_vector,
    build_composite_planet_vectors,
    build_planet_feature_vector,
    composite_planet_vector_to_dict,
    composite_vectors_to_feature_table,
    normalize_planet_vectors,
    validate_composite_vector,
)


def build_normalized_vectors(names):
    raw_vectors = []

    for name in names:
        acf = build_acf_profile(name)

        for layer in acf["identity_graph"]["layers"]:
            raw_vectors.append(
                build_planet_feature_vector(
                    layer=layer,
                    profile_name=acf["identity"]["name"],
                )
            )

    return normalize_planet_vectors(raw_vectors, mode="percentile")


def test_build_composite_planet_vector():
    vectors = build_normalized_vectors(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    michael_vectors = [
        vector
        for vector in vectors
        if vector.name == "Michael Elvis Brockway"
    ]

    composite = build_composite_planet_vector(
        planet="Saturn",
        vectors=michael_vectors,
    )

    assert composite.name == "Michael Elvis Brockway"
    assert composite.planet == "Saturn"
    assert composite.source_count == 3
    assert set(composite.source_ciphers) == {
        "hebrew_literal",
        "hebrew_phonetic",
        "ordinal",
    }
    assert validate_composite_vector(composite) is True


def test_build_composite_planet_vectors_all_planets():
    vectors = build_normalized_vectors(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    michael_vectors = [
        vector
        for vector in vectors
        if vector.name == "Michael Elvis Brockway"
    ]

    composites = build_composite_planet_vectors(michael_vectors)

    assert len(composites) == 7

    planets = [
        vector.planet
        for vector in composites
    ]

    assert planets == PLANET_ORDER

    for composite in composites:
        assert validate_composite_vector(composite) is True


def test_composite_planet_vector_to_dict():
    vectors = build_normalized_vectors(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    michael_vectors = [
        vector
        for vector in vectors
        if vector.name == "Michael Elvis Brockway"
    ]

    composite = build_composite_planet_vector(
        planet="Saturn",
        vectors=michael_vectors,
    )

    data = composite_planet_vector_to_dict(composite)

    assert data["name"] == "Michael Elvis Brockway"
    assert data["planet"] == "Saturn"
    assert "features" in data


def test_composite_vectors_to_feature_table():
    vectors = build_normalized_vectors(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    michael_vectors = [
        vector
        for vector in vectors
        if vector.name == "Michael Elvis Brockway"
    ]

    composites = build_composite_planet_vectors(michael_vectors)
    table = composite_vectors_to_feature_table(composites)

    assert len(table) == 7
    assert table[0]["planet"] == "Saturn"
    assert "graph_coherence" in table[0]

import pytest

from atlas.ive.schema import IVE_VERSION, VECTOR_FEATURES, NormalizedPlanetVector


def _norm_vector(name, cipher, overrides):
    """A NormalizedPlanetVector with all features 0.5 except `overrides`."""
    features = {feature: 0.5 for feature in VECTOR_FEATURES}
    features.update(overrides)
    return NormalizedPlanetVector(
        version=IVE_VERSION, name=name, cipher=cipher, planet="Saturn",
        kamea="saturn", grid_size=3, features=features,
        raw_features=dict(features), normalization_mode="raw", calibration_size=1,
    )


def test_composite_full_agreement_when_ciphers_identical():
    vectors = [
        _norm_vector("X", cipher, {})
        for cipher in ("ordinal", "hebrew_literal", "hebrew_phonetic")
    ]
    composite = build_composite_planet_vector(planet="Saturn", vectors=vectors)
    assert composite.completeness == 1.0
    assert composite.agreement_score == 1.0  # zero variance across ciphers
    assert composite.confidence_score == 1.0
    assert set(composite.feature_agreement) == set(VECTOR_FEATURES)
    assert all(value == 1.0 for value in composite.feature_agreement.values())


def test_composite_agreement_drops_on_the_feature_ciphers_disagree_about():
    vectors = [
        _norm_vector("X", "ordinal", {"density": 0.0}),
        _norm_vector("X", "hebrew_literal", {"density": 1.0}),
        _norm_vector("X", "hebrew_phonetic", {"density": 0.5}),
    ]
    composite = build_composite_planet_vector(planet="Saturn", vectors=vectors)
    assert composite.feature_agreement["density"] < 1.0  # they scattered here
    assert composite.feature_agreement["entropy"] == 1.0  # but agreed here
    assert composite.agreement_score < 1.0


def test_composite_single_cipher_penalised_by_completeness():
    composite = build_composite_planet_vector(
        planet="Saturn", vectors=[_norm_vector("X", "ordinal", {})]
    )
    assert composite.source_count == 1
    assert composite.agreement_score == 1.0  # one cipher = nothing to disagree with
    assert composite.completeness == pytest.approx(1.0 / 3.0)
    assert composite.confidence_score == pytest.approx(1.0 / 3.0)  # agreement * completeness
