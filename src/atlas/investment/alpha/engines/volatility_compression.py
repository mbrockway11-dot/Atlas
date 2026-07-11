"""Volatility Compression Alpha Engine v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha.engines.base import (
    AlphaEngine,
    EngineMetadata,
    canonical_row,
    clamp,
    feature_coverage,
    finite,
    signed_score_to_unit,
)


class VolatilityCompressionEngine(AlphaEngine):
    """Detect compressed volatility with an emerging directional bias."""

    metadata = EngineMetadata(
        engine_id="volatility_compression_v1",
        version="1.0.0",
        family="volatility_compression",
        holding_period=14,
        description=(
            "Compression engine using short-versus-medium volatility, "
            "ATR percentage, trend state, and moving-average location."
        ),
        required_features=(
            "volatility_7d",
            "volatility_30d",
            "atr_pct_14d",
            "distance_sma_14d",
            "return_7d",
            "trend_state",
        ),
    )

    def generate(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        rows: list[dict] = []

        for _, row in market.iterrows():
            volatility_7d = max(
                0.0,
                finite(row.get("volatility_7d")),
            )
            volatility_30d = max(
                0.0,
                finite(row.get("volatility_30d")),
            )
            atr_pct = max(
                0.0,
                finite(row.get("atr_pct_14d")),
            )
            distance_14d = finite(
                row.get("distance_sma_14d")
            )
            return_7d = finite(
                row.get("return_7d")
            )
            trend = str(
                row.get("trend_state", "UNKNOWN")
            ).upper()

            volatility_ratio = (
                volatility_7d / volatility_30d
                if volatility_30d > 0
                else 1.0
            )

            compression_strength = clamp(
                (1.05 - volatility_ratio) / 0.55
            )

            directional_value = (
                return_7d * 0.50
                + distance_14d * 0.50
            )

            directional_score = signed_score_to_unit(
                directional_value,
                scale=0.20,
            )

            trend_bias = {
                "UPTREND": 0.60,
                "DOWNTREND": 0.40,
                "NEUTRAL": 0.50,
                "SIDEWAYS": 0.50,
            }.get(trend, 0.50)

            # Compression moderates the score until a directional
            # bias is observable.
            score = clamp(
                0.50
                + (
                    directional_score - 0.50
                )
                * (
                    0.40
                    + compression_strength * 0.60
                )
                + (
                    trend_bias - 0.50
                )
                * 0.20
            )

            atr_quality = clamp(
                1.0 - atr_pct / 0.15
            )

            alignment = (
                1.0
                if (
                    return_7d > 0
                    and distance_14d > 0
                )
                or (
                    return_7d < 0
                    and distance_14d < 0
                )
                else 0.45
            )

            coverage = feature_coverage(
                row,
                self.metadata.required_features,
            )

            confidence = clamp(
                coverage * 0.40
                + compression_strength * 0.35
                + alignment * 0.15
                + atr_quality * 0.10
            )

            if volatility_ratio <= 0.70:
                regime = "DEEP_COMPRESSION"
            elif volatility_ratio <= 0.90:
                regime = "COMPRESSION"
            else:
                regime = "NOT_COMPRESSED"

            reasons = [
                f"VOLATILITY_{regime}",
                f"TREND_{trend}",
                (
                    "ABOVE_SMA_14D"
                    if distance_14d > 0
                    else "BELOW_SMA_14D"
                ),
                (
                    "RETURN_7D_POSITIVE"
                    if return_7d > 0
                    else "RETURN_7D_NONPOSITIVE"
                ),
            ]

            rows.append(
                canonical_row(
                    timestamp=row["timestamp"],
                    asset=row["asset"],
                    metadata=self.metadata,
                    raw_score=volatility_ratio,
                    normalized_score=score,
                    confidence=confidence,
                    regime=regime,
                    reason_codes=reasons,
                )
            )

        return pd.DataFrame(rows)
