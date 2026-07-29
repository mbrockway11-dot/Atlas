"""Locks the canonical normalization default at every public entry point.

The default is ``"raw"``: each profile's own bounded measurements, with no
dependence on which other profiles are present. These tests fail loudly if
anyone changes a default, because that silently alters results for every
caller that omits the argument. Changing a default is allowed -- but it must
be a deliberate edit here, not an accident elsewhere.
"""

from __future__ import annotations

import inspect

from atlas.acf.builder import build_acf_profile
from atlas.ive import build_identity_vector, build_raw_vectors_from_acf
from atlas.ive.identity_vector import DEFAULT_NORMALIZATION_MODE
from atlas.services import compare_profiles_service, contradiction_service


CANONICAL_DEFAULT = "raw"


def test_builder_default_constant_is_raw() -> None:
    """The exported default constant is raw."""
    assert DEFAULT_NORMALIZATION_MODE == CANONICAL_DEFAULT


def test_builder_signature_defaults_to_raw() -> None:
    """build_identity_vector's declared default is raw."""
    signature = inspect.signature(build_identity_vector)
    assert (
        signature.parameters["normalization_mode"].default
        == CANONICAL_DEFAULT
    )


def test_builder_omitted_mode_equals_explicit_raw() -> None:
    """Omitting the mode is identical to asking for raw."""
    acf = build_acf_profile("Nikola Tesla")

    implicit = build_identity_vector(acf)
    explicit = build_identity_vector(acf, normalization_mode="raw")

    assert implicit.quality["normalization_mode"] == CANONICAL_DEFAULT
    assert implicit.global_features == explicit.global_features

    for planet, vector in explicit.planets.items():
        assert implicit.planets[planet].features == vector.features


def test_raw_default_differs_from_population_mode() -> None:
    """Raw is genuinely distinct from a population-normalized result.

    Guards against the default silently becoming a no-op: if raw and
    percentile produced the same numbers, locking the default would be
    meaningless.
    """
    acfs = [
        build_acf_profile(name)
        for name in ("Nikola Tesla", "Isaac Newton", "Ada Lovelace")
    ]
    calibration_vectors = [
        vector for acf in acfs for vector in build_raw_vectors_from_acf(acf)
    ]

    raw = build_identity_vector(acfs[0])
    percentile = build_identity_vector(
        acfs[0],
        normalization_mode="percentile",
        calibration_vectors=calibration_vectors,
    )

    assert raw.global_features != percentile.global_features


def test_compare_profiles_service_defaults_to_percentile() -> None:
    """Pairwise comparison defaults to percentile, NOT the raw builder default.

    Raw self-normalized vectors saturate (~0.95 for every pair) and do not
    discriminate; population-normalized percentile does. The single-profile
    builder stays raw -- only the comparison path is population-relative. This
    is a deliberate departure from CANONICAL_DEFAULT, locked here so it cannot
    silently revert.
    """
    signature = inspect.signature(
        compare_profiles_service.build_compare_profiles_payload
    )
    assert signature.parameters["normalization_mode"].default == "percentile"


def test_contradiction_service_defaults_to_raw() -> None:
    """The contradiction service default is raw."""
    signature = inspect.signature(
        contradiction_service.build_compare_profiles_payload
    )
    assert (
        signature.parameters["normalization_mode"].default
        == CANONICAL_DEFAULT
    )
