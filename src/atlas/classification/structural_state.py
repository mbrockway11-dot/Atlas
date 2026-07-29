"""Structural state classification (distribution-calibrated).

The original cascade tested absolute thresholds -- ``symmetry >= 0.60``,
``edge_density >= 0.70``, ``driver >= 0.65``, ``regulator < 0.35`` -- that the
corpus never reaches (symmetry tops out ~0.47, edge_density ~0.08, driver ~0.13,
regulator floors ~0.62), so every branch failed and ``Adaptive`` was a forced
constant. The only metrics that actually vary are regulator and symmetry, so the
states are now decided on those two, **z-scored against the corpus** -- a state
describes where a profile sits in the population, not against an unreachable
absolute. Like the functional role, the label is relative to the calibration
corpus (``basis``).
"""

from dataclasses import dataclass

from atlas.classification.score_calibration import (
    CALIBRATION_BASIS,
    DEFAULT_SCORE_CALIBRATION,
    ScoreCalibration,
)
from atlas.signatures.topology_signature import TopologySignature


# "High" / "low" relative to the corpus, in standard-deviation units.
STATE_HIGH = 0.5
STATE_LOW = -0.5


@dataclass(frozen=True)
class StructuralState:
    """Condition of the graph structure."""

    state: str
    reason: str
    basis: str = CALIBRATION_BASIS


def classify_structural_state(
    signature: TopologySignature,
    calibration: ScoreCalibration = DEFAULT_SCORE_CALIBRATION,
) -> StructuralState:
    """Classify the graph's structural state relative to the corpus."""
    if signature.component_count > 2:
        return StructuralState(
            state="Fragmented",
            reason="More than two connected components indicate graph fragmentation.",
        )

    regulator_z = calibration.z("regulator", signature.regulator)
    symmetry_z = calibration.z("symmetry", signature.symmetry)
    driver_z = calibration.z("driver", signature.driver)
    amplifier_z = calibration.z("amplifier", signature.amplifier)

    if regulator_z >= STATE_HIGH and symmetry_z >= STATE_HIGH:
        return StructuralState(
            state="Stable",
            reason="Regulation and symmetry both high for the corpus -- structural balance.",
        )

    if regulator_z <= STATE_LOW and symmetry_z <= STATE_LOW:
        return StructuralState(
            state="Fragile",
            reason="Regulation and symmetry both low for the corpus -- perturbation-sensitive.",
        )

    if driver_z >= STATE_HIGH and regulator_z <= STATE_LOW:
        return StructuralState(
            state="Transitional",
            reason="Drive elevated over regulation for the corpus -- active reorganization.",
        )

    if amplifier_z >= STATE_HIGH and regulator_z <= STATE_LOW:
        return StructuralState(
            state="Emergent",
            reason="Amplification elevated over regulation for the corpus -- new structure forming.",
        )

    return StructuralState(
        state="Adaptive",
        reason="Regulation and symmetry near the corpus centre -- partial regulation with room to change.",
    )
