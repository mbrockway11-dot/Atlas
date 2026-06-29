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