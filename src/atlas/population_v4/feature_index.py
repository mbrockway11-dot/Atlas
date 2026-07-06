
"""Population Intelligence v4 feature index.

Indexes population v4 corpus records for fast lookup by structural labels,
themes, inferences, tensions, evidence engines, and vector features.
"""

from __future__ import annotations

from typing import Any


FEATURE_INDEX_VERSION = "4.0.0"


def build_population_feature_index(corpus: dict[str, Any]) -> dict[str, Any]:
    """Build feature index from a Population v4 corpus."""
    records = corpus.get("records", []) or []

    index = {
        "success": True,
        "version": FEATURE_INDEX_VERSION,
        "profile_count": len(records),
        "by_profile": {},
        "by_system_class": {},
        "by_subtype": {},
        "by_architecture": {},
        "by_theme": {},
        "by_inference": {},
        "by_tension": {},
        "by_evidence_engine": {},
        "by_vector_feature": {},
        "feature_frequencies": {},
        "summary": {},
    }

    for record in records:
        profile_key = str(record.get("profile_key") or "")
        if not profile_key:
            continue

        index["by_profile"][profile_key] = build_profile_index_entry(record)

        summary = record.get("summary", {}) or {}
        evidence = record.get("evidence", {}) or {}
        vector = record.get("vector", {}) or {}

        add(index["by_system_class"], summary.get("system_class"), profile_key)
        add(index["by_subtype"], summary.get("subtype"), profile_key)
        add(index["by_architecture"], summary.get("primary_architecture"), profile_key)

        for theme in record.get("themes", []) or []:
            add(index["by_theme"], theme, profile_key)

        for inference in record.get("inferences", []) or []:
            add(index["by_inference"], inference, profile_key)

        for tension in record.get("tensions", []) or []:
            add(index["by_tension"], tension, profile_key)

        for engine in evidence.get("engines", []) or []:
            add(index["by_evidence_engine"], engine, profile_key)

        for feature, value in vector.items():
            if float_or_zero(value) != 0.0:
                add(index["by_vector_feature"], feature, profile_key)
                index["feature_frequencies"][feature] = index["feature_frequencies"].get(feature, 0) + 1

    normalize_index_lists(index)

    index["summary"] = build_index_summary(index)

    return index


def build_profile_index_entry(record: dict[str, Any]) -> dict[str, Any]:
    """Build compact profile index entry."""
    summary = record.get("summary", {}) or {}
    evidence = record.get("evidence", {}) or {}
    metrics = record.get("metrics", {}) or {}
    vector = record.get("vector", {}) or {}

    return {
        "profile_key": record.get("profile_key"),
        "identity": record.get("identity", {}),
        "system_class": summary.get("system_class", "unresolved"),
        "subtype": summary.get("subtype", "unresolved"),
        "primary_architecture": summary.get("primary_architecture", "unresolved"),
        "themes": record.get("themes", []) or [],
        "inferences": record.get("inferences", []) or [],
        "tensions": record.get("tensions", []) or [],
        "evidence_engines": evidence.get("engines", []) or [],
        "theme_count": len(record.get("themes", []) or []),
        "inference_count": len(record.get("inferences", []) or []),
        "tension_count": len(record.get("tensions", []) or []),
        "evidence_engine_count": evidence.get("engine_count", 0),
        "inference_node_count": metrics.get("inference_node_count", 0),
        "inference_edge_count": metrics.get("inference_edge_count", 0),
        "nonzero_vector_features": [
            feature
            for feature, value in vector.items()
            if float_or_zero(value) != 0.0
        ],
    }


def add(bucket: dict[str, list[str]], label: Any, profile_key: str) -> None:
    """Add profile key to bucket label."""
    normalized = normalize_label(label)

    if not normalized:
        return

    if normalized in {"none", "null", "unknown", "unresolved"}:
        return

    bucket.setdefault(normalized, [])

    if profile_key not in bucket[normalized]:
        bucket[normalized].append(profile_key)


def normalize_index_lists(index: dict[str, Any]) -> None:
    """Sort all index profile lists."""
    for key, value in index.items():
        if not key.startswith("by_"):
            continue

        if isinstance(value, dict):
            for label, profiles in value.items():
                if isinstance(profiles, list):
                    value[label] = sorted(profiles)


def build_index_summary(index: dict[str, Any]) -> dict[str, Any]:
    """Build compact feature index summary."""
    return {
        "profile_count": index.get("profile_count", 0),
        "system_class_count": len(index.get("by_system_class", {})),
        "subtype_count": len(index.get("by_subtype", {})),
        "architecture_count": len(index.get("by_architecture", {})),
        "theme_count": len(index.get("by_theme", {})),
        "inference_count": len(index.get("by_inference", {})),
        "tension_count": len(index.get("by_tension", {})),
        "evidence_engine_count": len(index.get("by_evidence_engine", {})),
        "vector_feature_count": len(index.get("by_vector_feature", {})),
        "top_system_classes": top_buckets(index.get("by_system_class", {})),
        "top_architectures": top_buckets(index.get("by_architecture", {})),
        "top_themes": top_buckets(index.get("by_theme", {})),
        "top_inferences": top_buckets(index.get("by_inference", {})),
        "top_vector_features": top_frequency(index.get("feature_frequencies", {})),
    }


def top_buckets(bucket: dict[str, list[str]], *, limit: int = 20) -> list[dict[str, Any]]:
    """Return top bucket counts."""
    rows = [
        {
            "label": label,
            "count": len(profiles),
        }
        for label, profiles in bucket.items()
    ]

    return sorted(rows, key=lambda item: (-item["count"], item["label"]))[:limit]


def top_frequency(frequencies: dict[str, int], *, limit: int = 20) -> list[dict[str, Any]]:
    """Return top feature frequencies."""
    rows = [
        {
            "label": label,
            "count": count,
        }
        for label, count in frequencies.items()
    ]

    return sorted(rows, key=lambda item: (-item["count"], item["label"]))[:limit]


def query_feature_index(
    index: dict[str, Any],
    *,
    system_class: str | None = None,
    subtype: str | None = None,
    architecture: str | None = None,
    theme: str | None = None,
    inference: str | None = None,
    tension: str | None = None,
    evidence_engine: str | None = None,
    vector_feature: str | None = None,
) -> dict[str, Any]:
    """Query feature index by one or more labels."""
    sets: list[set[str]] = []

    add_query_set(sets, index.get("by_system_class", {}), system_class)
    add_query_set(sets, index.get("by_subtype", {}), subtype)
    add_query_set(sets, index.get("by_architecture", {}), architecture)
    add_query_set(sets, index.get("by_theme", {}), theme)
    add_query_set(sets, index.get("by_inference", {}), inference)
    add_query_set(sets, index.get("by_tension", {}), tension)
    add_query_set(sets, index.get("by_evidence_engine", {}), evidence_engine)
    add_query_set(sets, index.get("by_vector_feature", {}), vector_feature)

    if not sets:
        matches = set(index.get("by_profile", {}).keys())
    else:
        matches = set.intersection(*sets) if sets else set()

    profiles = [
        index.get("by_profile", {}).get(profile_key, {"profile_key": profile_key})
        for profile_key in sorted(matches)
    ]

    return {
        "success": True,
        "match_count": len(profiles),
        "profile_keys": [profile.get("profile_key") for profile in profiles],
        "profiles": profiles,
    }


def add_query_set(sets: list[set[str]], bucket: dict[str, list[str]], label: str | None) -> None:
    """Add matching profile set for query label."""
    if label is None:
        return

    normalized = normalize_label(label)
    sets.append(set(bucket.get(normalized, [])))


def normalize_label(value: Any) -> str:
    """Normalize label for stable indexing."""
    return (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )


def float_or_zero(value: Any) -> float:
    """Convert value to float or zero."""
    try:
        return float(value)
    except Exception:
        return 0.0
