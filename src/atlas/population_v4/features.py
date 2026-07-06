
"""Population Intelligence v4 feature extraction.

This module converts canonical profile payloads into stable population
feature records. The output is intentionally simple and deterministic so
later v4 layers can build clustering, archetypes, similarity, rarity, and
outlier detection on top of it.
"""

from __future__ import annotations

from typing import Any


FEATURE_VERSION = "4.0.0"


def build_population_feature_record(
    profile_key: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Build one population feature record from a canonical payload."""
    systems = payload.get("systems_report", {}) or {}

    return {
        "feature_version": FEATURE_VERSION,
        "profile_key": profile_key,
        "success": bool(payload.get("success")),
        "identity": extract_identity(payload),
        "summary": extract_summary(payload, systems),
        "themes": extract_themes(systems),
        "inferences": extract_inferences(systems),
        "tensions": extract_tensions(systems),
        "evidence": extract_evidence_summary(systems),
        "metrics": extract_metrics(payload, systems),
        "vector": build_feature_vector(payload, systems),
    }


def extract_identity(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract stable identity fields."""
    identity = payload.get("identity", {}) or {}
    intake = payload.get("intake", {}) or {}

    return {
        "name": first_present(
            identity,
            intake,
            [
                "name",
                "full_name",
                "display_name",
            ],
        ),
        "birth_date": first_present(
            identity,
            intake,
            [
                "birth_date",
                "date_of_birth",
                "dob",
            ],
        ),
        "birth_time": first_present(
            identity,
            intake,
            [
                "birth_time",
                "time_of_birth",
            ],
        ),
        "birth_location": first_present(
            identity,
            intake,
            [
                "birth_location",
                "place_of_birth",
                "location",
            ],
        ),
    }


def extract_summary(payload: dict[str, Any], systems: dict[str, Any]) -> dict[str, Any]:
    """Extract compact system summary."""
    executive = systems.get("executive_summary", {}) or systems.get("executive", {})

    return {
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
        "profile_status": payload.get("status") or payload.get("profile_status") or "compiled",
    }


def extract_themes(systems: dict[str, Any]) -> list[str]:
    """Extract normalized theme labels."""
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


def extract_inferences(systems: dict[str, Any]) -> list[str]:
    """Extract normalized inference labels."""
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


def extract_tensions(systems: dict[str, Any]) -> list[str]:
    """Extract normalized tension labels."""
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


def extract_evidence_summary(systems: dict[str, Any]) -> dict[str, Any]:
    """Extract evidence summary fields."""
    evidence = systems.get("evidence_matrix", {}) or systems.get("evidence", {})
    explainability = systems.get("explainability", {}) or {}

    engines = []

    for key in [
        "engines",
        "sources",
        "evidence_engines",
    ]:
        engines.extend(as_list(evidence.get(key)))

    return {
        "engine_count": len(unique_normalized(engines)),
        "engines": unique_normalized(engines),
        "explanation_count": count_items(explainability.get("explanations")),
        "evidence_record_count": count_items(evidence.get("records"))
        or count_items(evidence.get("items"))
        or int_or_zero(evidence.get("record_count")),
    }


def extract_metrics(payload: dict[str, Any], systems: dict[str, Any]) -> dict[str, Any]:
    """Extract useful numeric metrics."""
    metrics = payload.get("metrics", {}) or {}
    inference_graph = systems.get("inference_graph", {}) or {}
    consensus = systems.get("consensus", {}) or {}
    reasoning = systems.get("reasoning", {}) or {}

    return {
        "has_identity": bool(metrics.get("has_identity")),
        "has_kamea": bool(metrics.get("has_kamea")),
        "has_temporal": bool(metrics.get("has_temporal")),
        "has_systems_report": bool(metrics.get("has_systems_report") or systems.get("success")),
        "inference_node_count": count_items(inference_graph.get("nodes")),
        "inference_edge_count": count_items(inference_graph.get("edges")),
        "consensus_theme_count": count_items(consensus.get("themes"))
        or count_items(consensus.get("strongest_themes")),
        "reasoning_rule_count": count_items(reasoning.get("applied_rules"))
        or count_items(reasoning.get("rules")),
    }


def build_feature_vector(payload: dict[str, Any], systems: dict[str, Any]) -> dict[str, float]:
    """Build deterministic numeric feature vector."""
    themes = extract_themes(systems)
    inferences = extract_inferences(systems)
    tensions = extract_tensions(systems)
    evidence = extract_evidence_summary(systems)
    metrics = extract_metrics(payload, systems)
    summary = extract_summary(payload, systems)

    vector: dict[str, float] = {
        "theme_count": float(len(themes)),
        "inference_count": float(len(inferences)),
        "tension_count": float(len(tensions)),
        "evidence_engine_count": float(evidence.get("engine_count", 0)),
        "explanation_count": float(evidence.get("explanation_count", 0)),
        "evidence_record_count": float(evidence.get("evidence_record_count", 0)),
        "inference_node_count": float(metrics.get("inference_node_count", 0)),
        "inference_edge_count": float(metrics.get("inference_edge_count", 0)),
        "reasoning_rule_count": float(metrics.get("reasoning_rule_count", 0)),
    }

    add_one_hot(vector, "class", summary.get("system_class"))
    add_one_hot(vector, "architecture", summary.get("primary_architecture"))

    for theme in themes:
        vector[f"theme::{theme}"] = 1.0

    for inference in inferences:
        vector[f"inference::{inference}"] = 1.0

    for tension in tensions:
        vector[f"tension::{tension}"] = 1.0

    return vector


def add_one_hot(vector: dict[str, float], prefix: str, value: Any) -> None:
    """Add one-hot encoded field when value is populated."""
    label = normalize_label(value)

    if label and label not in {"none", "null", "unknown", "unresolved"}:
        vector[f"{prefix}::{label}"] = 1.0


def as_list(value: Any) -> list[Any]:
    """Convert common payload shapes into a list."""
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
        if "node_id" in value:
            return [value.get("node_id")]
        return list(value.keys())

    return [value]


def item_to_label(item: Any) -> str:
    """Convert item shape into a label."""
    if isinstance(item, dict):
        for key in [
            "name",
            "label",
            "id",
            "theme",
            "rule",
            "node_id",
            "source",
            "engine",
        ]:
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


def normalize_label(value: Any) -> str:
    """Normalize labels for stable population comparison."""
    return (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def first_value(source: dict[str, Any], keys: list[str]) -> str:
    """Return first populated source value."""
    for key in keys:
        if source.get(key):
            return str(source.get(key))

    return "unresolved"


def first_present(left: dict[str, Any], right: dict[str, Any], keys: list[str]) -> str:
    """Return first populated value from two dictionaries."""
    for source in [left, right]:
        for key in keys:
            if source.get(key):
                return str(source.get(key))

    return ""


def count_items(value: Any) -> int:
    """Count common collection shapes."""
    if value is None:
        return 0

    if isinstance(value, dict):
        return len(value)

    if isinstance(value, (list, tuple, set)):
        return len(value)

    return 1


def int_or_zero(value: Any) -> int:
    """Convert to int or zero."""
    try:
        return int(value)
    except Exception:
        return 0
