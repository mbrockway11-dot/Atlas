"""Shared Alpha Engine Framework v1 utilities."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

from atlas.investment.alpha.backtester.schema import (
    normalize_market_frame,
)

from atlas.investment.alpha.engines.schema import (
    empty_signal_frame,
    normalize_signal_output,
)


@dataclass(frozen=True)
class EngineMetadata:
    """Immutable alpha-engine metadata."""

    engine_id: str
    version: str
    family: str
    holding_period: int
    description: str
    required_features: tuple[str, ...]


class AlphaEngine(ABC):
    """Base class for deterministic Atlas alpha engines."""

    metadata: EngineMetadata

    def run(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        """Normalize inputs, validate features, and build signals."""
        frame = normalize_market_frame(market)

        if frame.empty:
            return empty_signal_frame()

        missing = [
            column
            for column in self.metadata.required_features
            if column not in frame.columns
        ]

        if missing:
            return empty_signal_frame()

        signals = self.generate(frame)

        if signals is None or signals.empty:
            return empty_signal_frame()

        return normalize_signal_output(signals)

    @abstractmethod
    def generate(
        self,
        market: pd.DataFrame,
    ) -> pd.DataFrame:
        """Generate canonical signal rows."""


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    """Convert a value to a finite float."""
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(result):
        return default

    return result


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    """Clamp a value into a deterministic range."""
    return max(
        minimum,
        min(maximum, float(value)),
    )


def signed_score_to_unit(
    value: float,
    *,
    scale: float,
) -> float:
    """Map a signed feature value into the interval [0, 1]."""
    safe_scale = max(abs(float(scale)), 1e-12)

    return clamp(
        0.5 + finite(value) / safe_scale
    )


def score_to_direction(
    score: float,
    *,
    long_threshold: float = 0.60,
    short_threshold: float = 0.40,
) -> str:
    """Convert a normalized score to a position direction."""
    if score >= long_threshold:
        return "LONG"

    if score <= short_threshold:
        return "SHORT"

    return "NEUTRAL"


def score_to_signal(
    score: float,
    confidence: float,
) -> str:
    """Convert score and confidence into a direction-consistent signal."""
    if confidence < 0.35:
        return "INSUFFICIENT_EVIDENCE"

    if score >= 0.70:
        return "STRONG_LONG"

    if score >= 0.60:
        return "LONG"

    if score <= 0.30:
        return "STRONG_SHORT"

    if score <= 0.40:
        return "SHORT"

    return "NEUTRAL"


def feature_coverage(
    row: pd.Series,
    columns: tuple[str, ...],
) -> float:
    """Measure required-feature coverage for one row."""
    if not columns:
        return 1.0

    present = 0

    for column in columns:
        if column not in row.index:
            continue

        value = row.get(column)

        if value is not None and not pd.isna(value):
            present += 1

    return present / len(columns)


def canonical_row(
    *,
    timestamp,
    asset: str,
    metadata: EngineMetadata,
    raw_score: float,
    normalized_score: float,
    confidence: float,
    regime: str,
    reason_codes: list[str],
) -> dict:
    """Build one canonical engine signal row."""
    score = clamp(normalized_score)
    confidence = clamp(confidence)

    return {
        "timestamp": timestamp,
        "date": timestamp,
        "asset": str(asset),
        "engine_id": metadata.engine_id,
        "engine_version": metadata.version,
        "family": metadata.family,
        "direction": score_to_direction(score),
        "signal": score_to_signal(
            score,
            confidence,
        ),
        "raw_score": round(
            finite(raw_score),
            8,
        ),
        "normalized_score": round(
            score,
            8,
        ),
        "confidence": round(
            confidence,
            8,
        ),
        "conviction": round(
            score * confidence,
            8,
        ),
        "holding_period": metadata.holding_period,
        "regime": str(regime or "UNKNOWN"),
        "reason_codes": "|".join(reason_codes),
        "source": "alpha_engine_framework_v1",
    }

