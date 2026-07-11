"""Tests for Macro Intelligence v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.macro_intelligence.classifier import (
    classify_macro_environment,
)
from atlas.investment.macro_intelligence.features import (
    calculate_series_features,
)


def sample_series() -> pd.DataFrame:
    return pd.DataFrame({
        "date": pd.date_range(
            "2020-01-01",
            periods=72,
            freq="MS",
            tz="UTC",
        ),
        "value": [
            100.0 + index
            for index in range(72)
        ],
    })


def indicator(
    key: str,
    z_score: float,
    latest_value: float = 1.0,
) -> dict:
    return {
        "key": key,
        "z_score": z_score,
        "latest_value": latest_value,
    }


def test_year_over_year_features_are_calculated():
    result = calculate_series_features(
        sample_series(),
        transform="year_over_year",
    )

    assert result[
        "observation_count"
    ] == 72

    assert result[
        "transformed_value"
    ] is not None

    assert result[
        "z_score"
    ] is not None


def test_classifier_requires_real_coverage():
    result = classify_macro_environment(
        []
    )

    assert (
        result["macro_regime"]
        == "INSUFFICIENT_DATA"
    )


def test_macro_classifier_is_deterministic():
    indicators = [
        indicator("cpi", 1.0),
        indicator("core_cpi", 1.0),
        indicator("ppi", 0.8),
        indicator("unemployment", 0.2),
        indicator("initial_claims", 0.3),
        indicator("fed_funds", 1.2),
        indicator("treasury_2y", 1.0, 4.5),
        indicator("treasury_10y", 0.8, 4.1),
        indicator("vix", 0.4),
        indicator("high_yield_spread", 0.3),
        indicator("financial_conditions", 0.2),
        indicator("dollar_index", 0.5),
        indicator("fed_balance_sheet", -0.5),
        indicator("money_supply", -0.4),
    ]

    first = classify_macro_environment(
        indicators
    )

    second = classify_macro_environment(
        indicators
    )

    assert first == second


def test_classifier_returns_bounded_scores():
    indicators = [
        indicator("cpi", 2.0),
        indicator("core_cpi", 2.0),
        indicator("ppi", 2.0),
        indicator("unemployment", 2.0),
        indicator("initial_claims", 2.0),
        indicator("fed_funds", 2.0),
        indicator("treasury_2y", 2.0, 5.0),
        indicator("treasury_10y", 2.0, 3.5),
        indicator("vix", 2.0),
        indicator("high_yield_spread", 2.0),
        indicator("financial_conditions", 2.0),
        indicator("dollar_index", 2.0),
        indicator("fed_balance_sheet", 2.0),
        indicator("money_supply", 2.0),
    ]

    result = classify_macro_environment(
        indicators
    )

    for field in [
        "confidence",
        "risk_pressure",
        "liquidity_support",
        "inflation_pressure",
        "growth_stress",
        "policy_restriction",
        "credit_stress",
    ]:
        assert 0.0 <= result[field] <= 1.0
