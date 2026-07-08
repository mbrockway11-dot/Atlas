
"""Alpha Hypothesis Generator."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

import pandas as pd


MARKET_FEATURES = Path("output/investment_alpha/market_features.csv")
ASSET_FEATURES = Path("output/investment_alpha/market_asset_features.csv")


@dataclass
class AlphaHypothesis:
    hypothesis_id: str
    family: str
    description: str
    signal_asset_rule: str
    conditions: list[dict[str, Any]]
    direction: str = "LONG"
    hold_period: int = 72
    rank_score: float = 1.0


def load_features(
    market_features_path: str | Path = MARKET_FEATURES,
    asset_features_path: str | Path = ASSET_FEATURES,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load generated market feature frames."""
    market = pd.read_csv(market_features_path) if Path(market_features_path).exists() else pd.DataFrame()
    asset = pd.read_csv(asset_features_path) if Path(asset_features_path).exists() else pd.DataFrame()
    return market, asset


def build_alpha_hypotheses(
    *,
    market_features_path: str | Path = MARKET_FEATURES,
    asset_features_path: str | Path = ASSET_FEATURES,
    max_per_family: int = 25,
) -> dict[str, Any]:
    """Generate candidate alpha hypotheses from feature columns."""
    market, asset = load_features(market_features_path, asset_features_path)

    if market.empty or asset.empty:
        return {
            "success": False,
            "error": "Missing market or asset feature files. Run scripts/build_market_features.py first.",
            "hypotheses": [],
        }

    hypotheses: list[AlphaHypothesis] = []

    hypotheses.extend(generate_momentum_hypotheses(asset, max_per_family=max_per_family))
    hypotheses.extend(generate_breadth_hypotheses(market, max_per_family=max_per_family))
    hypotheses.extend(generate_volatility_hypotheses(market, max_per_family=max_per_family))
    hypotheses.extend(generate_leadership_hypotheses(market, max_per_family=max_per_family))
    hypotheses.extend(generate_topology_hypotheses(market, max_per_family=max_per_family))

    rows = [asdict(h) for h in hypotheses]

    return {
        "success": True,
        "hypothesis_count": len(rows),
        "families": family_counts(rows),
        "hypotheses": rows,
        "summary": f"Alpha Hypothesis Generator produced {len(rows)} candidate rule(s).",
    }


def quantiles(df: pd.DataFrame, column: str) -> dict[str, float]:
    """Get useful quantiles for a numeric column."""
    s = pd.to_numeric(df[column], errors="coerce").dropna()
    if s.empty:
        return {}

    return {
        "q25": round(float(s.quantile(0.25)), 8),
        "q50": round(float(s.quantile(0.50)), 8),
        "q75": round(float(s.quantile(0.75)), 8),
        "q90": round(float(s.quantile(0.90)), 8),
    }


def condition(feature: str, op: str, value: Any, source: str = "market") -> dict[str, Any]:
    return {
        "source": source,
        "feature": feature,
        "op": op,
        "value": value,
    }


def generate_momentum_hypotheses(asset: pd.DataFrame, *, max_per_family: int) -> list[AlphaHypothesis]:
    """Generate momentum hypotheses."""
    hypotheses = []
    windows = [24, 72, 288]

    for window in windows:
        ret_col = f"return_{window}"
        rank_col = f"rank_return_{window}"

        if ret_col not in asset.columns or rank_col not in asset.columns:
            continue

        q = quantiles(asset, ret_col)
        if not q:
            continue

        for threshold_name in ["q50", "q75", "q90"]:
            threshold = q[threshold_name]

            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id=f"momentum_top_rank_{window}_{threshold_name}",
                    family="momentum",
                    description=(
                        f"Long strongest-ranked asset when {window}-period return "
                        f"is above {threshold_name} threshold."
                    ),
                    signal_asset_rule=f"asset_with_min_rank_return_{window}",
                    conditions=[
                        condition(rank_col, "<=", 1, source="asset"),
                        condition(ret_col, ">", threshold, source="asset"),
                    ],
                    hold_period=window,
                    rank_score=score_threshold(threshold_name),
                )
            )

    return hypotheses[:max_per_family]


def generate_breadth_hypotheses(market: pd.DataFrame, *, max_per_family: int) -> list[AlphaHypothesis]:
    """Generate market breadth hypotheses."""
    hypotheses = []

    for window in [24, 72, 288]:
        breadth_col = f"breadth_positive_{window}"
        spread_col = f"spread_return_{window}"

        if breadth_col not in market.columns:
            continue

        breadth_q = quantiles(market, breadth_col)

        for level in [0.5, 0.66, 0.8, 1.0]:
            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id=f"breadth_positive_{window}_{str(level).replace('.', '_')}",
                    family="breadth",
                    description=f"Long leader when {int(level * 100)}%+ of assets are positive over {window}.",
                    signal_asset_rule=f"leader_asset_{window}",
                    conditions=[
                        condition(breadth_col, ">=", level),
                    ],
                    hold_period=window,
                    rank_score=level,
                )
            )

        if spread_col in market.columns:
            q = quantiles(market, spread_col)
            if q:
                hypotheses.append(
                    AlphaHypothesis(
                        hypothesis_id=f"breadth_dispersion_breakout_{window}",
                        family="breadth",
                        description=f"Long leader when cross-sectional spread is elevated over {window}.",
                        signal_asset_rule=f"leader_asset_{window}",
                        conditions=[
                            condition(spread_col, ">", q["q75"]),
                            condition(breadth_col, ">=", 0.5),
                        ],
                        hold_period=window,
                        rank_score=0.75,
                    )
                )

    return hypotheses[:max_per_family]


def generate_volatility_hypotheses(market: pd.DataFrame, *, max_per_family: int) -> list[AlphaHypothesis]:
    """Generate volatility/compression hypotheses."""
    hypotheses = []

    if "vol_compression_72_vs_288" in market.columns:
        q = quantiles(market, "vol_compression_72_vs_288")
        if q:
            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id="volatility_compression_leader_72",
                    family="volatility",
                    description="Long 72-period leader after volatility compression.",
                    signal_asset_rule="leader_asset_72",
                    conditions=[
                        condition("vol_compression_72_vs_288", "<", q["q25"]),
                    ],
                    hold_period=72,
                    rank_score=0.75,
                )
            )

    if "vol_expansion_24_vs_72" in market.columns:
        q = quantiles(market, "vol_expansion_24_vs_72")
        if q:
            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id="volatility_expansion_leader_24",
                    family="volatility",
                    description="Long 24-period leader during volatility expansion.",
                    signal_asset_rule="leader_asset_24",
                    conditions=[
                        condition("vol_expansion_24_vs_72", ">", q["q75"]),
                    ],
                    hold_period=24,
                    rank_score=0.65,
                )
            )

    return hypotheses[:max_per_family]


def generate_leadership_hypotheses(market: pd.DataFrame, *, max_per_family: int) -> list[AlphaHypothesis]:
    """Generate leadership persistence/rotation hypotheses."""
    hypotheses = []

    for window in [24, 72, 288]:
        persistence_col = f"leader_persistence_{window}"
        changed_col = f"leader_changed_{window}"
        spread_col = f"leader_laggard_spread_{window}"

        if persistence_col in market.columns:
            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id=f"leader_persistence_{window}_3",
                    family="leadership",
                    description=f"Long leader when leadership persists for at least 3 bars over {window}.",
                    signal_asset_rule=f"leader_asset_{window}",
                    conditions=[
                        condition(persistence_col, ">=", 3),
                    ],
                    hold_period=window,
                    rank_score=0.7,
                )
            )

            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id=f"leader_persistence_{window}_8",
                    family="leadership",
                    description=f"Long leader when leadership persists for at least 8 bars over {window}.",
                    signal_asset_rule=f"leader_asset_{window}",
                    conditions=[
                        condition(persistence_col, ">=", 8),
                    ],
                    hold_period=window,
                    rank_score=0.8,
                )
            )

        if changed_col in market.columns and spread_col in market.columns:
            q = quantiles(market, spread_col)
            if q:
                hypotheses.append(
                    AlphaHypothesis(
                        hypothesis_id=f"leadership_rotation_breakout_{window}",
                        family="leadership",
                        description=f"Long new leader after leadership rotation with elevated spread over {window}.",
                        signal_asset_rule=f"leader_asset_{window}",
                        conditions=[
                            condition(changed_col, "==", 1),
                            condition(spread_col, ">", q["q75"]),
                        ],
                        hold_period=window,
                        rank_score=0.75,
                    )
                )

    return hypotheses[:max_per_family]


def generate_topology_hypotheses(market: pd.DataFrame, *, max_per_family: int) -> list[AlphaHypothesis]:
    """Generate topology hypotheses."""
    hypotheses = []

    if "graph_density" in market.columns:
        q = quantiles(market, "graph_density")
        if q:
            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id="topology_high_density_leader_72",
                    family="topology",
                    description="Long 72-period leader when correlation graph density is high.",
                    signal_asset_rule="leader_asset_72",
                    conditions=[
                        condition("graph_density", ">", q["q75"]),
                    ],
                    hold_period=72,
                    rank_score=0.7,
                )
            )

            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id="topology_low_density_leader_72",
                    family="topology",
                    description="Long 72-period leader when correlation graph density is low.",
                    signal_asset_rule="leader_asset_72",
                    conditions=[
                        condition("graph_density", "<", q["q25"]),
                    ],
                    hold_period=72,
                    rank_score=0.6,
                )
            )

    if "avg_abs_corr" in market.columns:
        q = quantiles(market, "avg_abs_corr")
        if q:
            hypotheses.append(
                AlphaHypothesis(
                    hypothesis_id="topology_high_correlation_leader_288",
                    family="topology",
                    description="Long 288-period leader when average absolute correlation is high.",
                    signal_asset_rule="leader_asset_288",
                    conditions=[
                        condition("avg_abs_corr", ">", q["q75"]),
                    ],
                    hold_period=288,
                    rank_score=0.65,
                )
            )

    return hypotheses[:max_per_family]


def score_threshold(name: str) -> float:
    return {
        "q50": 0.5,
        "q75": 0.75,
        "q90": 0.9,
    }.get(name, 0.5)


def family_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        family = row.get("family", "unknown")
        counts[family] = counts.get(family, 0) + 1
    return counts
