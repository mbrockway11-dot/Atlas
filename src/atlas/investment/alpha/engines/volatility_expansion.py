"""Volatility Expansion Alpha Engine v1."""

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


class VolatilityExpansionEngine(AlphaEngine):
    """Detect directional short-term volatility expansion."""

    metadata = EngineMetadata(
        engine_id="volatility_expansion_v1",
        version="1.0.0",
        family="volatility_expansion",
        holding_period=7,
        description=(
            "Directional volatility expansion using the ratio of "
            "7-day to 30-day volatility and short-horizon returns."
        ),
        required_features=(
            "volatility_7d",
            "volatility_30d",
            "return_1d",
            "return_7d",
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

            return_1d = finite(
                row.get("return_1d")
            )
            return_7d = finite(
                row.get("return_7d")
            )

            expansion_ratio = (
                volatility_7d / volatility_30d
                if volatility_30d > 0
                else 0.0
            )

            expansion_strength = clamp(
                (expansion_ratio - 0.80) / 1.20
            )

            direction_score = signed_score_to_unit(
                return_1d * 0.40
                + return_7d * 0.60,
                scale=0.20,
            )

            score = clamp(
                0.50
                + (
                    direction_score - 0.50
                )
                * (
                    0.35
                    + expansion_strength * 0.65
                )
            )

            directional_alignment = (
                1.0
                if (
                    return_1d > 0
                    and return_7d > 0
                )
                or (
                    return_1d < 0
                    and return_7d < 0
                )
                else 0.45
            )

            coverage = feature_coverage(
                row,
                self.metadata.required_features,
            )

            confidence = clamp(
                coverage * 0.45
                + expansion_strength * 0.35
                + directional_alignment * 0.20
            )

            if expansion_ratio >= 1.25:
                expansion_state = "EXPANDING"
            elif expansion_ratio <= 0.80:
                expansion_state = "COMPRESSED"
            else:
                expansion_state = "NORMAL"

            reasons = [
                f"VOLATILITY_{expansion_state}",
                (
                    "RETURN_1D_POSITIVE"
                    if return_1d > 0
                    else "RETURN_1D_NONPOSITIVE"
                ),
                (
                    "RETURN_7D_POSITIVE"
                    if return_7d > 0
                    else "RETURN_7D_NONPOSITIVE"
                ),
                (
                    "DIRECTION_ALIGNED"
                    if directional_alignment >= 1.0
                    else "DIRECTION_MIXED"
                ),
            ]

            rows.append(
                canonical_row(
                    timestamp=row["timestamp"],
                    asset=row["asset"],
                    metadata=self.metadata,
                    raw_score=expansion_ratio,
                    normalized_score=score,
                    confidence=confidence,
                    regime=expansion_state,
                    reason_codes=reasons,
                )
            )

        return pd.DataFrame(rows)
