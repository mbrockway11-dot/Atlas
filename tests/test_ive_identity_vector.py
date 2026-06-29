from atlas.acf.builder import build_acf_profile
from atlas.ive import (
    IDENTITY_GLOBAL_FEATURES,
    PLANET_ORDER,
    build_identity_vector,
    identity_vector_to_dict,
    validate_identity_vector,
)


def test_build_identity_vector():
    acf = build_acf_profile("Michael Elvis Brockway")

    identity_vector = build_identity_vector(acf)

    assert identity_vector.name == "Michael Elvis Brockway"
    assert len(identity_vector.planets) == 7
    assert list(identity_vector.planets.keys()) == PLANET_ORDER

    assert set(identity_vector.global_features) == set(IDENTITY_GLOBAL_FEATURES)

    for value in identity_vector.global_features.values():
        assert 0.0 <= value <= 1.0

    assert validate_identity_vector(identity_vector) is True


def test_identity_vector_to_dict():
    acf = build_acf_profile("Michael Elvis Brockway")

    identity_vector = build_identity_vector(acf)
    data = identity_vector_to_dict(identity_vector)

    assert data["name"] == "Michael Elvis Brockway"
    assert "planets" in data
    assert "global_features" in data
    assert "quality" in data
    assert "diagnostics" in data
    assert len(data["planets"]) == 7


def test_identity_vector_with_calibration_acfs():
    acf = build_acf_profile("Michael Elvis Brockway")

    calibration_acfs = [
        build_acf_profile("Michael Elvis Brockway"),
        build_acf_profile("Nikola Tesla"),
        build_acf_profile("Isaac Newton"),
    ]

    identity_vector = build_identity_vector(
        acf=acf,
        calibration_acfs=calibration_acfs,
        normalization_mode="percentile",
    )

    assert validate_identity_vector(identity_vector) is True
    assert identity_vector.quality["mean_calibration_size"] >= 1


def test_identity_vector_diagnostics_have_expected_keys():
    acf = build_acf_profile("Michael Elvis Brockway")

    identity_vector = build_identity_vector(acf)

    expected = [
        "dominant_coherence_planet",
        "weakest_coherence_planet",
        "dominant_stability_planet",
        "weakest_stability_planet",
        "dominant_entropy_planet",
        "weakest_entropy_planet",
        "identity_balance_index",
        "identity_complexity_index",
        "identity_stability_index",
    ]

    for key in expected:
        assert key in identity_vector.diagnostics