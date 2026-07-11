"""Regime-to-engine suitability for Regime Intelligence v1."""

from __future__ import annotations


REGIME_ENGINE_SUITABILITY = {
    "BROAD_TRENDING_RISK_ON": {
        "trend": 1.00,
        "momentum": 0.90,
        "volatility_expansion": 0.65,
        "volatility_compression": 0.35,
        "mean_reversion": 0.15,
        "market_breadth": 0.85,
        "drawdown_recovery": 0.50,
    },
    "SELECTIVE_TRENDING_RISK_ON": {
        "trend": 0.90,
        "momentum": 0.75,
        "volatility_expansion": 0.60,
        "volatility_compression": 0.40,
        "mean_reversion": 0.25,
        "market_breadth": 0.55,
        "drawdown_recovery": 0.65,
    },
    "VOLATILITY_EXPANSION": {
        "trend": 0.70,
        "momentum": 0.65,
        "volatility_expansion": 1.00,
        "volatility_compression": 0.20,
        "mean_reversion": 0.30,
        "market_breadth": 0.45,
        "drawdown_recovery": 0.60,
    },
    "VOLATILITY_COMPRESSION": {
        "trend": 0.40,
        "momentum": 0.30,
        "volatility_expansion": 0.55,
        "volatility_compression": 1.00,
        "mean_reversion": 0.65,
        "market_breadth": 0.40,
        "drawdown_recovery": 0.45,
    },
    "MEAN_REVERTING_DISPERSION": {
        "trend": 0.25,
        "momentum": 0.20,
        "volatility_expansion": 0.45,
        "volatility_compression": 0.60,
        "mean_reversion": 1.00,
        "market_breadth": 0.35,
        "drawdown_recovery": 0.75,
    },
    "CORRELATED_RISK_OFF": {
        "trend": 0.45,
        "momentum": 0.30,
        "volatility_expansion": 0.75,
        "volatility_compression": 0.20,
        "mean_reversion": 0.25,
        "market_breadth": 0.20,
        "drawdown_recovery": 0.55,
    },
    "LIQUIDITY_CONTRACTION": {
        "trend": 0.35,
        "momentum": 0.25,
        "volatility_expansion": 0.40,
        "volatility_compression": 0.35,
        "mean_reversion": 0.20,
        "market_breadth": 0.15,
        "drawdown_recovery": 0.45,
    },
    "TRANSITION": {
        "trend": 0.40,
        "momentum": 0.35,
        "volatility_expansion": 0.45,
        "volatility_compression": 0.45,
        "mean_reversion": 0.40,
        "market_breadth": 0.35,
        "drawdown_recovery": 0.55,
    },
    "NEUTRAL": {
        "trend": 0.50,
        "momentum": 0.50,
        "volatility_expansion": 0.50,
        "volatility_compression": 0.50,
        "mean_reversion": 0.50,
        "market_breadth": 0.50,
        "drawdown_recovery": 0.50,
    },
}


def build_engine_suitability(
    regime_report: dict,
    engine_summary,
) -> list[dict]:
    """Create read-only regime suitability rows."""
    regime = str(
        regime_report.get(
            "regime",
            "NEUTRAL",
        )
    )

    if regime == "TRANSITION":
        regime = str(
            regime_report.get(
                "primary_regime",
                "TRANSITION",
            )
        )

    mapping = REGIME_ENGINE_SUITABILITY.get(
        regime,
        REGIME_ENGINE_SUITABILITY[
            "NEUTRAL"
        ],
    )

    confidence = float(
        regime_report.get(
            "confidence",
            0.0,
        )
        or 0.0
    )

    rows = []

    if (
        engine_summary is None
        or engine_summary.empty
        or "engine_id" not in engine_summary.columns
    ):
        return rows

    for _, engine in engine_summary.iterrows():
        family = str(
            engine.get(
                "family",
                "unknown",
            )
        )

        suitability = float(
            mapping.get(
                family,
                0.50,
            )
        )

        effective = (
            0.50
            + (
                suitability - 0.50
            )
            * confidence
        )

        rows.append({
            "engine_id": str(
                engine.get(
                    "engine_id"
                )
            ),
            "family": family,
            "market_regime": str(
                regime_report.get(
                    "regime"
                )
            ),
            "primary_regime": str(
                regime_report.get(
                    "primary_regime"
                )
            ),
            "regime_confidence": confidence,
            "raw_suitability": round(
                suitability,
                8,
            ),
            "effective_suitability": round(
                effective,
                8,
            ),
            "read_only": True,
            "source": (
                "regime_intelligence_v1"
            ),
        })

    return sorted(
        rows,
        key=lambda row: (
            -row[
                "effective_suitability"
            ],
            row["engine_id"],
        ),
    )
