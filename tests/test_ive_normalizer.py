from atlas.acf.builder import build_acf_profile
from atlas.ive import (
    NormalizedPlanetVector,
    build_planet_feature_vector,
    minmax_scale,
    normalize_planet_vector,
    normalize_planet_vectors,
    percentile_rank,
    validate_normalized_vector,
    zscore_to_unit,
)


def build_vectors(names):
    vectors = []

    for name in names:
        acf = build_acf_profile(name)

        for layer in acf["identity_graph"]["layers"]:
            vectors.append(
                build_planet_feature_vector(
                    layer=layer,
                    profile_name=acf["identity"]["name"],
                )
            )

    return vectors


def test_normalize_planet_vector_percentile():
    vectors = build_vectors(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    vector = vectors[0]

    normalized = normalize_planet_vector(
        vector=vector,
        calibration_vectors=vectors,
        mode="percentile",
    )

    assert isinstance(normalized, NormalizedPlanetVector)
    assert normalized.name == vector.name
    assert normalized.cipher == vector.cipher
    assert normalized.planet == vector.planet
    assert normalized.normalization_mode == "percentile"
    assert normalized.calibration_size >= 1
    assert validate_normalized_vector(normalized) is True

    for value in normalized.features.values():
        assert 0.0 <= value <= 1.0


def test_normalize_planet_vectors_all_layers():
    vectors = build_vectors(
        [
            "Michael Elvis Brockway",
            "Nikola Tesla",
            "Isaac Newton",
        ]
    )

    normalized = normalize_planet_vectors(vectors, mode="percentile")

    assert len(normalized) == len(vectors)

    for vector in normalized:
        assert validate_normalized_vector(vector) is True


def test_minmax_scale():
    assert minmax_scale(5.0, [0.0, 5.0, 10.0]) == 0.5
    assert minmax_scale(10.0, [0.0, 5.0, 10.0]) == 1.0
    assert minmax_scale(0.0, [0.0, 5.0, 10.0]) == 0.0
    assert minmax_scale(5.0, [5.0, 5.0, 5.0]) == 0.5


def test_percentile_rank():
    values = [1.0, 2.0, 3.0, 4.0]

    assert percentile_rank(1.0, values) == 0.125
    assert percentile_rank(2.0, values) == 0.375
    assert percentile_rank(3.0, values) == 0.625
    assert percentile_rank(4.0, values) == 0.875


def test_zscore_to_unit():
    value = zscore_to_unit(2.0, [1.0, 2.0, 3.0])

    assert 0.0 <= value <= 1.0

    constant = zscore_to_unit(2.0, [2.0, 2.0, 2.0])

    assert constant == 0.5