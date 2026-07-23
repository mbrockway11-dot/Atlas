from __future__ import annotations

import pandas as pd

from atlas.comparison import (
    compare_planet_agreement,
    compare_profiles,
    feature_family,
    feature_is_registered,
    infer_planet_from_feature,
)


def test_feature_registry_accepts_semantic_measurements() -> None:
    assert feature_is_registered("saturn_entropy")
    assert feature_is_registered("mars_hub_ratio")
    assert feature_is_registered("kamea_mean_edge_density")
    assert feature_family("saturn_entropy") == "planetary_topology"


def test_feature_registry_rejects_coordinates() -> None:
    assert not feature_is_registered("saturn_longitude")
    assert not feature_is_registered("raw_coordinate_x")
    assert not feature_is_registered("compiler_elapsed_ms")


def test_planet_inference_supports_multiple_styles() -> None:
    assert infer_planet_from_feature("saturn_entropy") == "Saturn"
    assert infer_planet_from_feature("kamea.saturn.hub_ratio") == "Saturn"
    assert infer_planet_from_feature("planetary_mars_density") == "Mars"


def test_planet_matrix_identical_profiles() -> None:
    fingerprint = {
        planet: {
            "entropy": 0.5,
            "density": 0.25,
        }
        for planet in (
            "saturn",
            "jupiter",
            "mars",
            "sun",
            "venus",
            "mercury",
            "moon",
        )
    }

    result = compare_planet_agreement(
        fingerprint,
        fingerprint,
    )

    assert result.overall_similarity == 1.0
    assert all(
        similarity == 1.0
        for similarity in result.planet_similarity.values()
    )


def test_compare_profiles_uses_registered_features() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "name": "A",
                "saturn_entropy": 0.10,
                "mars_hub_ratio": 0.20,
                "saturn_longitude": 100.0,
            },
            {
                "name": "B",
                "saturn_entropy": 0.30,
                "mars_hub_ratio": 0.60,
                "saturn_longitude": 200.0,
            },
            {
                "name": "C",
                "saturn_entropy": 0.90,
                "mars_hub_ratio": 0.80,
                "saturn_longitude": 300.0,
            },
        ]
    )

    comparison = compare_profiles(
        dataframe,
        "A",
        "B",
        min_std=0.0,
    )

    assert comparison.feature_mode == "registered"
    assert "saturn_entropy" in comparison.selected_features
    assert "mars_hub_ratio" in comparison.selected_features
    assert "saturn_longitude" not in comparison.selected_features
    assert comparison.family_summary["ranked_families"]
    assert comparison.planet_summary["ranked_planets"]
