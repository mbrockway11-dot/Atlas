from atlas.comparison.planet_matrix import (
    PLANETS,
    compare_planet_agreement,
)


def _fingerprint(value: float):
    return {
        planet: {
            "density": value,
            "entropy": value,
            "hub_ratio": value,
        }
        for planet in PLANETS
    }


def test_identical_fingerprints_have_high_similarity():
    fp = _fingerprint(0.5)

    result = compare_planet_agreement(fp, fp)

    assert result.overall_similarity == 1.0
    assert result.dominant_match in PLANETS
    assert result.dominant_divergence in PLANETS
    assert len(result.rows) == 7


def test_planet_matrix_returns_all_planets():
    a = _fingerprint(0.2)
    b = _fingerprint(0.8)

    result = compare_planet_agreement(a, b)

    assert set(result.planet_similarity) == set(PLANETS)
    assert set(result.planet_confidence) == set(PLANETS)


def test_missing_planet_features_do_not_crash():
    a = {"saturn": {"density": 0.4}}
    b = {"saturn": {"density": 0.4}}

    result = compare_planet_agreement(a, b)

    assert len(result.rows) == 7
    assert result.planet_similarity["saturn"] == 1.0
    assert result.planet_similarity["jupiter"] == 0.0


def test_confidence_is_averaged_per_planet():
    a = _fingerprint(0.5)
    b = _fingerprint(0.5)

    result = compare_planet_agreement(
        a,
        b,
        confidence_a={"saturn": 1.0},
        confidence_b={"saturn": 0.5},
    )

    assert result.planet_confidence["saturn"] == 0.75


def test_rows_include_feature_explanations():
    a = {
        "saturn": {
            "density": 0.1,
            "entropy": 0.5,
            "hub_ratio": 0.9,
        }
    }

    b = {
        "saturn": {
            "density": 0.1,
            "entropy": 0.7,
            "hub_ratio": 0.2,
        }
    }

    result = compare_planet_agreement(a, b, top_n_features=2)
    saturn = result.rows[0]

    assert saturn.planet == "saturn"
    assert saturn.strongest_matches[0] == "density"
    assert "hub_ratio" in saturn.strongest_differences
    assert saturn.feature_distances["density"] == 0.0
    assert saturn.feature_distances["hub_ratio"] == 0.7