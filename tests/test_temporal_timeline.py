"""Tests for Atlas temporal runtime timeline."""

from __future__ import annotations

import pytest

from atlas.core.compiler import compile_profile
from atlas.temporal_runtime import build_date_range, evaluate_timeline


def test_build_date_range_is_inclusive():
    dates = build_date_range(
        start_date="2026-07-02",
        end_date="2026-07-04",
    )

    assert dates == [
        "2026-07-02",
        "2026-07-03",
        "2026-07-04",
    ]


def test_build_date_range_rejects_invalid_order():
    with pytest.raises(ValueError, match="end_date"):
        build_date_range(
            start_date="2026-07-04",
            end_date="2026-07-02",
        )


def test_evaluate_timeline_returns_serializable_payload():
    css = compile_profile("nikola_tesla").to_dict()

    timeline = evaluate_timeline(
        profile_key="nikola_tesla",
        css=css,
        start_date="2026-07-02",
        end_date="2026-07-04",
    )

    payload = timeline.to_dict()

    assert timeline.count == 3
    assert payload["profile_key"] == "nikola_tesla"
    assert payload["start_date"] == "2026-07-02"
    assert payload["end_date"] == "2026-07-04"
    assert payload["count"] == 3
    assert len(payload["results"]) == 3
    assert payload["results"][0]["evaluation_date"] == "2026-07-02"
    assert payload["results"][0]["success"] is True
    assert payload["metadata"]["runtime"] == "atlas.temporal_runtime.timeline"
