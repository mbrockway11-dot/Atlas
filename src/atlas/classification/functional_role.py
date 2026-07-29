"""Functional role classification (population-relative).

Driver / amplifier / regulator are produced by different formulas on
non-overlapping scales, so a raw ``argmax`` over them is a constant (Regulator
for every profile). This classifier instead z-scores each score against the
corpus (see ``score_calibration``) and ranks those, so the role answers "which
drive is elevated **for this person, relative to the population**" -- which
actually varies. The role is therefore relative to the calibration corpus, which
``basis`` records; callers should present it as such, not as an absolute trait.
"""

from dataclasses import dataclass
from typing import Any

from atlas.classification.score_calibration import (
    CALIBRATION_BASIS,
    DEFAULT_SCORE_CALIBRATION,
    ScoreCalibration,
)


# Margins are now in standard-deviation units of the population, not raw score
# points: how many sd separate the top relative drive from the second.
ROLE_MARGIN_STRONG = 1.00
ROLE_MARGIN_MODERATE = 0.50
ROLE_MARGIN_WEAK = 0.25


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
    driver_z: float = 0.0
    amplifier_z: float = 0.0
    regulator_z: float = 0.0
    basis: str = CALIBRATION_BASIS


def classify_functional_role(
    signature: Any,
    calibration: ScoreCalibration = DEFAULT_SCORE_CALIBRATION,
) -> FunctionalRole:
    """Classify signature as Driver, Amplifier, Regulator, Hybrid, or Ambiguous.

    Roles are decided on population-relative z-scores, so no single role is
    structurally guaranteed to win. ``calibration`` supplies the corpus the
    scores are measured against; pass a different one to classify relative to a
    different population.
    """
    raw = {
        "Driver": float(signature.driver),
        "Amplifier": float(signature.amplifier),
        "Regulator": float(signature.regulator),
    }
    zscores = {
        "Driver": calibration.z("driver", raw["Driver"]),
        "Amplifier": calibration.z("amplifier", raw["Amplifier"]),
        "Regulator": calibration.z("regulator", raw["Regulator"]),
    }

    ranked = sorted(zscores.items(), key=lambda item: item[1], reverse=True)
    primary_role, primary_z = ranked[0]
    secondary_role, secondary_z = ranked[1]

    margin = primary_z - secondary_z
    confidence = classify_confidence(margin)

    if margin < ROLE_MARGIN_WEAK:
        role = "Hybrid"
        subtype = f"{primary_role}-{secondary_role}"
        is_hybrid = True
        reason = (
            f"{primary_role} and {secondary_role} are nearly tied relative to "
            f"the corpus (margin {margin:.2f} sd), so this is a hybrid."
        )
    else:
        role = primary_role
        subtype = f"{primary_role}-{secondary_role}"
        is_hybrid = confidence in {"weak", "moderate"}
        reason = (
            f"{primary_role} is the most elevated drive relative to the corpus "
            f"({secondary_role} secondary; margin {margin:.2f} sd, "
            f"confidence {confidence})."
        )

    return FunctionalRole(
        role=role,
        reason=reason,
        driver=raw["Driver"],
        amplifier=raw["Amplifier"],
        regulator=raw["Regulator"],
        primary_role=primary_role,
        secondary_role=secondary_role,
        subtype=subtype,
        confidence=confidence,
        margin=margin,
        is_hybrid=is_hybrid,
        driver_z=zscores["Driver"],
        amplifier_z=zscores["Amplifier"],
        regulator_z=zscores["Regulator"],
        basis=CALIBRATION_BASIS,
    )


def classify_confidence(margin: float) -> str:
    """Classify confidence from the top-two z-score margin (in sd units)."""
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
        "driver_z": role.driver_z,
        "amplifier_z": role.amplifier_z,
        "regulator_z": role.regulator_z,
        "primary_role": role.primary_role,
        "secondary_role": role.secondary_role,
        "subtype": role.subtype,
        "confidence": role.confidence,
        "margin": role.margin,
        "is_hybrid": role.is_hybrid,
        "basis": role.basis,
    }
