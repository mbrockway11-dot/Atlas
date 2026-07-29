"""Defensive Risk-Off Alpha Engine v1.

The existing engines are all long-biased crypto-beta and highly correlated, so
ensembling them concentrates rather than diversifies (walk-forward confirmed).
This engine is built to be the missing *negative* correlate: it measures a
market-wide risk-off state and, only when that state is present, shorts the
weakest assets. In calm or risk-on markets it stays flat -- low confidence
collapses its signals to INSUFFICIENT_EVIDENCE -- so it contributes almost no
trades during bull runs and activates precisely when the long engines struggle.

Its standalone return in a bull sample is expected to be modest or negative
(shorting into strength is punished); its value is diversification -- being
positive when drawdown_recovery is negative. Whether it delivers that is an
empirical question the walk-forward answers, not an assumption.
"""

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


class DefensiveRiskOffEngine(AlphaEngine):
    """Short the weakest assets only when the market is broadly risk-off."""

    metadata = EngineMetadata(
        engine_id="defensive_risk_off_v1",
        version="1.0.0",
        family="defensive_risk_off",
        holding_period=14,
        description=(
            "Risk-off hedge engine: a market-wide risk-off gate (breadth, "
            "downtrend share, mean drawdown, volatility expansion, market "
            "momentum) activates short signals on the weakest assets, and "
            "stays flat when the market is calm or risk-on."
        ),
        required_features=(
            "return_7d",
            "momentum_30d",
            "distance_sma_30d",
            "drawdown_from_90d_high",
            "volatility_7d",
            "volatility_30d",
            "trend_state",
        ),
    )

    def generate(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        frame = market.copy()

        frame["_return_7d"] = pd.to_numeric(
            frame["return_7d"],
            errors="coerce",
        )
        frame["_momentum_30d"] = pd.to_numeric(
            frame["momentum_30d"],
            errors="coerce",
        )
        frame["_drawdown"] = pd.to_numeric(
            frame["drawdown_from_90d_high"],
            errors="coerce",
        )
        frame["_vol_7d"] = pd.to_numeric(
            frame["volatility_7d"],
            errors="coerce",
        )
        frame["_vol_30d"] = pd.to_numeric(
            frame["volatility_30d"],
            errors="coerce",
        )
        frame["_positive_7d"] = (
            frame["_return_7d"] > 0
        ).astype(float)
        frame["_downtrend"] = (
            frame["trend_state"]
            .astype(str)
            .str.upper()
            .eq("DOWNTREND")
        ).astype(float)

        aggregates = (
            frame.groupby("timestamp", sort=True)
            .agg(
                breadth_7d=("_positive_7d", "mean"),
                downtrend_share=("_downtrend", "mean"),
                mean_drawdown=("_drawdown", "mean"),
                mean_momentum=("_momentum_30d", "mean"),
                mean_vol_7d=("_vol_7d", "mean"),
                mean_vol_30d=("_vol_30d", "mean"),
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
            risk_off = self._market_risk_off(row)

            # Asset bearishness: positive when the asset is falling.
            bear_raw = -(
                finite(row.get("_momentum_30d")) * 0.40
                + finite(row.get("distance_sma_30d")) * 0.35
                + finite(row.get("_return_7d")) * 0.25
            )

            # Short pressure only builds when the market is risk-off AND the
            # asset is weak; in calm markets this collapses toward zero.
            short_pressure = risk_off * bear_raw

            score = signed_score_to_unit(
                -short_pressure,
                scale=0.12,
            )

            coverage = feature_coverage(
                row,
                self.metadata.required_features,
            )

            confidence = clamp(
                coverage * 0.35
                + risk_off * 0.45
                + clamp(abs(bear_raw) / 0.20) * 0.20
            )

            if risk_off >= 0.60:
                regime = "RISK_OFF"
            elif risk_off >= 0.40:
                regime = "ELEVATED_RISK"
            else:
                regime = "RISK_ON"

            reasons = [
                f"MARKET_{regime}",
                (
                    "WEAK_BREADTH"
                    if finite(row.get("breadth_7d"), default=0.5) < 0.5
                    else "BROAD_BREADTH"
                ),
                (
                    "ASSET_BEARISH"
                    if bear_raw > 0
                    else "ASSET_FIRM"
                ),
                (
                    "VOL_EXPANDING"
                    if finite(row.get("mean_vol_7d"))
                    > finite(row.get("mean_vol_30d"))
                    else "VOL_STABLE"
                ),
            ]

            rows.append(
                canonical_row(
                    timestamp=row["timestamp"],
                    asset=row["asset"],
                    metadata=self.metadata,
                    raw_score=short_pressure,
                    normalized_score=score,
                    confidence=confidence,
                    regime=regime,
                    reason_codes=reasons,
                )
            )

        return pd.DataFrame(rows)

    @staticmethod
    def _market_risk_off(row: pd.Series) -> float:
        """Combine market-wide features into a [0, 1] risk-off score."""
        breadth_7d = clamp(
            finite(row.get("breadth_7d"), default=0.5)
        )
        downtrend_share = clamp(
            finite(row.get("downtrend_share"))
        )
        mean_drawdown = min(
            0.0,
            finite(row.get("mean_drawdown")),
        )
        mean_momentum = finite(row.get("mean_momentum"))
        vol_7d = finite(row.get("mean_vol_7d"))
        vol_30d = max(finite(row.get("mean_vol_30d")), 1e-9)
        vol_expansion = vol_7d / vol_30d

        momentum_risk = (
            clamp(-mean_momentum / 0.20)
            if mean_momentum < 0
            else 0.0
        )

        return clamp(
            (1.0 - breadth_7d) * 0.30
            + downtrend_share * 0.25
            + clamp(abs(mean_drawdown) / 0.35) * 0.20
            + clamp((vol_expansion - 1.0) / 0.60) * 0.15
            + momentum_risk * 0.10
        )
