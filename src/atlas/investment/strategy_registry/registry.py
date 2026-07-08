
"""Strategy Registry builder."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.strategy_registry.loaders import (
    load_alpha_portfolio,
    load_cross_sectional_latest,
    load_sigil_v32_signals,
)
from atlas.investment.strategy_registry.normalizers import (
    normalize_alpha_portfolio,
    normalize_cross_sectional_ranker,
    normalize_sigil_v32,
)


def build_strategy_registry() -> dict[str, Any]:
    sigil = normalize_sigil_v32(load_sigil_v32_signals())
    portfolio = normalize_alpha_portfolio(load_alpha_portfolio())
    ranker = normalize_cross_sectional_ranker(load_cross_sectional_latest())

    signals = sigil + portfolio + ranker
    rows = [s.to_dict() for s in signals]

    df = pd.DataFrame(rows)

    summary = {
        "signal_count": int(len(df)),
        "source_counts": df["source"].value_counts().to_dict() if not df.empty else {},
        "family_counts": df["strategy_family"].value_counts().to_dict() if not df.empty else {},
        "action_counts": df["action"].value_counts().to_dict() if not df.empty else {},
        "asset_counts": df["asset"].value_counts().to_dict() if not df.empty and "asset" in df else {},
    }

    return {
        "success": True,
        "signals": rows,
        "summary": summary,
        "text_summary": (
            f"Strategy Registry collected {summary['signal_count']} signal row(s) "
            f"from {len(summary['source_counts'])} source(s)."
        ),
    }
