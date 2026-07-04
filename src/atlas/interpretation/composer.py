"""Atlas Interpretive Composer.

Turns semantic/reasoning outputs into human-facing explanations.

This layer does not calculate charts, graphs, or metrics.
It decides how to explain them.
"""

from __future__ import annotations

from typing import Any


COMPOSER_VERSION = "1.0"


def compose_interpretive_answer(payload: dict[str, Any]) -> str:
    """Compose a human-readable answer from Atlas reasoning payload."""
    scope = payload.get("scope", "general")
    profiles = payload.get("profiles", [])
    synthesis = payload.get("synthesis", {})
    claim = payload.get("claim", "")

    if scope == "relationship":
        return compose_relationship_answer(payload)

    if scope == "profile":
        return compose_profile_answer(payload)

    if len(profiles) >= 3:
        return compose_group_answer(payload)

    return compose_general_answer(payload, claim)


def compose_profile_answer(payload: dict[str, Any]) -> str:
    """Compose one-person interpretation."""
    profiles = payload.get("profiles", [])
    synthesis = payload.get("synthesis", {})
    semantic = synthesis.get("semantic", {})

    name = semantic.get("name") or humanize(first(profiles) or "this profile")
    role = semantic.get("structural_role", "unresolved")
    cognition = semantic.get("cognitive_style", "")
    motivation = semantic.get("motivational_style", "")
    emotion = semantic.get("emotional_style", "")
    stress = semantic.get("stress_response", "")
    growth = semantic.get("growth_path", "")
    civilization = semantic.get("civilization_function", "")
    temporal = semantic.get("temporal_activation", "")

    return f"""### Direct Answer

{name} is best understood as a **{role}**.

### Human Interpretation

{cognition}

{motivation}

{emotion}

### How This Likely Expressed in Life

{civilization}

This means Atlas does not read {name} as a list of isolated traits. It reads {name} as a living pattern: a way of perceiving, choosing, reacting, and shaping the world.

### Under Pressure

{stress}

### Growth Path

{growth}

### Temporal Activation

{temporal}

### Bottom Line

{name} should be understood through the role they naturally play in a larger field. Their graph shows the structure, the natal/Vedic layer describes behavioral style, and the temporal layer shows when that style becomes louder, more visible, or harder to regulate."""