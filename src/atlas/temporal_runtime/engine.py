"""Temporal Runtime Engine for Atlas.

The compiler builds the Canonical Structural Signature.
The runtime evaluates compiled temporal structure over time.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.temporal_runtime.scoring import score_transit_activation


@dataclass(frozen=True)
class TemporalRuntimeResult:
    """Result of one temporal runtime evaluation."""

    profile_key: str
    evaluation_date: str
    success: bool
    activation: dict[str, Any]
    scoring: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return a serializable runtime payload."""

        return {
            "profile_key": self.profile_key,
            "evaluation_date": self.evaluation_date,
            "success": self.success,
            "activation": self.activation,
            "scoring": self.scoring,
            "metadata": self.metadata,
        }


class TemporalRuntimeEngine:
    """Evaluate compiled CSS temporal structures."""

    def evaluate(
        self,
        *,
        profile_key: str,
        css: dict[str, Any],
        evaluation_date: str,
    ) -> TemporalRuntimeResult:
        """Evaluate one compiled CSS payload for a specific date."""
        temporal = css.get("temporal", {})
        natal = temporal.get("natal", {})
        ephemeris = natal.get("ephemeris", {})
        transits = ephemeris.get("transits", {})
        transit_summary = transits.get("summary", {})

        activation = {
            "has_temporal": bool(temporal),
            "has_natal": bool(natal),
            "has_ephemeris": bool(ephemeris),
            "has_transits": bool(transits),
            "transit_summary": transit_summary,
        }

        scoring = score_transit_activation(
            transit_summary
        )

        return TemporalRuntimeResult(
            profile_key=profile_key,
            evaluation_date=evaluation_date,
            success=True,
            activation=activation,
            scoring=scoring,
            metadata={
                "runtime_version": "0.1",
                "runtime": "atlas.temporal_runtime",
            },
        )