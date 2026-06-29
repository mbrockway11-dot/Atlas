"""Identity Vector explanations."""

from __future__ import annotations

from atlas.explanation.measurements import classify_value


def explain_identity_vector(identity_vector) -> list[str]:
    """Generate deterministic natural-language explanation lines."""
    features = identity_vector.global_features
    diagnostics = identity_vector.diagnostics

    lines = []

    lines.append(
        "This profile is represented by an Identity Vector built from seven composite planetary structures."
    )

    lines.append(
        f"Overall balance is {classify_value(features['planet_balance_index'])} "
        f"({features['planet_balance_index']:.4f}), meaning the planetary structures are "
        f"{balance_phrase(features['planet_balance_index'])}."
    )

    lines.append(
        f"Structural complexity is {classify_value(features['structural_complexity_index'])} "
        f"({features['structural_complexity_index']:.4f}), indicating "
        f"{complexity_phrase(features['structural_complexity_index'])}."
    )

    lines.append(
        f"Structural stability is {classify_value(features['structural_stability_index'])} "
        f"({features['structural_stability_index']:.4f}), suggesting "
        f"{stability_phrase(features['structural_stability_index'])}."
    )

    lines.append(
        f"The strongest coherence planet is {diagnostics['dominant_coherence_planet']}, "
        f"while the weakest coherence planet is {diagnostics['weakest_coherence_planet']}."
    )

    lines.append(
        f"The strongest stability planet is {diagnostics['dominant_stability_planet']}, "
        f"while the weakest stability planet is {diagnostics['weakest_stability_planet']}."
    )

    lines.append(
        f"The highest entropy planet is {diagnostics['dominant_entropy_planet']}, "
        f"while the lowest entropy planet is {diagnostics['weakest_entropy_planet']}."
    )

    return lines


def balance_phrase(value: float) -> str:
    """Describe balance value."""
    if value >= 0.75:
        return "well distributed rather than dominated by a single planetary channel"
    if value >= 0.45:
        return "partly distributed with some planetary emphasis"
    return "strongly concentrated into a narrower planetary emphasis"


def complexity_phrase(value: float) -> str:
    """Describe complexity value."""
    if value >= 0.75:
        return "a highly articulated structure with broad coverage and many active transitions"
    if value >= 0.45:
        return "a moderately complex structure with both concentrated and distributed behavior"
    return "a simpler or more compressed structure with fewer active differentiating features"


def stability_phrase(value: float) -> str:
    """Describe stability value."""
    if value >= 0.75:
        return "strong persistence across reduction, attractor behavior, and topology"
    if value >= 0.45:
        return "moderate persistence with both stable and shifting regions"
    return "a more fluid structure with weaker persistence across reductions"