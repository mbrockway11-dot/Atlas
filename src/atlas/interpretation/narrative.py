"""
Atlas Narrative Engine.

Converts semantic interpretations into human-readable explanations.

This module NEVER performs analysis.

It only explains deterministic semantic models.
"""

from __future__ import annotations

from typing import Any


NARRATIVE_VERSION = "1.0.0"


def compose_profile(
    semantic: dict[str, Any],
) -> str:
    """
    Compose a narrative explanation for one person.
    """

    name = semantic.get("name", "Unknown")

    role = semantic.get("structural_role", "Unknown")

    cognition = semantic.get("cognitive_style", "")

    motivation = semantic.get("motivational_style", "")

    emotion = semantic.get("emotional_style", "")

    relationship = semantic.get("relational_style", "")

    stress = semantic.get("stress_response", "")

    growth = semantic.get("growth_path", "")

    civilization = semantic.get("civilization_function", "")

    activation = semantic.get("temporal_activation", "")

    behaviors = semantic.get("probable_behavior", [])

    behavior_text = "\n".join(
        f"- {item}" for item in behaviors
    )

    return f"""
# {name}

## Structural Role

{name} is currently interpreted as a **{role}**.

Rather than describing personality traits in isolation, Atlas attempts to
identify the structural role a person naturally occupies inside larger
systems.

## Cognitive Style

{cognition}

## Motivation

{motivation}

## Emotional Expression

{emotion}

## Relationship Style

{relationship}

## Stress Pattern

{stress}

## Growth Path

{growth}

## Civilization Function

{civilization}

## Temporal Activation

{activation}

## Probable Behaviors

{behavior_text}

## Interpretation

Taken together, these layers suggest that {name} should not be understood as
a collection of isolated traits. Instead, Atlas models this person as a
dynamic system whose graph structure, temporal state, and semantic role work
together to produce recognizable patterns of behavior.
""".strip()


def compose_relationship(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
    relationship: dict[str, Any],
) -> str:
    """
    Compose a narrative explanation for two people.
    """

    a = profile_a["name"]

    b = profile_b["name"]

    summary = relationship.get("relationship_summary", "")

    dynamic = relationship.get("dynamic", "")

    temporal = relationship.get(
        "temporal_interaction",
        "",
    )

    civilization = relationship.get(
        "civilization_function",
        "",
    )

    growth = relationship.get(
        "growth_path",
        "",
    )

    outcomes = relationship.get(
        "probable_outcomes",
        [],
    )

    stresses = relationship.get(
        "stress_points",
        [],
    )

    outcome_text = "\n".join(
        f"- {item}" for item in outcomes
    )

    stress_text = "\n".join(
        f"- {item}" for item in stresses
    )

    return f"""
# {a} ↔ {b}

## Overall Interpretation

{summary}

## Structural Dynamic

{dynamic}

## Temporal Interaction

{temporal}

## Civilization Function

{civilization}

## Stress Points

{stress_text}

## Probable Outcomes

{outcome_text}

## Growth Path

{growth}

## Interpretation

Atlas does not treat compatibility as simple similarity.

Instead, the relationship is interpreted as the interaction between two
structural systems.

The important question is therefore not:

"Are these people alike?"

The more useful question is:

"What does each person's structure bring out in the other?"

That interaction often explains far more than personality traits alone.
""".strip()


def compose_population(
    semantic_profiles: list[dict[str, Any]],
) -> str:
    """
    Compose a population narrative.
    """

    count = len(semantic_profiles)

    return f"""
Atlas analyzed {count} semantic profiles.

Rather than averaging personalities, the system searches for recurring
structural roles, complementary functions, and emergent organization across
the population.

Population narratives should explain how groups self-organize rather than
simply listing statistics.
""".strip()