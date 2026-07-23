import pytest

from atlas.acf.builder import build_acf_profile
from atlas.ive import (
    PLANET_ORDER,
    build_identity_vector,
    build_planet_relationship_matrix,
    relationship_matrix_to_dict,
    validate_relationship_matrix,
)


def test_build_planet_relationship_matrix():
    acf = build_acf_profile("Michael Elvis Brockway")
    identity_vector = build_identity_vector(acf)

    matrix = build_planet_relationship_matrix(identity_vector)

    assert matrix.name == "Michael Elvis Brockway"
    assert matrix.planets == PLANET_ORDER
    assert validate_relationship_matrix(matrix) is True

    # A planet's cosine similarity with itself is 1.0 up to floating-point
    # rounding; assert approximately, not bit-exact.
    for planet in PLANET_ORDER:
        assert matrix.similarity[planet][planet] == pytest.approx(1.0)
        assert matrix.distance[planet][planet] == pytest.approx(0.0, abs=1e-9)
        assert matrix.agreement[planet][planet] == pytest.approx(1.0)


def test_relationship_matrix_to_dict():
    acf = build_acf_profile("Michael Elvis Brockway")
    identity_vector = build_identity_vector(acf)

    matrix = build_planet_relationship_matrix(identity_vector)
    data = relationship_matrix_to_dict(matrix)

    assert data["name"] == "Michael Elvis Brockway"
    assert "similarity" in data
    assert "distance" in data
    assert "agreement" in data
    assert "diagnostics" in data