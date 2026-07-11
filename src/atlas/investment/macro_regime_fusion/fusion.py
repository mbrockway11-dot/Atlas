"""Macro and market-regime fusion logic."""

from __future__ import annotations

import math


def build_fused_context(
    macro_report: dict,
    regime_report: dict,
) -> dict:
    """Combine macro conditions with market-state intelligence."""
    macro_environment = (
        macro_report.get(
            "macro_environment",
            {},
        )
        or {}
    )

    market_regime = (
        regime_report.get(
            "regime",
            {},
        )
        or {}
    )

    macro_name = str(
        macro_environment.get(
            "macro_regime",
            "INSUFFICIENT_DATA",
        )
    )

    market_name = str(
        market_regime.get(
            "regime",
            "INSUFFICIENT_DATA",
        )
    )

    primary_market = str(
        market_regime.get(
            "primary_regime",
            market_name,
        )
    )

    macro_confidence = clamp(
        finite(
            macro_environment.get(
                "confidence"
            )
        )
    )

    market_confidence = clamp(
        finite(
            market_regime.get(
                "confidence"
            )
        )
    )

    market_stability = clamp(
        finite(
            market_regime.get(
                "stability_score"
            )
        )
    )

    risk_pressure = clamp(
        finite(
            macro_environment.get(
                "risk_pressure"
            )
        )
    )

    liquidity_support = clamp(
        finite(
            macro_environment.get(
                "liquidity_support"
            )
        )
    )

    inflation_pressure = clamp(
        finite(
            macro_environment.get(
                "inflation_pressure"
            )
        )
    )

    growth_stress = clamp(
        finite(
            macro_environment.get(
                "growth_stress"
            )
        )
    )

    policy_restriction = clamp(
        finite(
            macro_environment.get(
                "policy_restriction"
            )
        )
    )

    credit_stress = clamp(
        finite(
            macro_environment.get(
                "credit_stress"
            )
        )
    )

    macro_risk_score = clamp(
        risk_pressure * 0.30
        + policy_restriction * 0.20
        + inflation_pressure * 0.15
        + growth_stress * 0.15
        + credit_stress * 0.20
    )

    market_risk_score = market_risk(
        market_name,
        primary_market,
    )

    unified_risk_score = clamp(
        macro_risk_score * 0.55
        + market_risk_score * 0.45
    )

    unified_support_score = clamp(
        liquidity_support * 0.45
        + (
            1.0 - unified_risk_score
        ) * 0.35
        + market_stability * 0.20
    )

    confidence = clamp(
        macro_confidence * 0.45
        + market_confidence * 0.40
        + market_stability * 0.15
    )

    fused_regime = classify_fused_regime(
        macro_name=macro_name,
        market_name=market_name,
        primary_market=primary_market,
        risk_score=unified_risk_score,
        liquidity_support=liquidity_support,
        growth_stress=growth_stress,
        policy_restriction=policy_restriction,
    )

    controls = build_context_controls(
        fused_regime=fused_regime,
        risk_score=unified_risk_score,
        support_score=unified_support_score,
        confidence=confidence,
        market_stability=market_stability,
    )

    reason_codes = build_reason_codes(
        macro_name=macro_name,
        market_name=market_name,
        risk_score=unified_risk_score,
        liquidity_support=liquidity_support,
        policy_restriction=policy_restriction,
        inflation_pressure=inflation_pressure,
        growth_stress=growth_stress,
        credit_stress=credit_stress,
    )

    return {
        "fused_regime": fused_regime,
        "macro_regime": macro_name,
        "market_regime": market_name,
        "primary_market_regime": primary_market,
        "confidence": round(
            confidence,
            8,
        ),
        "macro_risk_score": round(
            macro_risk_score,
            8,
        ),
        "market_risk_score": round(
            market_risk_score,
            8,
        ),
        "unified_risk_score": round(
            unified_risk_score,
            8,
        ),
        "unified_support_score": round(
            unified_support_score,
            8,
        ),
        "liquidity_support": round(
            liquidity_support,
            8,
        ),
        "market_stability": round(
            market_stability,
            8,
        ),
        "controls": controls,
        "reason_codes": reason_codes,
        "source": "macro_regime_fusion_v1",
    }


def classify_fused_regime(
    *,
    macro_name: str,
    market_name: str,
    primary_market: str,
    risk_score: float,
    liquidity_support: float,
    growth_stress: float,
    policy_restriction: float,
) -> str:
    """Classify the unified macro-market context."""
    if (
        macro_name == "INSUFFICIENT_DATA"
        or market_name == "INSUFFICIENT_DATA"
    ):
        return "INSUFFICIENT_DATA"

    if (
        risk_score >= 0.68
        and growth_stress >= 0.55
    ):
        return "DEFENSIVE_RISK_OFF"

    if (
        macro_name == "STAGFLATION_PRESSURE"
        and risk_score >= 0.58
    ):
        return "STAGFLATIONARY_DEFENSE"

    if market_name == "TRANSITION":
        if policy_restriction >= 0.60:
            return "RESTRICTIVE_TRANSITION"

        if liquidity_support >= 0.62:
            return "LIQUIDITY_SUPPORTED_TRANSITION"

        return "NEUTRAL_TRANSITION"

    if primary_market == "CORRELATED_RISK_OFF":
        return "MACRO_CONFIRMED_RISK_OFF"

    if (
        primary_market
        in {
            "BROAD_TRENDING_RISK_ON",
            "SELECTIVE_TRENDING_RISK_ON",
        }
        and liquidity_support >= 0.55
        and risk_score < 0.55
    ):
        return "MACRO_CONFIRMED_RISK_ON"

    if (
        primary_market
        in {
            "BROAD_TRENDING_RISK_ON",
            "SELECTIVE_TRENDING_RISK_ON",
        }
        and policy_restriction >= 0.60
    ):
        return "RESTRICTED_RISK_ON"

    if primary_market == "VOLATILITY_COMPRESSION":
        return "MACRO_CONSTRAINED_COMPRESSION"

    if primary_market == "VOLATILITY_EXPANSION":
        return "MACRO_SENSITIVE_EXPANSION"

    if primary_market == "MEAN_REVERTING_DISPERSION":
        return "MACRO_CONSTRAINED_DISPERSION"

    return "MIXED_CONTEXT"


def build_context_controls(
    *,
    fused_regime: str,
    risk_score: float,
    support_score: float,
    confidence: float,
    market_stability: float,
) -> dict:
    """Produce bounded, read-only portfolio guidance."""
    risk_budget_multiplier = clamp_range(
        1.05
        - risk_score * 0.45
        + support_score * 0.15,
        0.55,
        1.10,
    )

    cash_floor = clamp_range(
        0.10
        + risk_score * 0.45
        + (
            1.0 - market_stability
        ) * 0.15,
        0.10,
        0.70,
    )

    conviction_ceiling = clamp_range(
        0.60
        + confidence * 0.30
        - risk_score * 0.20,
        0.40,
        0.90,
    )

    volatility_target_multiplier = clamp_range(
        1.05
        - risk_score * 0.40,
        0.55,
        1.05,
    )

    turnover_multiplier = clamp_range(
        0.70
        + market_stability * 0.30
        - risk_score * 0.20,
        0.45,
        1.00,
    )

    if "TRANSITION" in fused_regime:
        turnover_multiplier = min(
            turnover_multiplier,
            0.75,
        )

        cash_floor = max(
            cash_floor,
            0.30,
        )

    if "RISK_OFF" in fused_regime:
        cash_floor = max(
            cash_floor,
            0.50,
        )

        risk_budget_multiplier = min(
            risk_budget_multiplier,
            0.70,
        )

    return {
        "risk_budget_multiplier": round(
            risk_budget_multiplier,
            8,
        ),
        "minimum_cash_weight": round(
            cash_floor,
            8,
        ),
        "conviction_ceiling": round(
            conviction_ceiling,
            8,
        ),
        "volatility_target_multiplier": round(
            volatility_target_multiplier,
            8,
        ),
        "turnover_multiplier": round(
            turnover_multiplier,
            8,
        ),
        "read_only": True,
        "execution_instruction": False,
    }


def build_reason_codes(
    *,
    macro_name: str,
    market_name: str,
    risk_score: float,
    liquidity_support: float,
    policy_restriction: float,
    inflation_pressure: float,
    growth_stress: float,
    credit_stress: float,
) -> list[str]:
    reasons = [
        f"MACRO_{macro_name}",
        f"MARKET_{market_name}",
    ]

    if policy_restriction >= 0.60:
        reasons.append(
            "POLICY_RESTRICTION_ELEVATED"
        )

    if inflation_pressure >= 0.60:
        reasons.append(
            "INFLATION_PRESSURE_ELEVATED"
        )

    if liquidity_support >= 0.60:
        reasons.append(
            "LIQUIDITY_SUPPORTIVE"
        )

    if liquidity_support <= 0.40:
        reasons.append(
            "LIQUIDITY_CONSTRAINED"
        )

    if growth_stress >= 0.60:
        reasons.append(
            "GROWTH_STRESS_ELEVATED"
        )

    if credit_stress >= 0.60:
        reasons.append(
            "CREDIT_STRESS_ELEVATED"
        )

    if risk_score >= 0.65:
        reasons.append(
            "UNIFIED_RISK_HIGH"
        )

    return reasons


def market_risk(
    market_name: str,
    primary_market: str,
) -> float:
    mapping = {
        "BROAD_TRENDING_RISK_ON": 0.20,
        "SELECTIVE_TRENDING_RISK_ON": 0.35,
        "VOLATILITY_COMPRESSION": 0.40,
        "MEAN_REVERTING_DISPERSION": 0.50,
        "VOLATILITY_EXPANSION": 0.65,
        "LIQUIDITY_CONTRACTION": 0.75,
        "CORRELATED_RISK_OFF": 0.90,
        "NEUTRAL": 0.50,
        "TRANSITION": 0.58,
    }

    if market_name == "TRANSITION":
        return mapping.get(
            primary_market,
            0.58,
        ) * 0.60 + 0.58 * 0.40

    return mapping.get(
        market_name,
        mapping.get(
            primary_market,
            0.50,
        ),
    )


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
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
    value: float,
) -> float:
    return clamp_range(
        value,
        0.0,
        1.0,
    )


def clamp_range(
    value: float,
    lower: float,
    upper: float,
) -> float:
    return max(
        lower,
        min(
            upper,
            finite(value),
        ),
    )
