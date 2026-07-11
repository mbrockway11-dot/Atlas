"""Drawdown Recovery Alpha Engine v1."""

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


class DrawdownRecoveryEngine(AlphaEngine):
    """Detect recovery or failure from significant drawdowns."""

    metadata = EngineMetadata(
        engine_id="drawdown_recovery_v1",
        version="1.0.0",
        family="drawdown_recovery",
        holding_period=14,
        description=(
            "Recovery engine using drawdown depth, short-term momentum, "
            "moving-average recovery, and volume participation."
        ),
        required_features=(
            "drawdown_from_90d_high",
            "return_7d",
            "momentum_14d",
            "distance_sma_14d",
            "volume_ratio_30d",
        ),
    )

    def generate(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        rows: list[dict] = []

        for _, row in market.iterrows():
            drawdown = min(
                0.0,
                finite(
                    row.get(
                        "drawdown_from_90d_high"
                    )
                ),
            )
            return_7d = finite(
                row.get("return_7d")
            )
            momentum_14d = finite(
                row.get("momentum_14d")
            )
            distance_14d = finite(
                row.get("distance_sma_14d")
            )
            volume_ratio = max(
                0.0,
                finite(
                    row.get("volume_ratio_30d"),
                    default=1.0,
                ),
            )

            recovery_direction = (
                return_7d * 0.35
                + momentum_14d * 0.30
                + distance_14d * 0.35
            )

            recovery_score = signed_score_to_unit(
                recovery_direction,
                scale=0.25,
            )

            drawdown_depth = clamp(
                abs(drawdown) / 0.45
            )

            volume_confirmation = clamp(
                volume_ratio / 1.50
            )

            # Deep drawdowns only strengthen the signal when recovery
            # evidence is present. Otherwise they strengthen the short side.
            score = clamp(
                0.50
                + (
                    recovery_score - 0.50
                )
                * (
                    0.55
                    + drawdown_depth * 0.45
                )
            )

            recovery_alignment = (
                1.0
                if (
                    return_7d > 0
                    and momentum_14d > 0
                    and distance_14d > 0
                )
                or (
                    return_7d < 0
                    and momentum_14d < 0
                    and distance_14d < 0
                )
                else 0.45
            )

            coverage = feature_coverage(
                row,
                self.metadata.required_features,
            )

            confidence = clamp(
                coverage * 0.35
                + drawdown_depth * 0.25
                + recovery_alignment * 0.25
                + volume_confirmation * 0.15
            )

            if drawdown <= -0.30 and recovery_direction > 0:
                regime = "DEEP_RECOVERY"
            elif drawdown <= -0.15 and recovery_direction > 0:
                regime = "RECOVERY"
            elif drawdown <= -0.15 and recovery_direction <= 0:
                regime = "DRAWDOWN_FAILURE"
            else:
                regime = "SHALLOW_DRAWDOWN"

            reasons = [
                f"DRAWDOWN_{regime}",
                (
                    "RETURN_7D_POSITIVE"
                    if return_7d > 0
                    else "RETURN_7D_NONPOSITIVE"
                ),
                (
                    "ABOVE_SMA_14D"
                    if distance_14d > 0
                    else "BELOW_SMA_14D"
                ),
                (
                    "VOLUME_CONFIRMED"
                    if volume_ratio >= 1.0
                    else "LOW_VOLUME"
                ),
            ]

            rows.append(
                canonical_row(
                    timestamp=row["timestamp"],
                    asset=row["asset"],
                    metadata=self.metadata,
                    raw_score=recovery_direction,
                    normalized_score=score,
                    confidence=confidence,
                    regime=regime,
                    reason_codes=reasons,
                )
            )

        return pd.DataFrame(rows)
