"""Vedic validation domain.

Evaluates whether Vedic Behavior output provides agreement, conflict, or unknown
signals relative to the Canonical Structural Model.

This module does not construct canonical structure.
It wraps the existing Vedic Behavior service behind the validation-domain
framework contract.
"""

from __future__ import annotations

from typing import Any

from atlas.services.vedic_behavior_service import build_vedic_behavior_payload
from atlas.validation.base import (
    Confidence,
    ValidationContext,
    ValidationResult,
    ValidationSignal,
    build_agreement_score,
)


VEDIC_VALIDATION_DOMAIN_VERSION = "1.0"


class VedicValidationDomain:
    """Vedic Behavior validation-domain adapter."""

    name = "vedic_behavior"
    version = VEDIC_VALIDATION_DOMAIN_VERSION
    domain_type = "validation_domain"

    def validate(self, context: ValidationContext) -> ValidationResult:
        """Validate canonical structure against Vedic Behavior output."""
        payload = safe_call(
            "vedic_behavior",
            lambda: build_vedic_behavior_payload(context.profile_key),
        )
        metrics = payload.get("metrics", {})
        confidence = confidence_from_metrics(metrics)

        agreement_signals = build_agreement_signals(payload, metrics)
        conflict_signals = build_conflict_signals(payload, metrics)
        unknown_signals = build_unknown_signals(payload, metrics)

        agreement_score = build_agreement_score(
            agreement_signals=agreement_signals,
            conflict_signals=conflict_signals,
            unknown_signals=unknown_signals,
            confidence=confidence,
        )

        return ValidationResult(
            domain=self.name,
            domain_type=self.domain_type,
            version=self.version,
            success=payload.get("success", False),
            agreement_signals=agreement_signals,
            conflict_signals=conflict_signals,
            unknown_signals=unknown_signals,
            confidence=confidence,
            agreement_score=agreement_score,
            warnings=[str(item) for item in payload.get("warnings", [])],
            errors=payload.get("errors", []),
            metrics=metrics,
            recommended_followup=build_followup(
                agreement_signals=agreement_signals,
                conflict_signals=conflict_signals,
                unknown_signals=unknown_signals,
            ),
            interpretation=build_interpretation(
                agreement_count=len(agreement_signals),
                conflict_count=len(conflict_signals),
                unknown_count=len(unknown_signals),
                confidence=confidence,
            ),
        )


def build_agreement_signals(
    payload: dict[str, Any],
    metrics: dict[str, Any],
) -> list[ValidationSignal]:
    """Build agreement signals from Vedic metrics."""
    signals: list[ValidationSignal] = []

    if payload.get("success"):
        signals.append(
            ValidationSignal(
                signal_type="agreement",
                message="Vedic Behavior produced a bounded validation-domain payload.",
                source="vedic_behavior",
                weight=1.0,
            )
        )

    assumption_count = safe_int(metrics.get("assumption_count"))
    if assumption_count > 0:
        signals.append(
            ValidationSignal(
                signal_type="agreement",
                message=(
                    f"Vedic Behavior produced {assumption_count} behavioral "
                    "assumption(s)."
                ),
                source="vedic_behavior",
                weight=1.0,
                metadata={"assumption_count": assumption_count},
            )
        )

    planet_count = safe_int(metrics.get("planet_count"))
    if planet_count > 0:
        signals.append(
            ValidationSignal(
                signal_type="agreement",
                message=f"Vedic layer resolved {planet_count} planetary record(s).",
                source="vedic_behavior",
                weight=0.8,
                metadata={"planet_count": planet_count},
            )
        )

    dasha_periods = safe_int(metrics.get("dasha_periods"))
    if dasha_periods > 0:
        signals.append(
            ValidationSignal(
                signal_type="agreement",
                message=f"Vimshottari dasha periods available: {dasha_periods}.",
                source="vedic_behavior",
                weight=0.8,
                metadata={"dasha_periods": dasha_periods},
            )
        )

    transit_contacts = safe_int(metrics.get("transit_contacts"))
    if transit_contacts > 0:
        signals.append(
            ValidationSignal(
                signal_type="agreement",
                message=f"Transit contacts available: {transit_contacts}.",
                source="vedic_behavior",
                weight=0.6,
                metadata={"transit_contacts": transit_contacts},
            )
        )

    return signals


def build_conflict_signals(
    payload: dict[str, Any],
    metrics: dict[str, Any],
) -> list[ValidationSignal]:
    """Build conflict signals from Vedic metrics."""
    signals: list[ValidationSignal] = []

    if not payload.get("success"):
        signals.append(
            ValidationSignal(
                signal_type="conflict",
                message="Vedic Behavior service failed.",
                source="vedic_behavior",
                weight=1.0,
            )
        )

    if not metrics.get("moon_nakshatra"):
        signals.append(
            ValidationSignal(
                signal_type="conflict",
                message="Moon nakshatra is unresolved, limiting Vedic validation precision.",
                source="vedic_behavior",
                weight=1.0,
            )
        )

    confidence = metrics.get("overall_confidence", {})
    if isinstance(confidence, dict) and confidence.get("label") in {"limited", "low"}:
        signals.append(
            ValidationSignal(
                signal_type="conflict",
                message=(
                    "Vedic Behavior confidence is limited or low and should remain "
                    "hypothesis-level."
                ),
                source="vedic_behavior",
                weight=0.8,
                metadata={"confidence": confidence},
            )
        )

    warning_count = safe_int(metrics.get("warning_count"))
    if warning_count > 0:
        signals.append(
            ValidationSignal(
                signal_type="conflict",
                message=f"Vedic Behavior reported {warning_count} warning(s).",
                source="vedic_behavior",
                weight=min(1.0, warning_count * 0.25),
                metadata={"warning_count": warning_count},
            )
        )

    return signals


def build_unknown_signals(
    payload: dict[str, Any],
    metrics: dict[str, Any],
) -> list[ValidationSignal]:
    """Build unknown signals from Vedic metrics."""
    signals: list[ValidationSignal] = []

    if safe_int(metrics.get("assumption_count")) <= 0:
        signals.append(
            ValidationSignal(
                signal_type="unknown",
                message="No Vedic behavioral assumptions were produced.",
                source="vedic_behavior",
                weight=1.0,
            )
        )

    if safe_int(metrics.get("planet_count")) <= 0:
        signals.append(
            ValidationSignal(
                signal_type="unknown",
                message="Planetary records were unavailable or unresolved.",
                source="vedic_behavior",
                weight=1.0,
            )
        )

    if safe_int(metrics.get("dasha_periods")) <= 0:
        signals.append(
            ValidationSignal(
                signal_type="unknown",
                message="Dasha periods were unavailable.",
                source="vedic_behavior",
                weight=0.8,
            )
        )

    return signals


def confidence_from_metrics(metrics: dict[str, Any]) -> Confidence:
    """Extract confidence from Vedic metrics."""
    confidence = metrics.get("overall_confidence", {})

    if isinstance(confidence, dict) and "score" in confidence:
        return Confidence.from_score(safe_float(confidence.get("score")))

    return Confidence.from_score(0.0)


def build_followup(
    *,
    agreement_signals: list[ValidationSignal],
    conflict_signals: list[ValidationSignal],
    unknown_signals: list[ValidationSignal],
) -> list[str]:
    """Build follow-up recommendations."""
    followup: list[str] = []

    conflict_text = " ".join(signal.message for signal in conflict_signals)
    unknown_text = " ".join(signal.message for signal in unknown_signals)

    if "Moon nakshatra is unresolved" in conflict_text:
        followup.append("Resolve Moon nakshatra and rerun Vedic validation.")

    if "confidence is limited or low" in conflict_text:
        followup.append(
            "Treat Vedic Behavior as hypothesis-level until temporal inputs improve."
        )

    if unknown_text:
        followup.append("Repair unresolved Vedic or temporal inputs before strong validation claims.")

    if agreement_signals:
        followup.append("Compare Vedic agreement signals against canonical graph intelligence.")

    if not followup:
        followup.append("Inspect Vedic validation output and determine next repair action.")

    return dedupe(followup)


def build_interpretation(
    *,
    agreement_count: int,
    conflict_count: int,
    unknown_count: int,
    confidence: Confidence,
) -> str:
    """Build interpretation text."""
    if agreement_count > conflict_count and agreement_count > unknown_count:
        return (
            "Vedic Behavior provides more agreement signals than conflict or unknown "
            f"signals, bounded by {confidence.label} domain confidence."
        )

    if conflict_count >= agreement_count and conflict_count > 0:
        return (
            "Vedic Behavior currently produces meaningful conflict or limitation "
            "signals and should be treated as a research target rather than confirmation."
        )

    if unknown_count > 0:
        return (
            "Vedic Behavior contains unresolved information. Validation should remain "
            "conservative until missing inputs are repaired."
        )

    return "Vedic Behavior did not produce enough information for validation."


def safe_call(name: str, fn) -> dict[str, Any]:
    """Safely execute service call."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "version": VEDIC_VALIDATION_DOMAIN_VERSION,
            "errors": [f"{name} failed: {exc}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def safe_int(value: Any) -> int:
    """Convert value to int safely."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def dedupe(values: list[str]) -> list[str]:
    """Dedupe while preserving order."""
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)

    return result


__all__ = ["VedicValidationDomain"]