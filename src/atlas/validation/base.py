"""Atlas validation-domain base contracts.

Validation domains compare the Canonical Structural Model against independent
observational domains.

They do not construct canonical structure.
They do not mutate AtlasProfile.
They produce agreement, conflict, unknown, confidence, and follow-up signals.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


VALIDATION_BASE_VERSION = "1.0"


@dataclass(frozen=True)
class Confidence:
    """Standard Atlas confidence record."""

    score: float
    percent: float
    label: str

    @classmethod
    def from_score(cls, score: float) -> "Confidence":
        """Build confidence from score."""
        score = clamp(score)

        return cls(
            score=round(score, 4),
            percent=round(score * 100, 2),
            label=confidence_label(score),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize confidence."""
        return asdict(self)


@dataclass(frozen=True)
class ValidationSignal:
    """One validation signal."""

    signal_type: str
    message: str
    source: str
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize signal."""
        return asdict(self)


@dataclass(frozen=True)
class ValidationResult:
    """Result returned by one validation domain."""

    domain: str
    domain_type: str
    version: str
    success: bool
    agreement_signals: list[ValidationSignal]
    conflict_signals: list[ValidationSignal]
    unknown_signals: list[ValidationSignal]
    confidence: Confidence
    agreement_score: Confidence
    warnings: list[str] = field(default_factory=list)
    errors: list[Any] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    recommended_followup: list[str] = field(default_factory=list)
    interpretation: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize validation result."""
        return {
            "domain": self.domain,
            "domain_type": self.domain_type,
            "version": self.version,
            "success": self.success,
            "agreement_signals": [
                signal.to_dict() for signal in self.agreement_signals
            ],
            "conflict_signals": [
                signal.to_dict() for signal in self.conflict_signals
            ],
            "unknown_signals": [
                signal.to_dict() for signal in self.unknown_signals
            ],
            "confidence": self.confidence.to_dict(),
            "agreement_score": self.agreement_score.to_dict(),
            "warnings": self.warnings,
            "errors": self.errors,
            "metrics": self.metrics,
            "recommended_followup": self.recommended_followup,
            "interpretation": self.interpretation,
        }


@dataclass(frozen=True)
class ValidationContext:
    """Context passed into validation domains."""

    profile_key: str
    canonical_summary: dict[str, Any]
    profile_payload: dict[str, Any] = field(default_factory=dict)
    graph_payload: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize context."""
        return asdict(self)


class ValidationDomain(Protocol):
    """Protocol for all Atlas validation domains."""

    name: str
    version: str
    domain_type: str

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate canonical structure against an independent domain."""


def build_agreement_score(
    *,
    agreement_signals: list[ValidationSignal],
    conflict_signals: list[ValidationSignal],
    unknown_signals: list[ValidationSignal],
    confidence: Confidence,
) -> Confidence:
    """Build deterministic agreement score."""
    agreement_weight = sum(signal.weight for signal in agreement_signals)
    conflict_weight = sum(signal.weight for signal in conflict_signals)
    unknown_weight = sum(signal.weight for signal in unknown_signals)

    total = agreement_weight + conflict_weight + unknown_weight

    if total <= 0:
        return Confidence.from_score(0.0)

    raw_agreement = agreement_weight / total

    score = clamp((raw_agreement * 0.70) + (confidence.score * 0.30))

    if conflict_weight > agreement_weight:
        score *= 0.75

    if unknown_weight > agreement_weight:
        score *= 0.85

    return Confidence.from_score(score)


def summarize_validation_results(
    results: list[ValidationResult],
) -> dict[str, Any]:
    """Build aggregate validation summary."""
    successful = [result for result in results if result.success]
    failed = [result for result in results if not result.success]

    agreement_count = sum(len(result.agreement_signals) for result in results)
    conflict_count = sum(len(result.conflict_signals) for result in results)
    unknown_count = sum(len(result.unknown_signals) for result in results)

    agreement_scores = [
        result.agreement_score.score
        for result in successful
    ]
    average_agreement = (
        sum(agreement_scores) / len(agreement_scores)
        if agreement_scores
        else 0.0
    )

    return {
        "domain_count": len(results),
        "successful_domains": len(successful),
        "failed_domains": len(failed),
        "agreement_signal_count": agreement_count,
        "conflict_signal_count": conflict_count,
        "unknown_signal_count": unknown_count,
        "average_agreement": Confidence.from_score(average_agreement).to_dict(),
        "validation_readiness": validation_readiness_label(
            agreement_count=agreement_count,
            conflict_count=conflict_count,
            unknown_count=unknown_count,
            average_agreement=average_agreement,
        ),
    }


def validation_readiness_label(
    *,
    agreement_count: int,
    conflict_count: int,
    unknown_count: int,
    average_agreement: float,
) -> str:
    """Resolve validation readiness label."""
    if conflict_count == 0 and unknown_count == 0 and average_agreement >= 0.75:
        return "strong_validation_candidate"

    if average_agreement >= 0.55 and conflict_count <= agreement_count:
        return "moderate_validation_candidate"

    if unknown_count > agreement_count or conflict_count > agreement_count:
        return "limited_validation_candidate"

    return "caution"


def confidence_label(score: float) -> str:
    """Resolve confidence label."""
    if score >= 0.80:
        return "high"

    if score >= 0.60:
        return "moderate"

    if score >= 0.40:
        return "limited"

    return "low"


def clamp(value: float) -> float:
    """Clamp a float to 0..1."""
    return max(0.0, min(1.0, value))


def json_export(data: Any) -> str:
    """Serialize validation data."""
    return json.dumps(data, indent=2, sort_keys=True)