"""Identity Vector interpretation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.explanation import (
    explain_archetype_score,
    explain_metric_value,
    explain_planet_feature,
)
from atlas.ontology import synthesize_identity_ontology


@dataclass(frozen=True)
class IdentityInterpretation:
    """Profile-specific Identity Vector interpretation."""

    name: str
    summary_lines: list[str]
    global_interpretation: list[str]
    planet_interpretations: dict[str, list[str]]
    archetype_interpretations: list[str]


def interpret_identity_vector(identity_vector) -> IdentityInterpretation:
    """Interpret one Identity Vector."""
    ontology = synthesize_identity_ontology(identity_vector)

    summary_lines = build_identity_summary_lines(identity_vector, ontology)
    global_interpretation = build_global_interpretation(identity_vector)
    planet_interpretations = build_planet_interpretations(identity_vector)
    archetype_interpretations = build_archetype_interpretations(ontology)

    return IdentityInterpretation(
        name=identity_vector.name,
        summary_lines=summary_lines,
        global_interpretation=global_interpretation,
        planet_interpretations=planet_interpretations,
        archetype_interpretations=archetype_interpretations,
    )


def identity_interpretation_to_dict(
    interpretation: IdentityInterpretation,
) -> dict[str, Any]:
    """Convert interpretation to JSON-safe dictionary."""
    return {
        "name": interpretation.name,
        "summary_lines": interpretation.summary_lines,
        "global_interpretation": interpretation.global_interpretation,
        "planet_interpretations": interpretation.planet_interpretations,
        "archetype_interpretations": interpretation.archetype_interpretations,
    }


def build_identity_summary_lines(identity_vector, ontology: dict) -> list[str]:
    """Build high-level identity summary."""
    features = identity_vector.global_features
    diagnostics = identity_vector.diagnostics

    lines = [
        f"{identity_vector.name} is represented by a normalized Identity Vector.",
        (
            f"Balance index is {features['planet_balance_index']:.4f}, "
            f"complexity is {features['structural_complexity_index']:.4f}, "
            f"and stability is {features['structural_stability_index']:.4f}."
        ),
        (
            f"Dominant coherence appears through "
            f"{diagnostics['dominant_coherence_planet']}; dominant stability "
            f"appears through {diagnostics['dominant_stability_planet']}."
        ),
    ]

    global_archetypes = ontology.get("global_archetypes", [])

    if global_archetypes:
        top = global_archetypes[0]
        lines.append(
            f"Primary structural archetype is {top['label']} "
            f"with score {top['score']:.4f}."
        )

    return lines


def build_global_interpretation(identity_vector) -> list[str]:
    """Interpret global Identity Vector metrics."""
    features = identity_vector.global_features

    metrics = [
        "planet_balance_index",
        "planet_variance_index",
        "structural_complexity_index",
        "structural_stability_index",
        "mean_graph_coherence",
        "mean_entropy",
        "mean_bridge_ratio",
        "mean_loop_ratio",
        "mean_hub_ratio",
        "mean_leaf_ratio",
    ]

    return [
        explain_metric_value(metric, features[metric])
        for metric in metrics
        if metric in features
    ]


def build_planet_interpretations(identity_vector) -> dict[str, list[str]]:
    """Interpret each composite planet vector."""
    interpretations: dict[str, list[str]] = {}

    for planet, vector in identity_vector.planets.items():
        strongest_feature = strongest_numeric_feature(vector.features)

        lines = [
            explain_planet_feature(planet, strongest_feature),
            explain_metric_value(
                "graph_coherence",
                vector.features.get("graph_coherence", 0.0),
            ),
            explain_metric_value(
                "topology_stability",
                vector.features.get("topology_stability", 0.0),
            ),
            explain_metric_value(
                "entropy",
                vector.features.get("entropy", 0.0),
            ),
        ]

        interpretations[planet] = lines

    return interpretations


def build_archetype_interpretations(ontology: dict) -> list[str]:
    """Interpret global ontology archetypes."""
    return [
        explain_archetype_score(
            archetype["key"],
            archetype["score"],
        )
        for archetype in ontology.get("global_archetypes", [])[:5]
    ]


def strongest_numeric_feature(features: dict[str, Any]) -> str:
    """Find strongest numeric feature in a feature dictionary."""
    numeric_items = [
        (key, value)
        for key, value in features.items()
        if isinstance(value, int | float)
    ]

    if not numeric_items:
        return "unknown"

    return max(
        numeric_items,
        key=lambda item: float(item[1]),
    )[0]