
"""Market direction exposure controller."""

from __future__ import annotations


def target_market_exposure(direction: str, confidence: float) -> dict:
    """Convert market direction and confidence into target gross exposure."""
    d = str(direction).upper()
    c = max(0.0, min(float(confidence or 0.0), 1.0))

    if d == "LONG":
        if c >= 0.80:
            exposure = 0.80
        elif c >= 0.65:
            exposure = 0.60
        elif c >= 0.50:
            exposure = 0.40
        else:
            exposure = 0.20
    elif d == "SHORT":
        if c >= 0.80:
            exposure = -0.50
        elif c >= 0.65:
            exposure = -0.35
        elif c >= 0.50:
            exposure = -0.20
        else:
            exposure = 0.0
    elif d == "NEUTRAL":
        exposure = 0.20
    else:
        exposure = 0.0

    return {
        "market_direction": d,
        "direction_confidence": round(c, 6),
        "target_net_exposure": round(float(exposure), 6),
        "target_cash_weight": round(float(max(0.0, 1.0 - abs(exposure))), 6),
        "exposure_label": exposure_label(exposure),
    }


def exposure_label(exposure: float) -> str:
    if exposure >= 0.75:
        return "aggressive_long"
    if exposure >= 0.40:
        return "moderate_long"
    if exposure > 0:
        return "light_long"
    if exposure <= -0.40:
        return "aggressive_short"
    if exposure < 0:
        return "light_short"
    return "cash"
