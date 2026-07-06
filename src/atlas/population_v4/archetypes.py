
"""Population Intelligence v4 archetype discovery."""

from __future__ import annotations

from typing import Any


ARCHETYPE_VERSION = "4.0.0"


def build_population_archetypes(cluster_report: dict[str, Any]) -> dict[str, Any]:
    """Build archetypes from Population v4 cluster report."""
    clusters = cluster_report.get("clustering", {}).get("clusters", []) or []

    archetypes = []

    for index, cluster in enumerate(clusters, start=1):
        archetypes.append(
            build_archetype(
                cluster,
                archetype_id=f"archetype_{index:03d}",
            )
        )

    return {
        "success": True,
        "version": ARCHETYPE_VERSION,
        "archetype_count": len(archetypes),
        "archetypes": archetypes,
        "profile_assignments": build_profile_assignments(archetypes),
        "summary": build_archetype_summary(archetypes),
    }


def build_archetype(cluster: dict[str, Any], *, archetype_id: str) -> dict[str, Any]:
    """Build one archetype from one cluster."""
    dominant_class = first_label(cluster.get("dominant_system_classes", []))
    dominant_architecture = first_label(cluster.get("dominant_architectures", []))
    dominant_theme = first_label(cluster.get("dominant_themes", []))
    dominant_inference = first_label(cluster.get("dominant_inferences", []))

    name = build_archetype_name(
        dominant_architecture,
        dominant_class,
        dominant_theme,
    )

    return {
        "archetype_id": archetype_id,
        "name": name,
        "cluster_id": cluster.get("cluster_id"),
        "member_count": cluster.get("member_count", 0),
        "members": cluster.get("members", []),
        "cohesion": cluster.get("cohesion", 0.0),
        "dominant_system_class": dominant_class,
        "dominant_architecture": dominant_architecture,
        "dominant_theme": dominant_theme,
        "dominant_inference": dominant_inference,
        "dominant_system_classes": cluster.get("dominant_system_classes", []),
        "dominant_architectures": cluster.get("dominant_architectures", []),
        "dominant_themes": cluster.get("dominant_themes", []),
        "dominant_inferences": cluster.get("dominant_inferences", []),
        "description": build_archetype_description(
            name,
            dominant_architecture,
            dominant_class,
            dominant_theme,
            dominant_inference,
            cluster.get("member_count", 0),
            cluster.get("cohesion", 0.0),
        ),
        "quality": archetype_quality(cluster),
    }


def build_archetype_name(
    architecture: str,
    system_class: str,
    theme: str,
) -> str:
    """Build readable archetype name."""
    architecture = clean_label(architecture)
    system_class = clean_label(system_class)
    theme = clean_label(theme)

    if architecture and architecture != "Unresolved":
        return architecture

    if system_class and system_class != "Unresolved":
        return system_class

    if theme and theme != "Unresolved":
        return f"{theme} Type"

    return "Unresolved Archetype"


def build_archetype_description(
    name: str,
    architecture: str,
    system_class: str,
    theme: str,
    inference: str,
    member_count: int,
    cohesion: float,
) -> str:
    """Build human-readable archetype description."""
    parts = [
        f"{name} represents a recurring structural family found in {member_count} profile(s).",
    ]

    if architecture and architecture != "unresolved":
        parts.append(f"Its dominant architecture is {clean_label(architecture)}.")

    if system_class and system_class != "unresolved":
        parts.append(f"Its dominant system class is {clean_label(system_class)}.")

    if theme and theme != "unresolved":
        parts.append(f"The strongest recurring theme is {clean_label(theme)}.")

    if inference and inference != "unresolved":
        parts.append(f"The dominant inference pattern is {clean_label(inference)}.")

    parts.append(f"Cluster cohesion is {float(cohesion):.3f}.")

    return " ".join(parts)


def archetype_quality(cluster: dict[str, Any]) -> str:
    """Label archetype quality."""
    member_count = int(cluster.get("member_count") or 0)
    cohesion = float(cluster.get("cohesion") or 0.0)

    if member_count <= 1:
        return "single_case_archetype"

    if cohesion >= 0.75:
        return "strong_archetype"

    if cohesion >= 0.55:
        return "emerging_archetype"

    return "loose_archetype"


def build_profile_assignments(archetypes: list[dict[str, Any]]) -> dict[str, Any]:
    """Assign every profile to its archetype."""
    assignments = {}

    for archetype in archetypes:
        for profile_key in archetype.get("members", []):
            assignments[profile_key] = {
                "archetype_id": archetype.get("archetype_id"),
                "archetype_name": archetype.get("name"),
                "cluster_id": archetype.get("cluster_id"),
                "quality": archetype.get("quality"),
                "cohesion": archetype.get("cohesion"),
            }

    return assignments


def build_archetype_summary(archetypes: list[dict[str, Any]]) -> dict[str, Any]:
    """Build archetype summary."""
    return {
        "archetype_count": len(archetypes),
        "strong_archetype_count": count_quality(archetypes, "strong_archetype"),
        "emerging_archetype_count": count_quality(archetypes, "emerging_archetype"),
        "single_case_archetype_count": count_quality(archetypes, "single_case_archetype"),
        "largest_archetypes": sorted(
            [
                {
                    "archetype_id": item.get("archetype_id"),
                    "name": item.get("name"),
                    "member_count": item.get("member_count"),
                    "quality": item.get("quality"),
                    "cohesion": item.get("cohesion"),
                }
                for item in archetypes
            ],
            key=lambda item: (-int(item.get("member_count") or 0), item.get("name") or ""),
        )[:20],
    }


def count_quality(archetypes: list[dict[str, Any]], quality: str) -> int:
    """Count archetypes by quality."""
    return sum(1 for item in archetypes if item.get("quality") == quality)


def first_label(rows: list[dict[str, Any]]) -> str:
    """Return first label from dominant count rows."""
    if not rows:
        return "unresolved"

    return str(rows[0].get("label") or "unresolved")


def clean_label(value: Any) -> str:
    """Clean normalized labels for display."""
    return (
        str(value or "unresolved")
        .replace("_", " ")
        .replace("-", " ")
        .strip()
        .title()
    )
