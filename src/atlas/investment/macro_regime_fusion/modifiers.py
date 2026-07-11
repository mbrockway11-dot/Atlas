"""Engine-family context modifiers for Macro-Regime Fusion v1."""

from __future__ import annotations

import pandas as pd


FAMILY_BASELINES = {
    "RESTRICTIVE_TRANSITION": {
        "drawdown_recovery": 1.10,
        "volatility_compression": 1.05,
        "trend": 0.90,
        "momentum": 0.85,
        "volatility_expansion": 0.95,
        "mean_reversion": 1.05,
        "market_breadth": 0.90,
    },
    "MACRO_CONFIRMED_RISK_ON": {
        "drawdown_recovery": 0.95,
        "volatility_compression": 0.95,
        "trend": 1.15,
        "momentum": 1.10,
        "volatility_expansion": 1.05,
        "mean_reversion": 0.85,
        "market_breadth": 1.05,
    },
    "DEFENSIVE_RISK_OFF": {
        "drawdown_recovery": 1.15,
        "volatility_compression": 0.90,
        "trend": 0.85,
        "momentum": 0.80,
        "volatility_expansion": 1.05,
        "mean_reversion": 0.85,
        "market_breadth": 0.80,
    },
}


def build_fused_engine_modifiers(
    fused_context: dict,
    engine_summary: pd.DataFrame,
) -> list[dict]:
    """Build bounded context modifiers by registered engine."""
    if (
        engine_summary is None
        or engine_summary.empty
        or "engine_id" not in engine_summary.columns
    ):
        return []

    fused_regime = str(
        fused_context.get(
            "fused_regime",
            "MIXED_CONTEXT",
        )
    )

    confidence = float(
        fused_context.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    mapping = FAMILY_BASELINES.get(
        fused_regime,
        {},
    )

    rows = []

    for _, engine in engine_summary.iterrows():
        family = str(
            engine.get(
                "family",
                "unknown",
            )
        )

        raw = float(
            mapping.get(
                family,
                1.0,
            )
        )

        effective = (
            1.0
            + (
                raw - 1.0
            )
            * confidence
        )

        effective = max(
            0.80,
            min(
                1.20,
                effective,
            ),
        )

        rows.append({
            "engine_id": str(
                engine.get(
                    "engine_id"
                )
            ),
            "family": family,
            "fused_regime": fused_regime,
            "fusion_confidence": confidence,
            "raw_context_modifier": round(
                raw,
                8,
            ),
            "effective_context_modifier": round(
                effective,
                8,
            ),
            "read_only": True,
            "source": "macro_regime_fusion_v1",
        })

    return sorted(
        rows,
        key=lambda row: (
            -row[
                "effective_context_modifier"
            ],
            row["engine_id"],
        ),
    )
