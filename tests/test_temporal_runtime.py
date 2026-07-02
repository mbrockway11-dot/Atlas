"""Tests for Atlas temporal runtime."""

from __future__ import annotations

from atlas.core.compiler import compile_profile
from atlas.temporal_runtime import TemporalRuntimeEngine
from atlas.temporal_runtime.scoring import score_transit_activation


def test_score_transit_activation_uses_expected_components():
    score = score_transit_activation(
        {
            "same_sign_count": 6,
            "opposition_count": 3,
            "contact_count": 81,
        }
    )

    assert score["score_status"] == "computed"
    assert score["activation_score"] == 47.1
    assert score["components"]["same_sign_score"] == 30.0
    assert score["components"]["opposition_score"] == 9.0
    assert score["components"]["density_score"] == 8.1


def test_temporal_runtime_engine_evaluates_compiled_css():
    css = compile_profile("nikola_tesla").to_dict()

    result = TemporalRuntimeEngine().evaluate(
        profile_key="nikola_tesla",
        css=css,
        evaluation_date="2026-07-02",
    )

    assert result.success is True
    assert result.activation["has_temporal"] is True
    assert result.activation["has_natal"] is True
    assert result.activation["has_ephemeris"] is True
    assert result.activation["has_transits"] is True
    assert result.scoring["score_status"] == "computed"
    assert result.scoring["activation_score"] > 0
    assert result.metadata["runtime"] == "atlas.temporal_runtime"
