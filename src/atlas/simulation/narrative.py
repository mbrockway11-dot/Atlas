
"""Narrative simulation engine.

Turns structural simulation telemetry into a human-readable scenario walkthrough.
"""

from __future__ import annotations

from typing import Any


def build_simulation_narrative(simulation: dict[str, Any]) -> dict[str, Any]:
    """Build narrative simulation output."""
    sim = simulation.get("simulation", {})
    decisions = sim.get("decisions", {})
    likely = decisions.get("likely_action") or {}
    action = likely.get("action", "unresolved")

    top_nodes = sim.get("propagation", {}).get("top_activated", [])[:6]
    recovery = sim.get("recovery", {})
    growth = simulation.get("growth", {})

    return {
        "title": "If this scenario occurred...",
        "walkthrough": build_walkthrough(action, top_nodes),
        "watch_for": build_watch_for(action),
        "highest_leverage_action": build_highest_leverage_action(action),
        "recovery_narrative": build_recovery_narrative(recovery),
        "growth_narrative": build_growth_narrative(growth),
        "confidence_note": build_confidence_note(top_nodes),
    }


def build_walkthrough(action: str, top_nodes: list[dict[str, Any]]) -> str:
    """Build scenario walkthrough."""
    activated = [
        clean_node(item.get("node_id", ""))
        for item in top_nodes
    ]

    activation_text = ", ".join(activated[:4]) if activated else "the strongest available structural patterns"

    if action in {"structure_plan", "sequence_work", "protect_continuity"}:
        return (
            f"When this scenario begins, Atlas expects the system to orient around {activation_text}. "
            "The first movement is unlikely to be impulsive action. Instead, the system tries to turn pressure "
            "into structure: defining scope, sequencing priorities, and protecting continuity. Once the situation "
            "has a usable architecture, action becomes cleaner and more confident."
        )

    if action in {"map_relationships", "gather_information", "connect_domains"}:
        return (
            f"When this scenario begins, Atlas expects activation around {activation_text}. "
            "The system is likely to pause long enough to map the relationships between moving parts. "
            "Rather than responding only to the surface event, it searches for the pattern behind the event, "
            "then chooses a response based on leverage points."
        )

    if action in {"compress_into_model", "build_symbolic_artifact", "name_the_pattern"}:
        return (
            f"When this scenario begins, Atlas expects activation around {activation_text}. "
            "The system is likely to compress the experience into a model, phrase, diagram, symbol, or reusable framework. "
            "Meaning becomes easier to act on once it has been named and externalized."
        )

    if action in {"explain_publicly", "teach_framework", "publish_artifact"}:
        return (
            f"When this scenario begins, Atlas expects activation around {activation_text}. "
            "The system is likely to move toward public explanation or visible authorship. Communication becomes strongest "
            "after the internal structure is coherent enough to be transmitted clearly."
        )

    return (
        f"When this scenario begins, Atlas expects activation around {activation_text}. "
        "The system is likely to stabilize first, reduce noise, and choose the safest next structural action."
    )


def build_watch_for(action: str) -> list[str]:
    """Build likely failure modes."""
    if action in {"structure_plan", "sequence_work", "protect_continuity"}:
        return [
            "Spending too long refining the structure before acting.",
            "Delaying communication while searching for completeness.",
            "Overbuilding the framework beyond what the situation requires.",
        ]

    if action in {"map_relationships", "gather_information", "connect_domains"}:
        return [
            "Collecting more context than the decision actually needs.",
            "Holding too many frameworks open at once.",
            "Difficulty choosing one path when several interpretations are plausible.",
        ]

    if action in {"compress_into_model", "build_symbolic_artifact", "name_the_pattern"}:
        return [
            "Over-symbolizing before grounding the result.",
            "Creating a model that is elegant but not yet practical.",
            "Mistaking pattern recognition for completion.",
        ]

    if action in {"explain_publicly", "teach_framework", "publish_artifact"}:
        return [
            "Waiting until the explanation is perfect before making it visible.",
            "Overexplaining instead of giving the audience a simple entry point.",
            "Carrying too much of the structure alone.",
        ]

    return [
        "Reducing noise for too long before choosing action.",
        "Waiting for certainty that may not arrive.",
    ]


def build_highest_leverage_action(action: str) -> str:
    """Build highest leverage recommendation."""
    if action in {"structure_plan", "sequence_work", "protect_continuity"}:
        return (
            "Create a simple first version of the plan and expose it to reality quickly. "
            "This preserves the need for structure while preventing refinement from becoming delay."
        )

    if action in {"map_relationships", "gather_information", "connect_domains"}:
        return (
            "Write the relationship map down. Once the structure is external, choose the smallest actionable leverage point."
        )

    if action in {"compress_into_model", "build_symbolic_artifact", "name_the_pattern"}:
        return (
            "Translate the model into plain language. The fastest improvement comes from making the symbol usable by others."
        )

    if action in {"explain_publicly", "teach_framework", "publish_artifact"}:
        return (
            "Publish or present the simplest coherent version. Visibility will clarify what the structure needs next."
        )

    return "Stabilize the environment, name the active pressure, and choose one bounded next action."


def build_recovery_narrative(recovery: dict[str, Any]) -> str:
    """Build recovery narrative."""
    path = recovery.get("recovery_path", [])

    if not path:
        return "Atlas could not identify a recovery path."

    return (
        "Recovery is expected to move through this sequence: "
        + " -> ".join(path)
        + ". The important pattern is return-to-coherence: pressure is absorbed, ordered, and reintegrated."
    )


def build_growth_narrative(growth: dict[str, Any]) -> str:
    """Build growth narrative."""
    vector = growth.get("current_growth_vector", "unresolved")
    sequence = growth.get("growth_sequence", [])

    return (
        f"The growth vector is {vector.replace('_', ' ')}. "
        f"Atlas models growth as: {' -> '.join(sequence)}."
    )


def build_confidence_note(top_nodes: list[dict[str, Any]]) -> str:
    """Build confidence note."""
    if not top_nodes:
        return "Confidence is limited because no activated nodes were available."

    return (
        f"Confidence is based on {len(top_nodes)} highly activated structural nodes after propagation. "
        "The narrative should be read as a likely sequence, not a deterministic prediction."
    )


def clean_node(node_id: str) -> str:
    """Clean node id."""
    return (
        str(node_id)
        .replace("theme:", "")
        .replace("inference:", "")
        .replace("_", " ")
    )
