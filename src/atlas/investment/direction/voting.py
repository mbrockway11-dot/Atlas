
"""Market direction voting."""

from __future__ import annotations

import pandas as pd


LONG_ACTIONS = {"BUY", "LONG", "ALLOCATE", "WATCH"}
SHORT_ACTIONS = {"SELL", "SHORT"}


def vote_direction(registry: pd.DataFrame) -> dict:
    """Vote market direction from registered strategy signals."""
    if registry.empty:
        return empty_vote()

    df = registry.copy()
    df["action"] = df["action"].fillna("NO_ACTION").astype(str).str.upper()
    df["direction"] = df["direction"].fillna("FLAT").astype(str).str.upper()
    df["confidence"] = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)
    df["target_exposure"] = pd.to_numeric(df["target_exposure"], errors="coerce").fillna(0.0)

    long_rows = df[
        (df["direction"] == "LONG")
        | (df["action"].isin(LONG_ACTIONS))
    ]

    short_rows = df[
        (df["direction"] == "SHORT")
        | (df["action"].isin(SHORT_ACTIONS))
    ]

    flat_rows = df[
        (df["direction"].isin(["FLAT", "NEUTRAL"]))
        | (df["action"].isin(["NO_ACTION", "WAIT"]))
    ]

    long_score = weighted_score(long_rows)
    short_score = weighted_score(short_rows)
    flat_score = max(0.0, len(flat_rows) * 0.05)

    total = long_score + short_score + flat_score

    if total <= 0:
        direction = "CASH"
        confidence = 0.0
    else:
        if long_score > short_score and long_score > flat_score:
            direction = "LONG"
            confidence = long_score / total
        elif short_score > long_score and short_score > flat_score:
            direction = "SHORT"
            confidence = short_score / total
        else:
            direction = "NEUTRAL"
            confidence = flat_score / total

    return {
        "success": True,
        "direction": direction,
        "confidence": round(float(confidence), 6),
        "long_score": round(float(long_score), 6),
        "short_score": round(float(short_score), 6),
        "flat_score": round(float(flat_score), 6),
        "total_score": round(float(total), 6),
        "long_count": int(len(long_rows)),
        "short_count": int(len(short_rows)),
        "flat_count": int(len(flat_rows)),
    }


def weighted_score(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0

    confidence = pd.to_numeric(df["confidence"], errors="coerce").fillna(0.0)
    exposure = pd.to_numeric(df["target_exposure"], errors="coerce").fillna(0.0)

    # Allocation rows carry exposure. Ranking rows carry confidence.
    exposure_score = exposure.sum()
    confidence_score = confidence.sum() * 0.50

    return float(exposure_score + confidence_score)


def empty_vote() -> dict:
    return {
        "success": False,
        "direction": "CASH",
        "confidence": 0.0,
        "long_score": 0.0,
        "short_score": 0.0,
        "flat_score": 0.0,
        "total_score": 0.0,
        "long_count": 0,
        "short_count": 0,
        "flat_count": 0,
    }
