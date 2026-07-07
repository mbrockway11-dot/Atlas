
"""Canonical Atlas market state."""

from __future__ import annotations

from typing import Any


def build_market_state(signal_payload: dict[str, Any]) -> dict[str, Any]:
    """Convert raw sigil-engine output into Atlas market state."""
    signal = signal_payload.get("signal", {}) or {}

    asset = first_present(signal, ["asset", "symbol", "leader_asset", "trade_asset"])
    action = normalize_action(first_present(signal, ["action", "signal_state", "decision", "side"]))
    direction = normalize_direction(first_present(signal, ["direction", "side", "trade_direction"]))
    confidence = parse_float(first_present(signal, ["confidence", "score", "signal_score", "edge_score"]), default=0.0)
    entry_ready = parse_bool(first_present(signal, ["entry_ready", "setup_active", "valid_signal", "trade_ready"]))

    return {
        "success": bool(signal_payload.get("success")),
        "source": "sigil_engine",
        "source_path": signal_payload.get("path", signal.get("_source_path", "")),
        "asset": asset or "UNKNOWN",
        "action": action,
        "direction": direction,
        "confidence": confidence,
        "entry_ready": entry_ready,
        "raw_signal": signal,
        "market_state_label": classify_market_state(action, direction, confidence, entry_ready),
    }


def first_present(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = row.get(key)
        if value not in (None, ""):
            return value
    return ""


def normalize_action(value: Any) -> str:
    text = str(value or "").upper()

    if "NO" in text and "TRADE" in text:
        return "NO_TRADE"
    if "WATCH" in text:
        return "WATCH"
    if "LONG" in text or "BUY" in text:
        return "LONG"
    if "SHORT" in text or "SELL" in text:
        return "SHORT"
    if "EXIT" in text:
        return "EXIT"

    return text or "UNKNOWN"


def normalize_direction(value: Any) -> str:
    text = str(value or "").upper()

    if "LONG" in text or "BUY" in text:
        return "LONG"
    if "SHORT" in text or "SELL" in text:
        return "SHORT"
    if "FLAT" in text:
        return "FLAT"

    return text or "UNKNOWN"


def classify_market_state(action: str, direction: str, confidence: float, entry_ready: bool) -> str:
    if not entry_ready:
        return "inactive_market_state"
    if action in {"LONG", "SHORT"} and confidence >= 0.70:
        return "actionable_research_state"
    if action in {"LONG", "SHORT", "WATCH"}:
        return "watch_state"
    return "neutral_market_state"


def parse_float(value: Any, *, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def parse_bool(value: Any) -> bool:
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "ready", "active"}
