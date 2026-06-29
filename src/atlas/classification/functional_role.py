"""Functional role classification.

This module classifies a topology signature into primary / secondary
functional roles instead of forcing every profile into one dominant label.
"""

from dataclasses import dataclass
from typing import Any


ROLE_MARGIN_STRONG = 0.20
ROLE_MARGIN_MODERATE = 0.10
ROLE_MARGIN_WEAK = 0.05


@dataclass(frozen=True)
class FunctionalRole:
    """Functional role classification."""

    role: str
    reason: str
    driver: float
    amplifier: float
    regulator: float
    primary_role: str
    secondary_role: str
    subtype: str
    confidence: str
    margin: float
    is_hybrid: bool


def classify_functional_role(signature: Any) -> FunctionalRole:
    """Classify signature as Driver, Amplifier, Regulator, Hybrid, or Ambiguous."""
    scores = {
        "Driver": float(signature.driver),
        "Amplifier": float(signature.amplifier),
        "Regulator": float(signature.regulator),
    }

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    primary_role, primary_score = ranked[0]
    secondary_role, secondary_score = ranked[1]

    margin = primary_score - secondary_score
    confidence = classify_confidence(margin)

    if margin < ROLE_MARGIN_WEAK:
        role = "Hybrid"
        subtype = f"{primary_role}-{secondary_role}"
        is_hybrid = True
        reason = (
            f"{primary_role} and {secondary_role} are nearly tied "
            f"(margin {margin:.4f}), so this is classified as a hybrid."
        )

    else:
        role = primary_role
        subtype = f"{primary_role}-{secondary_role}"
        is_hybrid = confidence in {"weak", "moderate"}
        reason = (
            f"{primary_role} is the highest functional role with "
            f"{secondary_role} as secondary modifier "
            f"(margin {margin:.4f}, confidence {confidence})."
        )

    return FunctionalRole(
        role=role,
        reason=reason,
        driver=scores["Driver"],
        amplifier=scores["Amplifier"],
        regulator=scores["Regulator"],
        primary_role=primary_role,
        secondary_role=secondary_role,
        subtype=subtype,
        confidence=confidence,
        margin=margin,
        is_hybrid=is_hybrid,
    )


def classify_confidence(margin: float) -> str:
    """Classify confidence from top-two score margin."""
    if margin >= ROLE_MARGIN_STRONG:
        return "strong"

    if margin >= ROLE_MARGIN_MODERATE:
        return "moderate"

    if margin >= ROLE_MARGIN_WEAK:
        return "weak"

    return "ambiguous"


def functional_role_to_dict(role: FunctionalRole) -> dict[str, Any]:
    """Convert functional role classification to dictionary."""
    return {
        "role": role.role,
        "reason": role.reason,
        "driver": role.driver,
        "amplifier": role.amplifier,
        "regulator": role.regulator,
        "primary_role": role.primary_role,
        "secondary_role": role.secondary_role,
        "subtype": role.subtype,
        "confidence": role.confidence,
        "margin": role.margin,
        "is_hybrid": role.is_hybrid,
    } 