from atlas.acf.builder import build_acf_profile
from atlas.ive import (
    IVE_VERSION,
    VECTOR_FEATURES,
    build_planet_feature_vector,
    planet_feature_vector_to_dict,
    validate_feature_vector,
)


def test_build_planet_feature_vector():
    acf = build_acf_profile("Michael Elvis Brockway")
    layer = acf["identity_graph"]["layers"][0]

    vector = build_planet_feature_vector(
        layer=layer,
        profile_name=acf["identity"]["name"],
    )

    assert vector.version == IVE_VERSION
    assert vector.name == "Michael Elvis Brockway"
    assert vector.cipher
    assert vector.planet
    assert vector.kamea
    assert vector.grid_size > 0

    assert set(vector.features) == set(VECTOR_FEATURES)

    for value in vector.features.values():
        assert 0.0 <= value <= 1.0

    assert validate_feature_vector(vector) is True


def test_planet_feature_vector_to_dict():
    acf = build_acf_profile("Michael Elvis Brockway")
    layer = acf["identity_graph"]["layers"][0]

    vector = build_planet_feature_vector(
        layer=layer,
        profile_name=acf["identity"]["name"],
    )

    data = planet_feature_vector_to_dict(vector)

    assert data["version"] == IVE_VERSION
    assert data["name"] == "Michael Elvis Brockway"
    assert "features" in data
    assert set(data["features"]) == set(VECTOR_FEATURES)


def test_all_21_layers_build_valid_vectors():
    acf = build_acf_profile("Michael Elvis Brockway")

    vectors = [
        build_planet_feature_vector(
            layer=layer,
            profile_name=acf["identity"]["name"],
        )
        for layer in acf["identity_graph"]["layers"]
    ]

    assert len(vectors) == 21

    for vector in vectors:
        assert validate_feature_vector(vector) is True