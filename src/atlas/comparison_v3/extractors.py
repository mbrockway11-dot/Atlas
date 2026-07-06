
"""Extraction helpers for Comparison v3."""

from __future__ import annotations

from typing import Any


def normalize_label(value: Any) -> str:
    """Normalize a label for comparison."""
    return str(value or "").strip().lower().replace(" ", "_")


def pretty_label(value: Any) -> str:
    """Pretty-print a normalized label."""
    return str(value or "").replace("_", " ").strip().title()


def extract_systems_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract systems report from canonical payload."""
    return payload.get("systems_report", {}) or {}


def extract_profile_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract compact profile summary."""
    systems = extract_systems_report(payload)
    executive = systems.get("executive_summary", {}) or systems.get("executive", {})

    return {
        "profile_key": payload.get("profile_key") or systems.get("profile_key"),
        "system_class": first_value(
            executive,
            [
                "system_class",
                "class",
                "primary_class",
            ],
        ),
        "subtype": first_value(
            executive,
            [
                "subtype",
                "system_subtype",
                "primary_subtype",
            ],
        ),
        "primary_architecture": first_value(
            executive,
            [
                "primary_architecture",
                "architecture",
                "dominant_architecture",
            ],
        ),
    }


def extract_themes(payload: dict[str, Any]) -> list[str]:
    """Extract comparison themes from payload."""
    systems = extract_systems_report(payload)
    candidates: list[Any] = []

    for key in [
        "strongest_themes",
        "consensus_themes",
        "dominant_themes",
        "themes",
    ]:
        candidates.extend(as_list(systems.get(key)))

    consensus = systems.get("consensus", {}) or {}
    for key in [
        "strongest_themes",
        "themes",
        "dominant_themes",
        "consensus_themes",
    ]:
        candidates.extend(as_list(consensus.get(key)))

    executive = systems.get("executive_summary", {}) or systems.get("executive", {})
    for key in [
        "strongest_themes",
        "themes",
    ]:
        candidates.extend(as_list(executive.get(key)))

    reasoning = systems.get("reasoning", {}) or {}
    candidates.extend(as_list(reasoning.get("themes")))

    return unique_normalized(candidates)


def extract_inferences(payload: dict[str, Any]) -> list[str]:
    """Extract inference/rule labels from payload."""
    systems = extract_systems_report(payload)
    candidates: list[Any] = []

    reasoning = systems.get("reasoning", {}) or {}
    for key in [
        "applied_rules",
        "rules",
        "inferences",
        "primary_inferences",
    ]:
        candidates.extend(as_list(reasoning.get(key)))

    executive = systems.get("executive_summary", {}) or systems.get("executive", {})
    for key in [
        "applied_rules",
        "rules",
        "inferences",
    ]:
        candidates.extend(as_list(executive.get(key)))

    graph = systems.get("inference_graph", {}) or {}
    candidates.extend(as_list(graph.get("nodes")))

    return unique_normalized(candidates)


def extract_tensions(payload: dict[str, Any]) -> list[str]:
    """Extract structural tensions."""
    systems = extract_systems_report(payload)
    candidates: list[Any] = []

    for key in [
        "tensions",
        "structural_tensions",
    ]:
        candidates.extend(as_list(systems.get(key)))

    tensions = systems.get("tensions_report", {}) or systems.get("structural_tensions", {})
    for key in [
        "tensions",
        "items",
    ]:
        candidates.extend(as_list(tensions.get(key)))

    return unique_normalized(candidates)


def extract_evidence_engines(payload: dict[str, Any]) -> list[str]:
    """Extract evidence engine labels when available."""
    systems = extract_systems_report(payload)
    evidence = systems.get("evidence_matrix", {}) or systems.get("evidence", {})
    candidates: list[Any] = []

    for key in [
        "engines",
        "sources",
        "evidence_engines",
    ]:
        candidates.extend(as_list(evidence.get(key)))

    return unique_normalized(candidates)


def as_list(value: Any) -> list[Any]:
    """Convert common payload shapes to a list."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, tuple):
        return list(value)

    if isinstance(value, set):
        return list(value)

    if isinstance(value, dict):
        if "name" in value:
            return [value.get("name")]
        if "label" in value:
            return [value.get("label")]
        if "id" in value:
            return [value.get("id")]
        return list(value.keys())

    return [value]


def item_to_label(item: Any) -> str:
    """Convert item shape to label."""
    if isinstance(item, dict):
        for key in ["name", "label", "id", "theme", "rule", "node_id"]:
            if item.get(key):
                return str(item.get(key))
        return ""

    return str(item)


def unique_normalized(items: list[Any]) -> list[str]:
    """Return unique normalized item labels."""
    seen: set[str] = set()
    output: list[str] = []

    for item in items:
        label = normalize_label(item_to_label(item))

        if not label or label in {"none", "null", "unknown", "unresolved"}:
            continue

        if label not in seen:
            seen.add(label)
            output.append(label)

    return output


def first_value(source: dict[str, Any], keys: list[str]) -> str:
    """Return first populated source value."""
    for key in keys:
        if source.get(key):
            return str(source.get(key))
    return "unresolved"
