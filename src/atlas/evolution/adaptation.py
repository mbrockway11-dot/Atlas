
"""Evolution adaptation model."""

from __future__ import annotations

from typing import Any


def build_adaptation_report(learning: dict[str, Any]) -> dict[str, Any]:
    """Build adaptation report."""
    signal = learning.get("learning_signal", "mixed_adaptation")

    if signal == "structure_reinforcement":
        return {
            "adaptation_label": "Structural reinforcement",
            "expected_change": "The twin becomes faster at converting pressure into ordered plans.",
            "strengthened_features": ["persistent_architecture", "constraint_pattern", "long_horizon_planning"],
            "watch_for": ["over-structuring", "delayed execution"],
        }

    if signal == "visibility_reinforcement":
        return {
            "adaptation_label": "Visibility reinforcement",
            "expected_change": "The twin becomes more likely to externalize structure through teaching or authorship.",
            "strengthened_features": ["visible_authorship", "message_propagation", "expressive_catalysis"],
            "watch_for": ["visibility fatigue", "overexplaining"],
        }

    if signal == "cognitive_mapping_reinforcement":
        return {
            "adaptation_label": "Mapping reinforcement",
            "expected_change": "The twin becomes more likely to map relationships before acting.",
            "strengthened_features": ["information_routing", "distributed_integration", "cross_domain_linking"],
            "watch_for": ["analysis drag", "too many open frameworks"],
        }

    return {
        "adaptation_label": "Mixed adaptation",
        "expected_change": "The twin shows multiple adaptation pathways without a single dominant reinforcement pattern.",
        "strengthened_features": [],
        "watch_for": ["unstable learning signal"],
    }
