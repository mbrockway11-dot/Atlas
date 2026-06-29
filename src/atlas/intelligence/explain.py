"""Explanation helpers for the Atlas Intelligence Engine."""

from __future__ import annotations

from atlas.intelligence.models import (
    ConfidenceSummary,
    IntelligenceSummary,
    PopulationPosition,
    StatisticalPosition,
    TopologyPosition,
)


def explain_population(position: PopulationPosition | None) -> str:
    """Explain population position in human-readable language."""
    if position is None:
        return "Population position is unavailable because the profile feature matrix could not be built."

    parts = []

    if position.nearest_neighbors:
        top = position.nearest_neighbors[0]
        name = top.get("name", "unknown")
        similarity = top.get("similarity")
        if similarity is not None:
            parts.append(f"The closest structural neighbor is {name} with similarity {similarity:.3f}.")
        else:
            parts.append(f"The closest structural neighbor is {name}.")

    if position.outlier_rank is not None and position.centroid_distance is not None:
        parts.append(
            f"The profile ranks #{position.outlier_rank} by distance from the population centroid "
            f"with centroid distance {position.centroid_distance:.3f}."
        )

    return " ".join(parts) if parts else "Population position was computed, but no strong neighbor or outlier signal was available."


def explain_statistics(position: StatisticalPosition | None) -> str:
    """Explain statistical position in human-readable language."""
    if position is None:
        return "Statistical position is unavailable because profile-level features could not be built."

    parts = []

    if position.cluster is not None:
        cluster = position.cluster.get("cluster")
        distance = position.cluster.get("distance_to_centroid")
        if distance is not None:
            parts.append(f"The profile is assigned to cluster {cluster} with centroid distance {distance:.3f}.")
        else:
            parts.append(f"The profile is assigned to cluster {cluster}.")

    if position.silhouette is not None:
        silhouette = position.silhouette.get("silhouette")
        if silhouette is not None:
            if silhouette >= 0.5:
                quality = "strong"
            elif silhouette >= 0.1:
                quality = "moderate"
            elif silhouette >= 0.0:
                quality = "weak"
            else:
                quality = "unstable"

            parts.append(f"Its silhouette score is {silhouette:.3f}, indicating {quality} cluster separation.")

    if position.principal_components is not None:
        pc_values = {
            key: value
            for key, value in position.principal_components.items()
            if key.startswith("pc")
        }
        if pc_values:
            rendered = ", ".join(f"{key.upper()}={value:.3f}" for key, value in pc_values.items())
            parts.append(f"Principal-component coordinates: {rendered}.")

    return " ".join(parts) if parts else "Statistical position was computed, but no cluster or component signal was available."


def explain_topology(position: TopologyPosition | None) -> str:
    """Explain topology position in human-readable language."""
    if position is None:
        return "Topology position is unavailable."

    if not position.available:
        return position.reason or "Topology position is unavailable."

    return (
        f"The profile has degree {position.degree}, weighted degree {position.weighted_degree:.3f}, "
        f"component {position.component}, and community {position.community}. "
        f"Closeness centrality is {position.closeness_centrality:.3f}."
    )


def explain_confidence(confidence: ConfidenceSummary) -> str:
    """Explain evidence confidence."""
    return (
        f"Confidence is {confidence.label} ({confidence.score:.2f}) based on "
        f"{confidence.evidence_count} evidence records."
    )


def build_intelligence_summary(
    population_position: PopulationPosition | None,
    statistical_position: StatisticalPosition | None,
    topology_position: TopologyPosition | None,
    confidence: ConfidenceSummary,
) -> IntelligenceSummary:
    """Build a readable Intelligence Engine summary."""
    population = explain_population(population_position)
    statistics = explain_statistics(statistical_position)
    topology = explain_topology(topology_position)
    confidence_text = explain_confidence(confidence)

    headline = f"Atlas Intelligence synthesis generated with {confidence.label} evidence confidence."

    return IntelligenceSummary(
        headline=headline,
        population=population,
        statistics=statistics,
        topology=topology,
        confidence=confidence_text,
    )