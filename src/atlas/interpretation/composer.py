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

def compose_relationship_answer(payload: dict[str, Any]) -> str:
    """Compose relationship interpretation."""
    synthesis = payload.get("synthesis", {})
    relationship = synthesis.get("relationship", {})
    profile_a = synthesis.get("profile_a", {})
    profile_b = synthesis.get("profile_b", {})

    a = profile_a.get("name", "Profile A")
    b = profile_b.get("name", "Profile B")

    return f"""### Direct Answer

{a} and {b} are best understood as two structural systems interacting.

### Human Interpretation

{relationship.get("relationship_summary", "")}

### Structural Dynamic

{relationship.get("dynamic", "")}

### Temporal Interaction

{relationship.get("temporal_interaction", "")}

### Civilization Function

{relationship.get("civilization_function", "")}

### Growth Path

{relationship.get("growth_path", "")}

### Bottom Line

This relationship should be understood through the feedback loop between both people, not through simple similarity alone."""


def compose_group_answer(payload: dict[str, Any]) -> str:
    """Compose group interpretation."""
    profiles = payload.get("profiles", [])

    return f"""### Direct Answer

Atlas reads this as a composite field of {len(profiles)} profiles.

### Human Interpretation

A group should be understood as an interaction between structural roles. Drivers create motion, Amplifiers spread signal, Regulators stabilize form, and Catalysts introduce mutation.

### Bottom Line

The group outcome depends on whether the roles differentiate clearly or collapse into conflict."""


def compose_general_answer(payload: dict[str, Any], claim: str = "") -> str:
    """Compose general interpretation."""
    return f"""### Direct Answer

{claim or "Atlas found a meaningful pattern, but the interpretation remains provisional."}

### Human Interpretation

Atlas needs a clearer profile, relationship, group, or timing target to produce a richer human interpretation."""


def first(values: list[Any]) -> Any:
    """Return first item or None."""
    return values[0] if values else None


def humanize(value: str) -> str:
    """Humanize profile keys."""
    return str(value).replace("_", " ").title()
