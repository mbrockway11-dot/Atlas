"""Cluster interpretation utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PLANET_LABELS = {
    "saturn": "Saturn",
    "jupiter": "Jupiter",
    "mars": "Mars",
    "sun": "Sun",
    "venus": "Venus",
    "mercury": "Mercury",
    "moon": "Moon",
}

FEATURE_LABELS = {
    "node_coverage": "node coverage",
    "edge_coverage": "edge coverage",
    "density": "density",
    "entropy": "entropy",
    "axis_strength": "axis strength",
    "graph_coherence": "graph coherence",
    "core_survival_score": "core survival",
    "topology_stability": "topology stability",
    "attractor_stability": "attractor stability",
    "bridge_ratio": "bridge behavior",
    "articulation_ratio": "articulation",
    "loop_ratio": "looping",
    "hub_ratio": "hub concentration",
    "leaf_ratio": "terminal branching",
    "reduction_entropy": "reduction entropy",
    "node_survival_auc": "node persistence",
    "edge_survival_auc": "edge persistence",
    "structural_complexity_index": "structural complexity index",
    "structural_stability_index": "structural stability index",
}


def load_cluster_report(
    path: str | Path = "research/corpus/clusters.json",
) -> dict[str, Any]:
    """Load cluster report JSON."""
    report_path = Path(path)

    if not report_path.exists():
        raise FileNotFoundError(f"Cluster report not found: {report_path}")

    return json.loads(report_path.read_text(encoding="utf-8"))


def interpret_cluster_report(
    report: dict[str, Any],
) -> dict[str, Any]:
    """Interpret every cluster in a cluster report."""
    return {
        "cluster_count": report.get("cluster_count", 0),
        "feature_count": report.get("feature_count", 0),
        "clusters": [
            interpret_cluster(cluster)
            for cluster in report.get("clusters", [])
        ],
        "outliers": report.get("outliers", []),
    }


def interpret_cluster(cluster: dict[str, Any]) -> dict[str, Any]:
    """Interpret one cluster summary."""
    dominant_features = cluster.get("dominant_features", [])

    positive_features = [
        feature
        for feature in dominant_features
        if feature.get("centroid_value", 0.0) > 0
    ]

    negative_features = [
        feature
        for feature in dominant_features
        if feature.get("centroid_value", 0.0) < 0
    ]

    label = build_cluster_label(
        positive_features=positive_features,
        negative_features=negative_features,
        fallback_id=cluster.get("cluster_id", 0),
    )

    return {
        "cluster_id": cluster.get("cluster_id"),
        "label": label,
        "size": cluster.get("size", 0),
        "representative": cluster.get("representative"),
        "members": cluster.get("members", []),
        "dominant_positive_features": positive_features,
        "dominant_negative_features": negative_features,
        "summary_lines": build_cluster_summary_lines(
            cluster=cluster,
            positive_features=positive_features,
            negative_features=negative_features,
            label=label,
        ),
    }


def build_cluster_label(
    *,
    positive_features: list[dict[str, Any]],
    negative_features: list[dict[str, Any]],
    fallback_id: int,
) -> str:
    """Build deterministic cluster label from dominant features."""
    source_features = positive_features or negative_features

    if not source_features:
        return f"Cluster {fallback_id}"

    top_feature = source_features[0]["feature"]
    planet, feature = parse_feature_name(top_feature)

    if positive_features:
        if planet:
            return f"{planet} {feature.title()} Type"

        return f"{feature.title()} Type"

    if planet:
        return f"Low {planet} {feature.title()} Type"

    return f"Low {feature.title()} Type"


def build_cluster_summary_lines(
    *,
    cluster: dict[str, Any],
    positive_features: list[dict[str, Any]],
    negative_features: list[dict[str, Any]],
    label: str,
) -> list[str]:
    """Build readable cluster interpretation lines."""
    lines = [
        (
            f"{label} contains {cluster.get('size', 0)} profiles. "
            f"Representative profile: {cluster.get('representative')}."
        )
    ]

    if positive_features:
        lines.append(
            "Dominant elevated features: "
            + ", ".join(
                describe_feature(feature["feature"])
                for feature in positive_features[:3]
            )
            + "."
        )

    if negative_features:
        lines.append(
            "Dominant reduced features: "
            + ", ".join(
                describe_feature(feature["feature"])
                for feature in negative_features[:3]
            )
            + "."
        )

    members = cluster.get("members", [])

    if members:
        preview = ", ".join(members[:5])
        lines.append(f"Representative members include: {preview}.")

    return lines


def parse_feature_name(feature: str) -> tuple[str | None, str]:
    """Parse feature name into planet/global and readable feature label."""
    if feature.startswith("global_"):
        cleaned = feature.removeprefix("global_")
        cleaned = cleaned.removeprefix("mean_")
        return None, feature_label(cleaned)

    for prefix, planet in PLANET_LABELS.items():
        marker = f"{prefix}_"

        if feature.startswith(marker):
            cleaned = feature.removeprefix(marker)
            return planet, feature_label(cleaned)

    return None, feature_label(feature)


def feature_label(feature: str) -> str:
    """Convert feature key to readable label."""
    return FEATURE_LABELS.get(
        feature,
        feature.replace("_", " "),
    )


def describe_feature(feature: str) -> str:
    """Describe feature in readable form."""
    planet, label = parse_feature_name(feature)

    if planet:
        return f"{planet} {label}"

    return label


def cluster_interpretation_to_text(
    interpretation: dict[str, Any],
) -> str:
    """Render cluster interpretation as text."""
    lines = [
        "Atlas Cluster Interpretation",
        "=" * 56,
        f"Clusters: {interpretation['cluster_count']}",
        f"Features: {interpretation['feature_count']}",
        "",
    ]

    for cluster in interpretation["clusters"]:
        lines.append(f"Cluster {cluster['cluster_id']}: {cluster['label']}")
        lines.append("-" * 56)

        for line in cluster["summary_lines"]:
            lines.append(f"- {line}")

        lines.append("")

    lines.append("Top outliers:")

    for row in interpretation.get("outliers", [])[:10]:
        lines.append(
            f"- {row['name']}: cluster={row['cluster_id']} "
            f"distance={float(row['distance_to_centroid']):.4f}"
        )

    return "\n".join(lines)