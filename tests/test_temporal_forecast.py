"""Tests for Atlas temporal runtime forecast helpers."""

from __future__ import annotations

import pytest

from atlas.core.compiler import compile_profile
from atlas.temporal_runtime import evaluate_forecast


def test_evaluate_forecast_builds_forward_window():
    css = compile_profile("nikola_tesla").to_dict()

    forecast = evaluate_forecast(
        profile_key="nikola_tesla",
        css=css,
        start_date="2026-07-02",
        days=5,
    )

    assert forecast.start_date == "2026-07-02"
    assert forecast.end_date == "2026-07-06"
    assert forecast.count == 5
    assert forecast.summary["summary_status"] == "computed"


def test_evaluate_forecast_rejects_non_positive_days():
    css = compile_profile("nikola_tesla").to_dict()

    with pytest.raises(ValueError, match="days"):
        evaluate_forecast(
            profile_key="nikola_tesla",
            css=css,
            start_date="2026-07-02",
            days=0,
        )
