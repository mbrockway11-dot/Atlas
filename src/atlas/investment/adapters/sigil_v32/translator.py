
"""Translate Sigil V32 outputs into Atlas strategy signals."""

from __future__ import annotations

import pandas as pd

from atlas.investment.adapters.sigil_v32.schema import StrategySignal


def row_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"true", "1", "yes", "y"}


def row_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def translate_engine_states(df: pd.DataFrame) -> list[StrategySignal]:
    if df.empty:
        return []

    signals: list[StrategySignal] = []

    for _, row in df.iterrows():
        signals.append(
            StrategySignal(
                source="sigil_v32",
                engine=str(row.get("engine_name", "unknown")),
                asset=row.get("asset"),
                timestamp=str(row.get("timestamp")) if row.get("timestamp") is not None else None,
                signal_state=row.get("signal_state"),
                action=row.get("action"),
                direction=row.get("direction"),
                target_exposure=row_float(row.get("target_exposure"), 0.0),
                entry_ready=row_bool(row.get("entry_ready")),
                setup_active=row_bool(row.get("setup_active")),
                notes=row.get("notes"),
            )
        )

    return signals
