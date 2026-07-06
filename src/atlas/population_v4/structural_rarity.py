
"""Population Intelligence v4 structural rarity engine."""

from __future__ import annotations

from typing import Any


RARITY_VERSION = "4.0.0"


def build_structural_rarity_report(
    corpus: dict[str, Any],
    archetypes: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build structural rarity report for a population corpus."""
    records = corpus.get("records", []) or []
    profile_count = len(records)

    frequencies = build_frequency_tables(records, archetypes or {})
    rows = [
        build_profile_rarity_row(record, frequencies, profile_count, archetypes or {})
        for record in records
    ]

    rows.sort(key=lambda item: item.get("rarity_score", 0.0), reverse=True)

    return {
        "success": True,
        "version": RARITY_VERSION,
        "profile_count": profile_count,
        "rarity_rows": rows,
        "frequencies": frequencies,
        "summary": build_rarity_summary(rows),
    }


def build_frequency_tables(
    records: list[dict[str, Any]],
    archetypes: dict[str, Any],
) -> dict[str, Any]:
    """Build feature frequency tables."""
    archetype_assignments = archetypes.get("profile_assignments", {}) or {}

    frequencies = {
        "system_class": {},
        "architecture": {},
        "themes": {},
        "inferences": {},
        "tensions": {},
        "evidence_engines": {},
        "vector_features": {},
        "archetypes": {},
        "theme_pairs": {},
        "inference_pairs": {},
    }

    for record in records:
        profile_key = record.get("profile_key")
        summary = record.get("summary", {}) or {}
        evidence = record.get("evidence", {}) or {}

        increment(frequencies["system_class"], summary.get("system_class"))
        increment(frequencies["architecture"], summary.get("primary_architecture"))

        themes = record.get("themes", []) or []
        inferences = record.get("inferences", []) or []

        for theme in themes:
            increment(frequencies["themes"], theme)

        for inference in inferences:
            increment(frequencies["inferences"], inference)

        for tension in record.get("tensions", []) or []:
            increment(frequencies["tensions"], tension)

        for engine in evidence.get("engines", []) or []:
            increment(frequencies["evidence_engines"], engine)

        for feature in active_vector_features(record):
            increment(frequencies["vector_features"], feature)

        assignment = archetype_assignments.get(profile_key, {})
        increment(frequencies["archetypes"], assignment.get("archetype_name"))

        for pair in combinations_2(themes):
            increment(frequencies["theme_pairs"], " + ".join(pair))

        for pair in combinations_2(inferences):
            increment(frequencies["inference_pairs"], " + ".join(pair))

    return frequencies


def build_profile_rarity_row(
    record: dict[str, Any],
    frequencies: dict[str, Any],
    profile_count: int,
    archetypes: dict[str, Any],
) -> dict[str, Any]:
    """Build rarity score for one profile."""
    profile_key = record.get("profile_key")
    summary = record.get("summary", {}) or {}
    evidence = record.get("evidence", {}) or {}
    assignments = archetypes.get("profile_assignments", {}) or {}
    assignment = assignments.get(profile_key, {})

    rare_items = []

    rare_items.append(score_item("system_class", summary.get("system_class"), frequencies, profile_count))
    rare_items.append(score_item("architecture", summary.get("primary_architecture"), frequencies, profile_count))
    rare_items.append(score_item("archetypes", assignment.get("archetype_name"), frequencies, profile_count))

    for theme in record.get("themes", []) or []:
        rare_items.append(score_item("themes", theme, frequencies, profile_count))

    for inference in record.get("inferences", []) or []:
        rare_items.append(score_item("inferences", inference, frequencies, profile_count))

    for tension in record.get("tensions", []) or []:
        rare_items.append(score_item("tensions", tension, frequencies, profile_count))

    for engine in evidence.get("engines", []) or []:
        rare_items.append(score_item("evidence_engines", engine, frequencies, profile_count))

    for feature in active_vector_features(record):
        rare_items.append(score_item("vector_features", feature, frequencies, profile_count))

    for pair in combinations_2(record.get("themes", []) or []):
        rare_items.append(score_item("theme_pairs", " + ".join(pair), frequencies, profile_count))

    for pair in combinations_2(record.get("inferences", []) or []):
        rare_items.append(score_item("inference_pairs", " + ".join(pair), frequencies, profile_count))

    valid_items = [
        item for item in rare_items
        if item.get("label")
    ]

    if not valid_items:
        rarity_score = 0.0
    else:
        top_items = sorted(valid_items, key=lambda item: item.get("rarity", 0.0), reverse=True)[:12]
        rarity_score = sum(item.get("rarity", 0.0) for item in top_items) / len(top_items)

    return {
        "profile_key": profile_key,
        "rarity_score": round(rarity_score, 6),
        "label": rarity_label(rarity_score),
        "rarest_features": sorted(valid_items, key=lambda item: item.get("rarity", 0.0), reverse=True)[:20],
        "archetype": assignment,
        "summary": build_profile_rarity_summary(profile_key, rarity_score, valid_items),
    }


def score_item(
    category: str,
    label: Any,
    frequencies: dict[str, Any],
    profile_count: int,
) -> dict[str, Any]:
    """Score one feature's rarity."""
    normalized = normalize(label)

    if not normalized:
        return {
            "category": category,
            "label": "",
            "count": 0,
            "frequency": 0.0,
            "rarity": 0.0,
        }

    count = int((frequencies.get(category, {}) or {}).get(normalized, 0))
    frequency = count / max(1, profile_count)
    rarity = 1.0 - frequency

    return {
        "category": category,
        "label": normalized,
        "count": count,
        "frequency": round(frequency, 6),
        "rarity": round(rarity, 6),
    }


def active_vector_features(record: dict[str, Any]) -> list[str]:
    """Return active non-zero vector features."""
    vector = record.get("vector", {}) or {}

    output = []
    for feature, value in vector.items():
        try:
            numeric = float(value)
        except Exception:
            numeric = 0.0

        if numeric != 0.0:
            output.append(feature)

    return sorted(output)


def combinations_2(values: list[str]) -> list[tuple[str, str]]:
    """Return deterministic 2-combinations."""
    cleaned = sorted({normalize(value) for value in values if normalize(value)})
    pairs = []

    for left_index, left in enumerate(cleaned):
        for right in cleaned[left_index + 1:]:
            pairs.append((left, right))

    return pairs


def increment(bucket: dict[str, int], label: Any) -> None:
    """Increment normalized label count."""
    normalized = normalize(label)

    if not normalized:
        return

    bucket[normalized] = bucket.get(normalized, 0) + 1


def normalize(value: Any) -> str:
    """Normalize label."""
    label = (
        str(value or "")
        .strip()
        .lower()
        .replace(" ", "_")
        .replace("-", "_")
    )

    if label in {"", "none", "null", "unknown", "unresolved"}:
        return ""

    return label


def rarity_label(score: float) -> str:
    """Label rarity score."""
    if score >= 0.88:
        return "extreme_rarity"

    if score >= 0.75:
        return "high_rarity"

    if score >= 0.58:
        return "moderate_rarity"

    if score >= 0.35:
        return "mild_rarity"

    return "common_pattern"


def build_profile_rarity_summary(
    profile_key: str,
    rarity_score: float,
    items: list[dict[str, Any]],
) -> str:
    """Build profile rarity summary."""
    rarest = sorted(items, key=lambda item: item.get("rarity", 0.0), reverse=True)[:3]

    if not rarest:
        return f"{profile_key} does not have enough features for rarity scoring."

    labels = ", ".join(item.get("label", "") for item in rarest)

    return (
        f"{profile_key} has a {rarity_label(rarity_score)} signature. "
        f"The rarest contributing features are: {labels}."
    )


def build_rarity_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build rarity summary."""
    if not rows:
        return {
            "extreme_rarity_count": 0,
            "high_rarity_count": 0,
            "top_rare_profiles": [],
            "mean_rarity_score": 0.0,
        }

    return {
        "extreme_rarity_count": count_label(rows, "extreme_rarity"),
        "high_rarity_count": count_label(rows, "high_rarity"),
        "moderate_rarity_count": count_label(rows, "moderate_rarity"),
        "mild_rarity_count": count_label(rows, "mild_rarity"),
        "common_pattern_count": count_label(rows, "common_pattern"),
        "mean_rarity_score": round(
            sum(float(row.get("rarity_score") or 0.0) for row in rows) / len(rows),
            6,
        ),
        "top_rare_profiles": rows[:20],
    }


def count_label(rows: list[dict[str, Any]], label: str) -> int:
    """Count rows by label."""
    return sum(1 for row in rows if row.get("label") == label)
