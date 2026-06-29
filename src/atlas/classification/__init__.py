"""Atlas classification public API."""

from atlas.classification.expression import (
    TopologicalExpression,
    classify_topological_expression,
)
from atlas.classification.functional_role import (
    FunctionalRole,
    classify_functional_role,
)
from atlas.classification.meanings import (
    FUNCTIONAL_ROLE_MEANINGS,
    PLANETARY_TOPOLOGY_MEANINGS,
    STRUCTURAL_STATE_MEANINGS,
    TOPOLOGICAL_EXPRESSION_MEANINGS,
    get_expression_meaning,
    get_functional_role_meaning,
    get_planetary_topology_meaning,
    get_structural_state_meaning,
)
from atlas.classification.profile_classifier import (
    AtlasClassification,
    classification_to_dict,
    classify_signature,
)
from atlas.classification.structural_state import (
    StructuralState,
    classify_structural_state,
)

__all__ = [
    "FunctionalRole",
    "classify_functional_role",
    "TopologicalExpression",
    "classify_topological_expression",
    "StructuralState",
    "classify_structural_state",
    "AtlasClassification",
    "classify_signature",
    "classification_to_dict",
    "FUNCTIONAL_ROLE_MEANINGS",
    "TOPOLOGICAL_EXPRESSION_MEANINGS",
    "STRUCTURAL_STATE_MEANINGS",
    "PLANETARY_TOPOLOGY_MEANINGS",
    "get_functional_role_meaning",
    "get_expression_meaning",
    "get_structural_state_meaning",
    "get_planetary_topology_meaning",
]