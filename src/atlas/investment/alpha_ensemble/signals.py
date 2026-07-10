
"""Alpha Ensemble v4 signal extraction."""

from __future__ import annotations

import pandas as pd


DEFAULT_ASSETS = ["BTC-USD", "ETH-USD", "SOL-USD"]


def extract_candidate_signals(inputs: dict) -> list[dict]:
    signals = []

    signals.extend(strategy_registry_signals(inputs.get("strategy_registry")))
    signals.extend(backtest_signals(inputs.get("backtests")))
    signals.extend(sigil_signals(inputs.get("sigil_adapter", {}) or {}))
    signals.extend(market_direction_signals(inputs.get("market_direction", {}) or {}))

    if not signals:
        signals = fallback_signals()

    return signals


def strategy_registry_signals(registry: pd.DataFrame) -> list[dict]:
    if registry is None or registry.empty or "asset" not in registry.columns:
        return []

    rows = []

    for _, row in registry.iterrows():
        asset = str(row.get("asset"))
        conf = float(row.get("asset_confidence") or 0.5)
        status = str(row.get("status") or "MAINTAIN")

        direction = "LONG" if status in {"PROMOTE", "MAINTAIN"} else "REDUCE"

        rows.append({
            "asset": asset,
            "signal_source": "strategy_registry_v3",
            "direction": direction,
            "raw_score": conf,
            "confidence": conf,
            "status": status,
        })

    return rows


def backtest_signals(backtests: pd.DataFrame) -> list[dict]:
    if backtests is None or backtests.empty:
        return []

    asset_col = "asset" if "asset" in backtests.columns else None
    if not asset_col:
        return []

    rows = []

    for _, row in backtests.iterrows():
        asset = str(row.get(asset_col))
        win_rate = float(row.get("win_rate") or row.get("accuracy") or 0.5)
        expectancy = float(row.get("expectancy") or row.get("avg_return") or 0.0)

        score = min(1.0, max(0.0, 0.50 + (win_rate - 0.50) + expectancy))

        rows.append({
            "asset": asset,
            "signal_source": "alpha_backtests",
            "direction": "LONG" if score >= 0.5 else "REDUCE",
            "raw_score": score,
            "confidence": score,
            "status": "BACKTESTED",
        })

    return rows


def sigil_signals(sigil: dict) -> list[dict]:
    rows = []

    candidates = sigil.get("signals") or sigil.get("rows") or []

    if isinstance(candidates, list):
        for row in candidates:
            if not isinstance(row, dict):
                continue

            asset = row.get("asset")
            if not asset:
                continue

            conf = float(row.get("confidence") or row.get("score") or 0.5)
            direction = str(row.get("direction") or "LONG")

            rows.append({
                "asset": asset,
                "signal_source": "sigil_v32_adapter",
                "direction": direction,
                "raw_score": conf,
                "confidence": conf,
                "status": "SIGIL_SIGNAL",
            })

    return rows


def market_direction_signals(market_direction: dict) -> list[dict]:
    direction = str(
        market_direction.get("direction")
        or market_direction.get("market_direction")
        or market_direction.get("regime")
        or ""
    ).upper()

    if not direction:
        return []

    if "BEAR" in direction or "RISK_OFF" in direction:
        score = 0.35
    elif "BULL" in direction or "RISK_ON" in direction:
        score = 0.65
    else:
        score = 0.50

    return [
        {
            "asset": asset,
            "signal_source": "market_direction",
            "direction": "LONG" if score >= 0.5 else "REDUCE",
            "raw_score": score,
            "confidence": score,
            "status": direction,
        }
        for asset in DEFAULT_ASSETS
    ]


def fallback_signals() -> list[dict]:
    return [
        {
            "asset": "BTC-USD",
            "signal_source": "fallback",
            "direction": "LONG",
            "raw_score": 0.55,
            "confidence": 0.55,
            "status": "FALLBACK",
        },
        {
            "asset": "ETH-USD",
            "signal_source": "fallback",
            "direction": "LONG",
            "raw_score": 0.55,
            "confidence": 0.55,
            "status": "FALLBACK",
        },
        {
            "asset": "SOL-USD",
            "signal_source": "fallback",
            "direction": "HOLD",
            "raw_score": 0.50,
            "confidence": 0.50,
            "status": "FALLBACK",
        },
    ]
