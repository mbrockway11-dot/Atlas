
"""Population Intelligence v4 corpus builder."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.library.profile_library import list_saved_profiles
from atlas.population_v4.features import build_population_feature_record


CORPUS_VERSION = "4.0.0"


def build_population_v4_corpus(
    profile_keys: list[str] | None = None,
    *,
    limit: int | None = None,
    force: bool = False,
) -> dict[str, Any]:
    """Build v4 population corpus from saved canonical profiles."""
    selected_profiles = profile_keys or list_saved_profiles()

    if limit is not None:
        selected_profiles = selected_profiles[:limit]

    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for profile_key in selected_profiles:
        try:
            payload = compile_canonical_profile(profile_key, force=force)
            record = build_population_feature_record(profile_key, payload)
            records.append(record)

            if not payload.get("success"):
                errors.append(
                    {
                        "profile_key": profile_key,
                        "errors": payload.get("errors", []),
                    }
                )

        except Exception as exc:
            errors.append(
                {
                    "profile_key": profile_key,
                    "errors": [str(exc)],
                }
            )

    matrix = build_feature_matrix(records)

    return {
        "success": len(records) > 0,
        "version": CORPUS_VERSION,
        "profile_count": len(records),
        "requested_profile_count": len(selected_profiles),
        "error_count": len(errors),
        "errors": errors,
        "records": records,
        "matrix": matrix,
        "summary": build_corpus_summary(records, matrix, errors),
    }


def build_feature_matrix(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Build sparse feature matrix from feature records."""
    feature_names = sorted(
        {
            feature
            for record in records
            for feature in (record.get("vector", {}) or {}).keys()
        }
    )

    rows = []

    for record in records:
        vector = record.get("vector", {}) or {}
        rows.append(
            {
                "profile_key": record.get("profile_key"),
                "values": [
                    float(vector.get(feature, 0.0))
                    for feature in feature_names
                ],
            }
        )

    return {
        "feature_count": len(feature_names),
        "feature_names": feature_names,
        "rows": rows,
    }


def build_corpus_summary(
    records: list[dict[str, Any]],
    matrix: dict[str, Any],
    errors: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build compact corpus summary."""
    class_counts = count_summary_value(records, ["summary", "system_class"])
    architecture_counts = count_summary_value(records, ["summary", "primary_architecture"])

    theme_counts: dict[str, int] = {}

    for record in records:
        for theme in record.get("themes", []):
            theme_counts[theme] = theme_counts.get(theme, 0) + 1

    inference_counts: dict[str, int] = {}

    for record in records:
        for inference in record.get("inferences", []):
            inference_counts[inference] = inference_counts.get(inference, 0) + 1

    return {
        "profile_count": len(records),
        "feature_count": matrix.get("feature_count", 0),
        "error_count": len(errors),
        "system_classes": sort_counts(class_counts),
        "architectures": sort_counts(architecture_counts),
        "top_themes": sort_counts(theme_counts)[:20],
        "top_inferences": sort_counts(inference_counts)[:20],
    }


def count_summary_value(records: list[dict[str, Any]], path: list[str]) -> dict[str, int]:
    """Count nested record values."""
    counts: dict[str, int] = {}

    for record in records:
        value: Any = record

        for key in path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)

        label = str(value or "unresolved")

        if not label:
            label = "unresolved"

        counts[label] = counts.get(label, 0) + 1

    return counts


def sort_counts(counts: dict[str, int]) -> list[dict[str, Any]]:
    """Return sorted count rows."""
    return [
        {
            "label": label,
            "count": count,
        }
        for label, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    ]
