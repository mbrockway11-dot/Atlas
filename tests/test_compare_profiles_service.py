"""Tests for Compare Profiles service."""

from __future__ import annotations

from atlas.services.compare_profiles_service import (
    build_compare_profiles_payload,
)


def test_compare_profiles_payload_builds():
    payload = build_compare_profiles_payload(
        "nikola_tesla",
        "aaron_beck",
        normalization_mode="raw",
    )

    assert payload.success is True
    assert payload.version == "3.0"
    assert payload.profile_a["key"] == "nikola_tesla"
    assert payload.profile_b["key"] == "aaron_beck"
    assert payload.vector_a is not None
    assert payload.vector_b is not None
    assert payload.comparison is not None
    assert payload.planet_matrix is not None
    assert payload.summary["normalization_mode"] == "raw"
    assert payload.diagnostics["global_feature_delta"]


def test_compare_profiles_rejects_same_profile():
    payload = build_compare_profiles_payload(
        "nikola_tesla",
        "nikola_tesla",
    )

    assert payload.success is False
    assert payload.errors
