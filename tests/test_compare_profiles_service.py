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


def test_compare_defaults_to_percentile_and_discriminates():
    default = build_compare_profiles_payload("nikola_tesla", "aaron_beck")
    raw = build_compare_profiles_payload(
        "nikola_tesla", "aaron_beck", normalization_mode="raw"
    )
    assert default.success and raw.success
    assert default.summary["normalization_mode"] == "percentile"
    assert default.summary["calibration_profile_count"] > 0
    # Population-normalized comparison gives a different (discriminating) score
    # than the saturated raw score for the same pair.
    assert (
        default.summary["composite_similarity"]
        != raw.summary["composite_similarity"]
    )


def test_compare_falls_back_to_raw_without_calibration(monkeypatch):
    import atlas.services.compare_profiles_service as svc
    from atlas.compiled.runtime import CompiledRuntimeError

    def _no_calibration():
        raise CompiledRuntimeError("no calibration for test")

    monkeypatch.setattr(svc, "load_runtime_statistics", _no_calibration)
    payload = build_compare_profiles_payload("nikola_tesla", "aaron_beck")
    assert payload.success is True
    assert payload.summary["normalization_mode"] == "raw"  # fell back, not 0.5-collapse
    assert any("Falling back to raw" in w for w in payload.warnings)
