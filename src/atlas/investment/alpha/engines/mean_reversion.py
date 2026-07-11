"""Mean Reversion Alpha Engine v1."""

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


class MeanReversionEngine(AlphaEngine):
    """Detect statistically stretched short-horizon price conditions."""

    metadata = EngineMetadata(
        engine_id="mean_reversion_v1",
        version="1.0.0",
        family="mean_reversion",
        holding_period=7,
        description=(
            "Contrarian engine using short-term returns, moving-average "
            "distance, and drawdown from the 90-day high."
        ),
        required_features=(
            "return_7d",
            "distance_sma_7d",
            "distance_sma_30d",
            "drawdown_from_90d_high",
        ),
    )

    def generate(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        rows: list[dict] = []

        for _, row in market.iterrows():
            return_7d = finite(
                row.get("return_7d")
            )
            distance_7d = finite(
                row.get("distance_sma_7d")
            )
            distance_30d = finite(
                row.get("distance_sma_30d")
            )
            drawdown = finite(
                row.get("drawdown_from_90d_high")
            )

            stretch = (
                return_7d * 0.35
                + distance_7d * 0.30
                + distance_30d * 0.25
                + drawdown * 0.10
            )

            # Invert the directional stretch:
            # negative stretch becomes a long reversion score,
            # positive stretch becomes a short reversion score.
            score = signed_score_to_unit(
                -stretch,
                scale=0.25,
            )

            short_term_alignment = (
                1.0
                if (
                    return_7d < 0
                    and distance_7d < 0
                    and distance_30d < 0
                )
                or (
                    return_7d > 0
                    and distance_7d > 0
                    and distance_30d > 0
                )
                else 0.45
            )

            extremity = clamp(
                abs(stretch) / 0.20
            )

            coverage = feature_coverage(
                row,
                self.metadata.required_features,
            )

            confidence = clamp(
                coverage * 0.45
                + extremity * 0.35
                + short_term_alignment * 0.20
            )

            if stretch <= -0.12:
                regime = "OVERSOLD"
            elif stretch >= 0.12:
                regime = "OVERBOUGHT"
            else:
                regime = "BALANCED"

            reasons = [
                f"REVERSION_{regime}",
                (
                    "RETURN_7D_NEGATIVE"
                    if return_7d < 0
                    else "RETURN_7D_NONNEGATIVE"
                ),
                (
                    "BELOW_SMA_7D"
                    if distance_7d < 0
                    else "ABOVE_SMA_7D"
                ),
                (
                    "BELOW_SMA_30D"
                    if distance_30d < 0
                    else "ABOVE_SMA_30D"
                ),
            ]

            rows.append(
                canonical_row(
                    timestamp=row["timestamp"],
                    asset=row["asset"],
                    metadata=self.metadata,
                    raw_score=stretch,
                    normalized_score=score,
                    confidence=confidence,
                    regime=regime,
                    reason_codes=reasons,
                )
            )

        return pd.DataFrame(rows)
