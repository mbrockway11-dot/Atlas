"""Temporal graph synthesis service.

Combines graph structure, temporal pressure, and human-readable interpretation.
"""

from __future__ import annotations

from typing import Any


TEMPORAL_GRAPH_SYNTHESIS_VERSION = "1.0"


def build_temporal_graph_synthesis(
    *,
    query_plan: dict[str, Any],
    hypothesis_model: dict[str, Any],
    falsification_model: dict[str, Any],
    discovery_model: dict[str, Any],
) -> dict[str, Any]:
    """Build human-readable temporal-graph synthesis."""
    scope = query_plan.get("scope", "general")
    profiles = query_plan.get("profiles", [])

    best = hypothesis_model.get("best_supported_hypothesis") or {}
    claim = best.get("claim", "")

    cases = falsification_model.get("cases", []) or []
    discoveries = discovery_model.get("discoveries", []) or []

    temporal_case = find_temporal_case(cases)
    graph_case = find_graph_case(cases)

    graph_pattern = describe_graph_pattern(claim, graph_case)
    temporal_overlay = describe_temporal_overlay(temporal_case)
    human_meaning = describe_human_meaning(
        scope=scope,
        profiles=profiles,
        claim=claim,
        graph_pattern=graph_pattern,
        temporal_overlay=temporal_overlay,
    )

    return {
        "success": True,
        "version": TEMPORAL_GRAPH_SYNTHESIS_VERSION,
        "scope": scope,
        "profiles": profiles,
        "structural_pattern": graph_pattern,
        "temporal_overlay": temporal_overlay,
        "activation_pressure": describe_activation_pressure(temporal_case, graph_case),
        "human_interpretation": human_meaning,
        "probable_reactions": build_probable_reactions(scope, claim),
        "timing_cautions": build_timing_cautions(temporal_case),
        "confidence": resolve_overlay_confidence(best, temporal_case, graph_case),
        "discovery_context": [
            item.get("title") or item.get("summary")
            for item in discoveries[:3]
            if isinstance(item, dict)
        ],
    }


def find_temporal_case(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Find the most relevant temporal falsification case."""
    for case in cases:
        text = " ".join(
            str(case.get(key, ""))
            for key in ("hypothesis_title", "claim", "source")
        ).lower()

        if any(token in text for token in ("temporal", "birth", "nakshatra", "dasha", "transit")):
            return case

    return {}


def find_graph_case(cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Find the most relevant graph falsification case."""
    for case in cases:
        text = " ".join(
            str(case.get(key, ""))
            for key in ("hypothesis_title", "claim", "source")
        ).lower()

        if any(token in text for token in ("graph", "edge", "node", "alignment", "morphology")):
            return case

    return {}


def describe_graph_pattern(claim: str, graph_case: dict[str, Any]) -> str:
    """Describe the graph structure in plain language."""
    text = " ".join(
        [
            claim,
            str(graph_case.get("hypothesis_title", "")),
            str(graph_case.get("claim", "")),
        ]
    ).lower()

    if "limited" in text or "low" in text:
        return (
            "The graph structure suggests limited smooth alignment. This usually means "
            "the subjects may share a meaningful field, but they do not move through it "
            "in the same way. The relationship is more catalytic than naturally harmonious."
        )

    if "transformation" in text or "mutation" in text:
        return (
            "The graph structure suggests transformation. The relationship appears to "
            "change the shape of the field rather than simply confirm similarity."
        )

    return (
        "The graph structure shows a meaningful pattern, but Atlas should avoid strong "
        "claims until node overlap, edge overlap, and morphology confidence are reviewed."
    )


def describe_temporal_overlay(temporal_case: dict[str, Any]) -> str:
    """Describe temporal pressure in plain language."""
    if not temporal_case:
        return (
            "The temporal overlay is available only in a general way. Atlas can discuss "
            "probable activation, but exact timing should remain provisional."
        )

    pressure = temporal_case.get("falsification_pressure", {})
    label = pressure.get("label", "unknown") if isinstance(pressure, dict) else "unknown"

    return (
        f"The temporal layer is the main timing caution. Its falsification pressure is "
        f"{label}, meaning timing-sensitive claims should be handled carefully until birth, "
        f"Moon/Nakshatra, dasha, or transit assumptions are verified."
    )


def describe_activation_pressure(
    temporal_case: dict[str, Any],
    graph_case: dict[str, Any],
) -> str:
    """Explain how temporal pressure activates graph structure."""
    temporal_pressure = pressure_label(temporal_case)
    graph_pressure = pressure_label(graph_case)

    return (
        "The graph shows the structure; the temporal layer shows when that structure may "
        "become active, stressed, or visible. "
        f"Current graph pressure is {graph_pressure}; temporal pressure is {temporal_pressure}."
    )


def describe_human_meaning(
    *,
    scope: str,
    profiles: list[str],
    claim: str,
    graph_pattern: str,
    temporal_overlay: str,
) -> str:
    """Translate graph + time into human meaning."""
    if scope == "relationship" and len(profiles) >= 2:
        a = humanize_key(profiles[0])
        b = humanize_key(profiles[1])

        return (
            f"Humanly, {a} and {b} should be read as two systems activating each other. "
            "The graph layer describes their structural fit or friction; the temporal layer "
            "describes when that friction becomes more visible. If the graph alignment is limited, "
            "the likely experience is not easy blending. It is contrast, pressure, and mutual "
            "activation. One side may reveal possibility while the other demands form, proof, "
            "execution, or control."
        )

    return (
        "Humanly, this means the structure is not static. The graph describes the person's "
        "baseline pattern, while the temporal overlay describes when that pattern becomes more "
        "intense, more visible, or more difficult to regulate."
    )


def build_probable_reactions(scope: str, claim: str) -> list[str]:
    """Build probable human reactions."""
    if scope == "relationship":
        return [
            "One person may feel energized by the other but not fully understood.",
            "Creative tension may produce breakthroughs when roles are respected.",
            "Stress may turn difference into competition, control, withdrawal, or resentment.",
            "The healthiest outcome comes from naming the contrast instead of forcing similarity.",
        ]

    return [
        "Under supportive timing, the person may express the structure with clarity and confidence.",
        "Under pressure, the same structure may become exaggerated, defensive, or unstable.",
        "Growth comes from recognizing when a repeating pattern is being temporally activated.",
    ]


def build_timing_cautions(temporal_case: dict[str, Any]) -> list[str]:
    """Build timing cautions."""
    if not temporal_case:
        return [
            "Exact timing should remain provisional until the temporal payload is inspected.",
        ]

    observations = temporal_case.get("required_observations", []) or []

    return [
        str(item)
        for item in observations[:5]
    ] or [
        "Verify birth metadata and rerun temporal intelligence before making precise timing claims.",
    ]


def resolve_overlay_confidence(
    best: dict[str, Any],
    temporal_case: dict[str, Any],
    graph_case: dict[str, Any],
) -> str:
    """Resolve overlay confidence."""
    confidence = best.get("confidence", {})
    label = confidence.get("label", "unknown") if isinstance(confidence, dict) else "unknown"
    percent = confidence.get("percent") if isinstance(confidence, dict) else None

    temporal_label = pressure_label(temporal_case)

    if temporal_label in {"high", "critical"}:
        return f"{percent}% {label}, with temporal caution" if percent else f"{label}, with temporal caution"

    return f"{percent}% {label}" if percent else str(label)


def pressure_label(case: dict[str, Any]) -> str:
    """Return pressure label."""
    pressure = case.get("falsification_pressure") or case.get("pressure") or {}

    if isinstance(pressure, dict):
        return str(pressure.get("label", "unknown"))

    return "unknown"


def humanize_key(value: str) -> str:
    """Humanize profile key."""
    return value.replace("_", " ").title()