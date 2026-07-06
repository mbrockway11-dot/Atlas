
"""Population Intelligence v4 population dynamics.

Runs Dynamic Resonance v2 across a corpus to discover:
- dynamic neighbors
- shared attractor families
- recovery-response families
- dynamic field clusters
"""

from __future__ import annotations

from typing import Any

from atlas.dynamics import build_dynamic_resonance_v2


POPULATION_DYNAMICS_VERSION = "4.0.0"


def build_population_dynamics_report(
    corpus: dict[str, Any],
    *,
    limit: int | None = None,
    min_resonance: float = 0.0,
) -> dict[str, Any]:
    """Build population-level dynamic resonance report."""
    records = corpus.get("records", []) or []

    if limit is not None:
        records = records[:limit]

    comparisons = []

    for left_index, left in enumerate(records):
        for right in records[left_index + 1:]:
            left_payload = record_payload(left)
            right_payload = record_payload(right)

            resonance = build_dynamic_resonance_v2(left_payload, right_payload)

            if float(resonance.get("dynamic_resonance") or 0.0) < min_resonance:
                continue

            comparisons.append(resonance)

    neighbors = build_dynamic_neighbors(records, comparisons)
    families = build_dynamic_families(records)
    attractor_families = build_attractor_families(records)

    return {
        "success": True,
        "version": POPULATION_DYNAMICS_VERSION,
        "profile_count": len(records),
        "comparison_count": len(comparisons),
        "comparisons": sorted(
            comparisons,
            key=lambda item: item.get("dynamic_resonance", 0.0),
            reverse=True,
        ),
        "dynamic_neighbors": neighbors,
        "dynamic_families": families,
        "attractor_families": attractor_families,
        "summary": build_population_dynamics_summary(comparisons, neighbors, families),
    }


def build_dynamic_neighbors(
    records: list[dict[str, Any]],
    comparisons: list[dict[str, Any]],
    *,
    limit: int = 5,
) -> dict[str, Any]:
    """Build nearest dynamic neighbors per profile."""
    profile_keys = [
        record.get("profile_key")
        for record in records
        if record.get("profile_key")
    ]

    buckets = {key: [] for key in profile_keys}

    for item in comparisons:
        left = item.get("left_profile_key")
        right = item.get("right_profile_key")

        if left in buckets:
            buckets[left].append(
                {
                    "profile_key": right,
                    "dynamic_resonance": item.get("dynamic_resonance"),
                    "label": item.get("label"),
                    "component_scores": item.get("component_scores", {}),
                    "shared": item.get("shared", {}),
                }
            )

        if right in buckets:
            buckets[right].append(
                {
                    "profile_key": left,
                    "dynamic_resonance": item.get("dynamic_resonance"),
                    "label": item.get("label"),
                    "component_scores": item.get("component_scores", {}),
                    "shared": item.get("shared", {}),
                }
            )

    reports = {}

    for key, rows in buckets.items():
        rows.sort(key=lambda item: item.get("dynamic_resonance", 0.0), reverse=True)
        reports[key] = {
            "profile_key": key,
            "neighbor_count": len(rows),
            "neighbors": rows[:limit],
            "top_neighbor": rows[0] if rows else None,
        }

    return {
        "profile_count": len(reports),
        "reports": reports,
    }


def build_dynamic_families(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Group profiles by response/stability family."""
    families: dict[str, list[str]] = {}

    for record in records:
        key = family_key(record)
        profile_key = record.get("profile_key")

        if not profile_key:
            continue

        families.setdefault(key, []).append(profile_key)

    rows = [
        {
            "family": key,
            "count": len(values),
            "profiles": sorted(values),
        }
        for key, values in families.items()
    ]

    rows.sort(key=lambda item: (-item["count"], item["family"]))

    return {
        "family_count": len(rows),
        "families": rows,
    }


def build_attractor_families(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Group profiles by dominant attractor nodes."""
    buckets: dict[str, list[str]] = {}

    for record in records:
        dynamics = record.get("payload", {}).get("dynamics", {}) or record.get("dynamics", {}) or {}
        field = dynamics.get("identity_field", {}) or {}
        profile_key = record.get("profile_key")

        if not profile_key:
            continue

        attractors = [
            str(item.get("node"))
            for item in field.get("dominant_attractors", [])[:3]
            if item.get("node") is not None
        ]

        key = "+".join(attractors) if attractors else "no_dominant_attractor"

        buckets.setdefault(key, []).append(profile_key)

    rows = [
        {
            "attractor_family": key,
            "count": len(values),
            "profiles": sorted(values),
        }
        for key, values in buckets.items()
    ]

    rows.sort(key=lambda item: (-item["count"], item["attractor_family"]))

    return {
        "attractor_family_count": len(rows),
        "families": rows,
    }


def record_payload(record: dict[str, Any]) -> dict[str, Any]:
    """Return canonical-like payload from population record."""
    payload = record.get("payload")

    if isinstance(payload, dict):
        return payload

    return {
        "profile_key": record.get("profile_key"),
        "dynamics": record.get("dynamics", {}),
        "systems_report": record.get("systems_report", {}),
        "kamea": record.get("kamea", {}),
    }


def family_key(record: dict[str, Any]) -> str:
    """Build dynamic family key."""
    dynamics = record.get("payload", {}).get("dynamics", {}) or record.get("dynamics", {}) or {}
    profile = dynamics.get("dynamic_profile", {}) or {}
    prediction = dynamics.get("prediction", {}) or {}

    flow = profile.get("flow_stability") or "unknown_flow"
    phase = profile.get("phase_complexity") or "unknown_phase"
    response = prediction.get("likely_dynamic_response") or "unknown_response"

    return f"{flow}::{phase}::{response}"


def build_population_dynamics_summary(
    comparisons: list[dict[str, Any]],
    neighbors: dict[str, Any],
    families: dict[str, Any],
) -> dict[str, Any]:
    """Build compact population dynamics summary."""
    values = [
        float(item.get("dynamic_resonance") or 0.0)
        for item in comparisons
    ]

    if values:
        mean_resonance = sum(values) / len(values)
        max_resonance = max(values)
    else:
        mean_resonance = 0.0
        max_resonance = 0.0

    return {
        "mean_dynamic_resonance": round(mean_resonance, 6),
        "max_dynamic_resonance": round(max_resonance, 6),
        "high_resonance_pair_count": sum(1 for value in values if value >= 0.82),
        "moderate_resonance_pair_count": sum(1 for value in values if value >= 0.62),
        "dynamic_family_count": families.get("family_count", 0),
        "profile_neighbor_reports": neighbors.get("profile_count", 0),
    }
