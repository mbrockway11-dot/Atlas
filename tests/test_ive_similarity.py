from atlas.acf.builder import build_acf_profile
from atlas.ive import (
    build_identity_vector,
    build_raw_vectors_from_acf,
    compare_identity_vectors,
    identity_similarity_to_dict,
    validate_identity_similarity,
)


def test_compare_identity_vectors():
    acf_a = build_acf_profile("Michael Elvis Brockway")
    acf_b = build_acf_profile("Nikola Tesla")

    calibration_vectors = [
        vector
        for acf in (acf_a, acf_b, build_acf_profile("Isaac Newton"))
        for vector in build_raw_vectors_from_acf(acf)
    ]

    vector_a = build_identity_vector(acf_a, calibration_vectors=calibration_vectors)
    vector_b = build_identity_vector(acf_b, calibration_vectors=calibration_vectors)

    similarity = compare_identity_vectors(vector_a, vector_b)

    assert similarity.name_a == "Michael Elvis Brockway"
    assert similarity.name_b == "Nikola Tesla"
    assert validate_identity_similarity(similarity) is True

    assert 0.0 <= similarity.global_similarity <= 1.0
    assert 0.0 <= similarity.relationship_similarity <= 1.0
    assert 0.0 <= similarity.composite_similarity <= 1.0
    assert similarity.planet_similarity


def test_identity_similarity_to_dict():
    acf_a = build_acf_profile("Michael Elvis Brockway")
    acf_b = build_acf_profile("Nikola Tesla")

    vector_a = build_identity_vector(acf_a)
    vector_b = build_identity_vector(acf_b)

    similarity = compare_identity_vectors(vector_a, vector_b)
    data = identity_similarity_to_dict(similarity)

    assert data["name_a"] == "Michael Elvis Brockway"
    assert data["name_b"] == "Nikola Tesla"
    assert "composite_similarity" in data
    assert "diagnostics" in data