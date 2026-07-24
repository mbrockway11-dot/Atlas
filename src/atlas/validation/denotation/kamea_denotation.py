"""What Kamea denotes, frozen -- structural axis only.

Step 2 of the 1E order: freeze the precise information Kamea supplies. 1D
established exactly what that is, and exactly what it is not.

Kamea supplies three structural facts about a trajectory:

    quantized trajectory          which cells, in order
    repeated-visit structure      how much it dwells and returns
    translation-normalized shape  the figure, position discarded

These map onto the ontology's **dynamic** axis -- repetition, stabilization,
disruption, and so on -- and nowhere else. The restriction is not caution, it
is the 1D finding: the square's only geometric operation is a subtractive
coarsening, and the planet contributed the square, not a meaning. So Kamea may
not be read as "Saturnian restraint"; it may be read as "high repetition, low
transition", which is a structural claim a longitude-bin sequence could not
make on its own only because it lacks the dedup and shape steps.

Every mapping here is ``direct``: it is computed from the path's measured
properties by a fixed rule, with no interpretive symbolism. That is what lets
Kamea enter the audit honestly while the symbolic systems still await their
frozen dictionaries.
"""

from __future__ import annotations

from typing import Any

from atlas.validation.denotation.expressions import (
    DenotationClaim,
    SystemExpression,
)
from atlas.validation.temporal_kamea import TemporalKameaPath


KAMEA_DENOTATION_VERSION = "1.0.0"

# Structural thresholds, fixed before any subject. Expressed as fractions of
# the path length so they are scale- and body-independent.
HIGH_REPETITION = 0.5      # at least half the samples revisit a cell
LOW_TRANSITION = 0.25      # at most a quarter of steps change cell
HIGH_TRANSITION = 0.75     # at least three quarters change cell


def kamea_expression(trajectory: TemporalKameaPath) -> SystemExpression:
    """Freeze one Kamea trajectory as a system expression.

    The expression carries the measured structural quantities, not an
    interpretation of them. Reference class is ``transit`` because a
    trajectory is an instant's neighbourhood, not an enduring trait.
    """
    diagnostics = trajectory.diagnostics()

    return SystemExpression(
        system="kamea",
        subject_id=trajectory.instants[len(trajectory.instants) // 2]
        .isoformat(),
        content={
            "kamea_key": trajectory.kamea_key,
            "distinct_cells": diagnostics["distinct_cells"],
            "transition_count": diagnostics["transition_count"],
            "longest_stationary_run": diagnostics["longest_stationary_run"],
            "reversal_count": diagnostics["reversal_count"],
            "samples": len(trajectory.coordinates),
            "stationary": diagnostics["stationary"],
        },
        reference_class="transit",
    )


def kamea_dynamic_claims(
    expression: SystemExpression,
) -> list[DenotationClaim]:
    """Translate a Kamea expression onto the dynamic axis.

    Fixed rules over measured quantities. A path that dwells denotes
    repetition or stabilization; one that moves and reverses denotes
    disruption or reversal. Polarity is neutral throughout: structure carries
    no valence on its own, and asserting one would be the interpretive step
    this layer exists to avoid.
    """
    content = expression.content
    samples = max(int(content["samples"]), 1)
    steps = max(samples - 1, 1)

    revisit_fraction = 1.0 - content["distinct_cells"] / samples
    transition_fraction = content["transition_count"] / steps
    reversal_fraction = content["reversal_count"] / steps

    claims: list[DenotationClaim] = []

    def add(value: str, confidence: float, basis: str) -> None:
        claims.append(
            DenotationClaim(
                system="kamea",
                subject_id=expression.subject_id,
                axis="dynamic",
                value=value,
                polarity="neutral",
                temporal_scope="transit",
                mapping_kind="direct",
                confidence=confidence,
                source_basis=basis,
            )
        )

    if revisit_fraction >= HIGH_REPETITION:
        add(
            "repetition",
            round(revisit_fraction, 3),
            f"revisit_fraction {revisit_fraction:.2f} >= {HIGH_REPETITION}",
        )

    if transition_fraction <= LOW_TRANSITION:
        add(
            "stabilization",
            round(1.0 - transition_fraction, 3),
            f"transition_fraction {transition_fraction:.2f} <= "
            f"{LOW_TRANSITION}",
        )
    elif transition_fraction >= HIGH_TRANSITION:
        add(
            "disruption",
            round(transition_fraction, 3),
            f"transition_fraction {transition_fraction:.2f} >= "
            f"{HIGH_TRANSITION}",
        )

    if reversal_fraction >= LOW_TRANSITION:
        add(
            "reversal",
            round(reversal_fraction, 3),
            f"reversal_fraction {reversal_fraction:.2f} >= {LOW_TRANSITION}",
        )

    return claims


def kamea_denotation_manifest() -> dict[str, Any]:
    """Return the frozen contribution Kamea makes, for the record."""
    return {
        "version": KAMEA_DENOTATION_VERSION,
        "axis": "dynamic",
        "polarity": "neutral (structure carries no valence)",
        "mapping_kind": "direct",
        "supplies": [
            "quantized trajectory",
            "repeated-visit structure",
            "translation-normalized shape",
        ],
        "excludes": (
            "symbolic domains. 1D showed the square's only geometric "
            "operation is a subtractive coarsening, so the planet supplied "
            "the square, not a meaning. Kamea denotes structure, never "
            "'Saturnian restraint'."
        ),
        "thresholds": {
            "high_repetition": HIGH_REPETITION,
            "low_transition": LOW_TRANSITION,
            "high_transition": HIGH_TRANSITION,
        },
    }
