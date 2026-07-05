"""Identity ontology synthesis."""

from __future__ import annotations

from atlas.ontology.archetypes import rank_archetypes
from atlas.ontology.structural_roles import rank_structural_roles


def synthesize_identity_ontology(identity_vector) -> dict:
    """Build ontology synthesis from an IdentityVector."""
    global_archetypes = rank_archetypes(identity_vector.global_features)

    planet_archetypes = {
        planet: rank_archetypes(vector.features)
        for planet, vector in identity_vector.planets.items()
    }

    return {
        "name": identity_vector.name,
        "global_archetypes": global_archetypes,
        "planet_archetypes": planet_archetypes,
        "summary": build_ontology_summary(
            global_archetypes,
            planet_archetypes,
        ),
    }


def build_ontology_summary(
    global_archetypes: list[dict],
    planet_archetypes: dict[str, list[dict]],
) -> list[str]:
    """Build deterministic ontology summary lines."""
    lines = []

    if global_archetypes:
        top = global_archetypes[0]
        lines.append(
            f"Primary global archetype is {top['label']} "
            f"({top['score']:.4f})."
        )

    strongest_planet = None
    strongest_score = -1.0
    strongest_label = None

    for planet, ranked in planet_archetypes.items():
        if not ranked:
            continue

        top = ranked[0]

        if top["score"] > strongest_score:
            strongest_score = top["score"]
            strongest_planet = planet
            strongest_label = top["label"]

    if strongest_planet and strongest_label:
        lines.append(
            f"Strongest planet-level archetype is {strongest_label} "
            f"in {strongest_planet} ({strongest_score:.4f})."
        )

    return lines
