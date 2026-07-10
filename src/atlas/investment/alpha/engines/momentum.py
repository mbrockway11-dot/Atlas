"""Cross-Sectional Momentum Alpha Engine v1."""

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


class CrossSectionalMomentumEngine(AlphaEngine):
    """Score relative momentum across the approved universe."""

    metadata = EngineMetadata(
        engine_id="cross_sectional_momentum_v1",
        version="1.0.0",
        family="momentum",
        holding_period=30,
        description=(
            "Cross-sectional momentum using percentile rank, "
            "30-day momentum, and 30-day return."
        ),
        required_features=(
            "cross_sectional_percentile",
            "momentum_30d",
            "return_30d",
        ),
    )

    def generate(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        rows: list[dict] = []

        for _, row in market.iterrows():
            percentile = clamp(
                finite(
                    row.get(
                        "cross_sectional_percentile"
                    ),
                    default=0.5,
                )
            )

            momentum = finite(
                row.get("momentum_30d")
            )
            return_30d = finite(
                row.get("return_30d")
            )

            momentum_score = signed_score_to_unit(
                momentum,
                scale=0.40,
            )
            return_score = signed_score_to_unit(
                return_30d,
                scale=0.40,
            )

            score = clamp(
                percentile * 0.50
                + momentum_score * 0.30
                + return_score * 0.20
            )

            cross_feature_agreement = (
                1.0
                if (
                    percentile >= 0.60
                    and momentum > 0
                    and return_30d > 0
                )
                or (
                    percentile <= 0.40
                    and momentum < 0
                    and return_30d < 0
                )
                else 0.50
            )

            coverage = feature_coverage(
                row,
                self.metadata.required_features,
            )

            confidence = clamp(
                coverage * 0.60
                + cross_feature_agreement * 0.40
            )

            reasons = [
                (
                    "TOP_CROSS_SECTION"
                    if percentile >= 0.75
                    else (
                        "BOTTOM_CROSS_SECTION"
                        if percentile <= 0.25
                        else "MID_CROSS_SECTION"
                    )
                ),
                (
                    "MOMENTUM_POSITIVE"
                    if momentum > 0
                    else "MOMENTUM_NONPOSITIVE"
                ),
                (
                    "RETURN_30D_POSITIVE"
                    if return_30d > 0
                    else "RETURN_30D_NONPOSITIVE"
                ),
            ]

            rows.append(
                canonical_row(
                    timestamp=row["timestamp"],
                    asset=row["asset"],
                    metadata=self.metadata,
                    raw_score=(
                        percentile
                        + momentum
                        + return_30d
                    ),
                    normalized_score=score,
                    confidence=confidence,
                    regime=str(
                        row.get(
                            "trend_state",
                            "UNKNOWN",
                        )
                    ),
                    reason_codes=reasons,
                )
            )

        return pd.DataFrame(rows)
