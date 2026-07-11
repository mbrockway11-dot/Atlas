"""Market Breadth Alpha Engine v1."""

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


class MarketBreadthEngine(AlphaEngine):
    """Measure market-wide participation and asset alignment."""

    metadata = EngineMetadata(
        engine_id="market_breadth_v1",
        version="1.0.0",
        family="market_breadth",
        holding_period=7,
        description=(
            "Market participation engine using positive-return breadth, "
            "trend breadth, and each asset's alignment with the market."
        ),
        required_features=(
            "return_1d",
            "return_7d",
            "trend_state",
        ),
    )

    def generate(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        frame = market.copy()

        frame["return_1d_numeric"] = pd.to_numeric(
            frame["return_1d"],
            errors="coerce",
        )
        frame["return_7d_numeric"] = pd.to_numeric(
            frame["return_7d"],
            errors="coerce",
        )

        frame["positive_1d"] = (
            frame["return_1d_numeric"] > 0
        ).astype(float)

        frame["positive_7d"] = (
            frame["return_7d_numeric"] > 0
        ).astype(float)

        frame["uptrend_flag"] = (
            frame["trend_state"]
            .astype(str)
            .str.upper()
            .eq("UPTREND")
        ).astype(float)

        frame["downtrend_flag"] = (
            frame["trend_state"]
            .astype(str)
            .str.upper()
            .eq("DOWNTREND")
        ).astype(float)

        aggregates = (
            frame.groupby(
                "timestamp",
                sort=True,
            )
            .agg(
                breadth_1d=(
                    "positive_1d",
                    "mean",
                ),
                breadth_7d=(
                    "positive_7d",
                    "mean",
                ),
                uptrend_share=(
                    "uptrend_flag",
                    "mean",
                ),
                downtrend_share=(
                    "downtrend_flag",
                    "mean",
                ),
                breadth_asset_count=(
                    "asset",
                    "count",
                ),
            )
            .reset_index()
        )

        frame = frame.merge(
            aggregates,
            on="timestamp",
            how="left",
        )

        rows: list[dict] = []

        for _, row in frame.iterrows():
            breadth_1d = clamp(
                finite(row.get("breadth_1d"), default=0.5)
            )
            breadth_7d = clamp(
                finite(row.get("breadth_7d"), default=0.5)
            )
            uptrend_share = clamp(
                finite(row.get("uptrend_share"))
            )
            downtrend_share = clamp(
                finite(row.get("downtrend_share"))
            )

            market_score = clamp(
                breadth_1d * 0.30
                + breadth_7d * 0.35
                + uptrend_share * 0.25
                + (
                    1.0 - downtrend_share
                )
                * 0.10
            )

            asset_return_7d = finite(
                row.get("return_7d_numeric")
            )

            asset_alignment = signed_score_to_unit(
                asset_return_7d,
                scale=0.20,
            )

            score = clamp(
                market_score * 0.70
                + asset_alignment * 0.30
            )

            participation_extremity = clamp(
                abs(market_score - 0.50) * 2.0
            )

            asset_count = int(
                finite(
                    row.get("breadth_asset_count")
                )
            )

            sample_quality = clamp(
                asset_count / 10.0
            )

            coverage = feature_coverage(
                row,
                self.metadata.required_features,
            )

            confidence = clamp(
                coverage * 0.35
                + sample_quality * 0.30
                + participation_extremity * 0.25
                + 0.10
            )

            if market_score >= 0.70:
                regime = "BROAD_RISK_ON"
            elif market_score <= 0.30:
                regime = "BROAD_RISK_OFF"
            else:
                regime = "SELECTIVE"

            reasons = [
                f"BREADTH_{regime}",
                (
                    "MAJORITY_POSITIVE_1D"
                    if breadth_1d >= 0.50
                    else "MAJORITY_NEGATIVE_1D"
                ),
                (
                    "MAJORITY_POSITIVE_7D"
                    if breadth_7d >= 0.50
                    else "MAJORITY_NEGATIVE_7D"
                ),
                (
                    "ASSET_ALIGNED_POSITIVE"
                    if asset_return_7d > 0
                    else "ASSET_ALIGNED_NEGATIVE"
                ),
            ]

            rows.append(
                canonical_row(
                    timestamp=row["timestamp"],
                    asset=row["asset"],
                    metadata=self.metadata,
                    raw_score=market_score,
                    normalized_score=score,
                    confidence=confidence,
                    regime=regime,
                    reason_codes=reasons,
                )
            )

        return pd.DataFrame(rows)
