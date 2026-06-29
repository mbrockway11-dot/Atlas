"""Composite Atlas profile classification."""

from dataclasses import dataclass
from typing import Any

from atlas.classification.expression import (
    TopologicalExpression,
    classify_topological_expression,
)
from atlas.classification.functional_role import (
    FunctionalRole,
    classify_functional_role,
)
from atlas.classification.structural_state import (
    StructuralState,
    classify_structural_state,
)
from atlas.signatures.topology_signature import TopologySignature


@dataclass(frozen=True)
class AtlasClassification:
    """Layered Atlas classification output."""

    function: FunctionalRole
    expression: TopologicalExpression
    state: StructuralState
    scale: str


def classify_signature(
    signature: TopologySignature,
    scale: str = "Individual",
) -> AtlasClassification:
    """Classify one topology signature across Atlas classification layers."""
    return AtlasClassification(
        function=classify_functional_role(signature),
        expression=classify_topological_expression(signature),
        state=classify_structural_state(signature),
        scale=scale,
    )


def classification_to_dict(
    classification: AtlasClassification,
) -> dict[str, Any]:
    """Convert AtlasClassification to JSON-safe dictionary."""
    return {
        "function": {
            "role": classification.function.role,
            "confidence": classification.function.confidence,
            "driver": classification.function.driver,
            "amplifier": classification.function.amplifier,
            "regulator": classification.function.regulator,
        },
        "expression": {
            "type": classification.expression.expression,
            "reason": classification.expression.reason,
        },
        "state": {
            "type": classification.state.state,
            "reason": classification.state.reason,
        },
        "scale": classification.scale,
        "summary": (
            f"{classification.function.role} + "
            f"{classification.expression.expression} + "
            f"{classification.state.state} + "
            f"{classification.scale}"
        ),
    }