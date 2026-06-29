"""Atlas structural ontology."""

from atlas.ontology.archetypes import (
    STRUCTURAL_ARCHETYPES,
    get_archetype,
    list_archetypes,
    rank_archetypes,
    score_archetype,
    score_archetypes,
)
from atlas.ontology.identity import (
    synthesize_identity_ontology,
)
from atlas.ontology.structural_roles import (
    STRUCTURAL_ROLE_ONTOLOGY,
    explain_structural_role,
    rank_structural_roles,
)

__all__ = [
    "STRUCTURAL_ARCHETYPES",
    "STRUCTURAL_ROLE_ONTOLOGY",
    "get_archetype",
    "list_archetypes",
    "score_archetype",
    "score_archetypes",
    "rank_archetypes",
    "explain_structural_role",
    "rank_structural_roles",
    "synthesize_identity_ontology",
]