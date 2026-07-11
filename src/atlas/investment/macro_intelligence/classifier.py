"""Deterministic macroeconomic environment classification."""

from __future__ import annotations

import math


def classify_macro_environment(
    indicators: list[dict],
) -> dict:
    """Classify the macro environment from real observations."""
    valid = [
        row
        for row in indicators
        if row.get(
            "z_score"
        ) is not None
    ]

    if len(valid) < 5:
        return {
            "macro_regime": "INSUFFICIENT_DATA",
            "confidence": 0.0,
            "risk_pressure": 0.0,
            "liquidity_support": 0.0,
            "inflation_pressure": 0.0,
            "growth_stress": 0.0,
            "policy_restriction": 0.0,
            "credit_stress": 0.0,
            "component_scores": {},
            "reason_codes": [
                "INSUFFICIENT_VALID_SERIES"
            ],
        }

    by_key = {
        str(row["key"]): row
        for row in valid
    }

    inflation = mean_score([
        positive_z(
            by_key,
            "cpi",
        ),
        positive_z(
            by_key,
            "core_cpi",
        ),
        positive_z(
            by_key,
            "ppi",
        ),
    ])

    labor_stress = mean_score([
        positive_z(
            by_key,
            "unemployment",
        ),
        positive_z(
            by_key,
            "initial_claims",
        ),
    ])

    policy_restriction = mean_score([
        positive_z(
            by_key,
            "fed_funds",
        ),
        positive_z(
            by_key,
            "treasury_2y",
        ),
    ])

    credit_stress = mean_score([
        positive_z(
            by_key,
            "high_yield_spread",
        ),
        positive_z(
            by_key,
            "financial_conditions",
        ),
        positive_z(
            by_key,
            "vix",
        ),
    ])

    dollar_pressure = positive_z(
        by_key,
        "dollar_index",
    )

    liquidity_support = mean_score([
        negative_z(
            by_key,
            "fed_balance_sheet",
        ),
        negative_z(
            by_key,
            "money_supply",
        ),
    ])

    yield_curve = calculate_yield_curve(
        by_key
    )

    curve_stress = clamp(
        -yield_curve / 2.0
    )

    risk_pressure = mean_score([
        inflation,
        labor_stress,
        policy_restriction,
        credit_stress,
        dollar_pressure,
        curve_stress,
    ])

    growth_stress = mean_score([
        labor_stress,
        credit_stress,
        curve_stress,
    ])

    reason_codes: list[str] = []

    if inflation >= 0.65:
        reason_codes.append(
            "ELEVATED_INFLATION_PRESSURE"
        )

    if policy_restriction >= 0.65:
        reason_codes.append(
            "RESTRICTIVE_POLICY"
        )

    if credit_stress >= 0.65:
        reason_codes.append(
            "CREDIT_OR_VOLATILITY_STRESS"
        )

    if liquidity_support >= 0.65:
        reason_codes.append(
            "LIQUIDITY_SUPPORTIVE"
        )

    if growth_stress >= 0.65:
        reason_codes.append(
            "GROWTH_STRESS"
        )

    if curve_stress >= 0.65:
        reason_codes.append(
            "YIELD_CURVE_STRESS"
        )

    if (
        inflation >= 0.60
        and growth_stress >= 0.60
    ):
        regime = "STAGFLATION_PRESSURE"

    elif (
        risk_pressure >= 0.68
        and liquidity_support < 0.45
    ):
        regime = "MACRO_RISK_OFF"

    elif (
        policy_restriction >= 0.60
        and credit_stress < 0.55
    ):
        regime = "RESTRICTIVE_STABILITY"

    elif (
        liquidity_support >= 0.62
        and risk_pressure < 0.55
    ):
        regime = "LIQUIDITY_EXPANSION"

    elif (
        inflation < 0.45
        and growth_stress < 0.45
        and liquidity_support >= 0.45
    ):
        regime = "DISINFLATIONARY_RISK_ON"

    else:
        regime = "MIXED_MACRO"

    confidence = clamp(
        0.35
        + abs(
            risk_pressure
            - 0.50
        ) * 0.50
        + abs(
            liquidity_support
            - 0.50
        ) * 0.20
        + min(
            0.15,
            len(valid) / 100.0,
        )
    )

    return {
        "macro_regime": regime,
        "confidence": round(
            confidence,
            8,
        ),
        "risk_pressure": round(
            risk_pressure,
            8,
        ),
        "liquidity_support": round(
            liquidity_support,
            8,
        ),
        "inflation_pressure": round(
            inflation,
            8,
        ),
        "growth_stress": round(
            growth_stress,
            8,
        ),
        "policy_restriction": round(
            policy_restriction,
            8,
        ),
        "credit_stress": round(
            credit_stress,
            8,
        ),
        "dollar_pressure": round(
            dollar_pressure,
            8,
        ),
        "yield_curve_10y_2y": round(
            yield_curve,
            8,
        ),
        "component_scores": {
            "inflation": round(
                inflation,
                8,
            ),
            "labor_stress": round(
                labor_stress,
                8,
            ),
            "policy_restriction": round(
                policy_restriction,
                8,
            ),
            "credit_stress": round(
                credit_stress,
                8,
            ),
            "dollar_pressure": round(
                dollar_pressure,
                8,
            ),
            "liquidity_support": round(
                liquidity_support,
                8,
            ),
            "curve_stress": round(
                curve_stress,
                8,
            ),
        },
        "reason_codes": reason_codes,
    }


def calculate_yield_curve(
    by_key: dict[str, dict],
) -> float:
    ten_year = value(
        by_key,
        "treasury_10y",
        field="latest_value",
    )

    two_year = value(
        by_key,
        "treasury_2y",
        field="latest_value",
    )

    return ten_year - two_year


def positive_z(
    by_key: dict[str, dict],
    key: str,
) -> float:
    z_score = value(
        by_key,
        key,
        field="z_score",
    )

    return clamp(
        0.50
        + z_score / 6.0
    )


def negative_z(
    by_key: dict[str, dict],
    key: str,
) -> float:
    return 1.0 - positive_z(
        by_key,
        key,
    )


def value(
    by_key: dict[str, dict],
    key: str,
    *,
    field: str,
) -> float:
    row = by_key.get(
        key,
        {}
    )

    return finite(
        row.get(field)
    )


def mean_score(
    values: list[float],
) -> float:
    valid = [
        finite(item)
        for item in values
        if item is not None
    ]

    if not valid:
        return 0.50

    return clamp(
        sum(valid)
        / len(valid)
    )


def finite(
    item,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(item)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )


def clamp(
    item: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            finite(item),
        ),
    )
