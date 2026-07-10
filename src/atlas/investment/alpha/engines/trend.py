"""Trend Continuation Alpha Engine v1."""

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


class TrendContinuationEngine(AlphaEngine):
    """Score persistent multi-horizon directional trends."""

    metadata = EngineMetadata(
        engine_id="trend_continuation_v1",
        version="1.0.0",
        family="trend",
        holding_period=30,
        description=(
            "Multi-horizon trend continuation using trend state, "
            "30-day momentum, and 90-day momentum."
        ),
        required_features=(
            "trend_state",
            "momentum_30d",
            "momentum_90d",
        ),
    )

    def generate(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        rows: list[dict] = []

        for _, row in market.iterrows():
            trend = str(
                row.get("trend_state", "UNKNOWN")
            ).upper()

            momentum_30d = finite(
                row.get("momentum_30d")
            )
            momentum_90d = finite(
                row.get("momentum_90d")
            )

            momentum_30_score = signed_score_to_unit(
                momentum_30d,
                scale=0.40,
            )
            momentum_90_score = signed_score_to_unit(
                momentum_90d,
                scale=0.80,
            )

            trend_score = {
                "UPTREND": 1.0,
                "DOWNTREND": 0.0,
                "NEUTRAL": 0.5,
                "SIDEWAYS": 0.5,
            }.get(trend, 0.5)

            score = clamp(
                trend_score * 0.40
                + momentum_30_score * 0.35
                + momentum_90_score * 0.25
            )

            alignment = (
                1.0
                if (
                    trend == "UPTREND"
                    and momentum_30d > 0
                    and momentum_90d > 0
                )
                or (
                    trend == "DOWNTREND"
                    and momentum_30d < 0
                    and momentum_90d < 0
                )
                else 0.55
            )

            coverage = feature_coverage(
                row,
                self.metadata.required_features,
            )

            confidence = clamp(
                coverage * 0.60
                + alignment * 0.40
            )

            reasons = [
                f"TREND_{trend}",
                (
                    "MOMENTUM_30D_POSITIVE"
                    if momentum_30d > 0
                    else "MOMENTUM_30D_NONPOSITIVE"
                ),
                (
                    "MOMENTUM_90D_POSITIVE"
                    if momentum_90d > 0
                    else "MOMENTUM_90D_NONPOSITIVE"
                ),
            ]

            rows.append(
                canonical_row(
                    timestamp=row["timestamp"],
                    asset=row["asset"],
                    metadata=self.metadata,
                    raw_score=(
                        momentum_30d * 0.60
                        + momentum_90d * 0.40
                    ),
                    normalized_score=score,
                    confidence=confidence,
                    regime=trend,
                    reason_codes=reasons,
                )
            )

        return pd.DataFrame(rows)
