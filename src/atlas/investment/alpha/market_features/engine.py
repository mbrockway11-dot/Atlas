
"""Market Feature Engine."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.market_features.breadth import build_breadth_features
from atlas.investment.alpha.market_features.leadership import build_leadership_features
from atlas.investment.alpha.market_features.loader import load_price_data, normalize_price_data
from atlas.investment.alpha.market_features.momentum import add_momentum_features
from atlas.investment.alpha.market_features.topology import build_topology_features
from atlas.investment.alpha.market_features.volatility import add_volatility_features


def build_market_feature_frame(root: str | Path) -> dict[str, Any]:
    """Build complete market feature frame."""
    raw = load_price_data(root)
    price = normalize_price_data(raw)

    if price.empty:
        return {
            "success": False,
            "error": "No usable price data found.",
            "root": str(root),
        }

    asset_features = add_momentum_features(price)
    asset_features = add_volatility_features(asset_features)

    breadth = build_breadth_features(asset_features)
    leadership = build_leadership_features(asset_features)
    topology = build_topology_features(asset_features)

    market = breadth.merge(leadership, on="date", how="outer")
    market = market.merge(topology, on="date", how="outer")
    market = market.sort_values("date").reset_index(drop=True)

    return {
        "success": True,
        "root": str(root),
        "asset_features": asset_features,
        "market_features": market,
        "breadth_features": breadth,
        "leadership_features": leadership,
        "topology_features": topology,
        "summary": (
            f"Market Feature Engine built {len(asset_features)} asset-feature row(s) "
            f"and {len(market)} market-feature row(s) across "
            f"{asset_features['asset'].nunique()} asset(s)."
        ),
    }
