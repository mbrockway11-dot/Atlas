"""Atlas Intelligence Engine.

This module is orchestration only.

It connects existing Atlas systems into one canonical payload. It does not
implement new PCA, similarity, topology, clustering, z-score, or graph logic.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.intelligence.explain import build_intelligence_summary
from atlas.intelligence.models import (
    AtlasIntelligencePayload,
    ConfidenceSummary,
    EvidenceRecord,
    IntelligenceEngineConfig,
    PopulationPosition,
    ProfileReference,
    ProvenanceRecord,
    StatisticalPosition,
    TopologyPosition,
)
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.research.matrix import build_profile_matrix_rows
from atlas.research.population_topology import build_population_topology_graph
from atlas.research.session import build_research_session
from atlas.research.statistical import (
    kmeans_clusters,
    principal_components,
    silhouette_scores,
)
from atlas.research.validation import (
    build_profile_feature_matrix,
    nearest_neighbors,
    outlier_scores,
)


def load_acf(profile_dir: Path) -> dict[str, Any]:
    """Load a profile ACF JSON file."""
    acf_path = profile_dir / "profile.acf.json"

    if not acf_path.exists():
        raise FileNotFoundError(f"Missing profile.acf.json: {acf_path}")

    return json.loads(acf_path.read_text(encoding="utf-8"))


def load_population_matrix() -> pd.DataFrame:
    """Load all saved profiles into the row-level Atlas research matrix."""
    rows: list[dict[str, Any]] = []

    for profile_key in list_saved_profiles():
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

        if not acf_path.exists():
            continue

        try:
            acf = json.loads(acf_path.read_text(encoding="utf-8"))
            rows.extend(build_profile_matrix_rows(acf))
        except Exception:
            continue

    return pd.DataFrame(rows)


def resolve_profile_name(profile_dir: Path, acf: dict[str, Any]) -> str:
    """Resolve the display/profile name used by the population matrix."""
    for key in ["name", "full_name", "display_name"]:
        value = acf.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    identity = acf.get("identity")
    if isinstance(identity, dict):
        for key in ["name", "full_name", "display_name"]:
            value = identity.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return profile_dir.name


def build_population_position(
    profile_name: str,
    profile_features: pd.DataFrame,
    config: IntelligenceEngineConfig,
) -> PopulationPosition:
    """Build nearest-neighbor and outlier position."""
    neighbors = nearest_neighbors(
        profile_features,
        profile_name,
        limit=config.neighbor_limit,
        metric=config.similarity_metric,
    )

    outliers = outlier_scores(profile_features)

    outlier_rank = None
    centroid_distance = None

    if not outliers.empty and profile_name in outliers["name"].tolist():
        match = outliers.reset_index()
        row = match.loc[match["name"] == profile_name].iloc[0]
        outlier_rank = int(row["index"]) + 1
        centroid_distance = float(row["centroid_distance"])

    return PopulationPosition(
        nearest_neighbors=neighbors,
        outlier_rank=outlier_rank,
        centroid_distance=centroid_distance,
    )


def build_statistical_position(
    profile_name: str,
    profile_features: pd.DataFrame,
    config: IntelligenceEngineConfig,
) -> StatisticalPosition:
    """Build PCA, cluster, and silhouette position."""
    pca = principal_components(
        profile_features,
        n_components=config.principal_components,
    )

    clusters = kmeans_clusters(
        profile_features,
        k=min(config.cluster_count, len(profile_features)),
    )

    silhouettes = silhouette_scores(profile_features, clusters)

    cluster_payload = None
    silhouette_payload = None
    pca_payload = None

    if not clusters.empty and profile_name in clusters["name"].tolist():
        row = clusters.loc[clusters["name"] == profile_name].iloc[0]
        cluster_payload = {
            "cluster": int(row["cluster"]),
            "distance_to_centroid": float(row["distance_to_centroid"]),
        }

    if not silhouettes.empty and profile_name in silhouettes["name"].tolist():
        row = silhouettes.loc[silhouettes["name"] == profile_name].iloc[0]
        silhouette_payload = {
            "cluster": int(row["cluster"]),
            "silhouette": float(row["silhouette"]),
        }

    if pca.get("available"):
        for row in pca["coordinates"]:
            if row["name"] == profile_name:
                pca_payload = row
                break

    return StatisticalPosition(
        cluster=cluster_payload,
        silhouette=silhouette_payload,
        principal_components=pca_payload,
        explained_variance_ratio=pca.get("explained_variance_ratio", []),
    )


def build_topology_position(
    profile_name: str,
    profile_features: pd.DataFrame,
    config: IntelligenceEngineConfig,
) -> TopologyPosition:
    """Build population topology role for one profile."""
    graph = build_population_topology_graph(
        profile_features,
        threshold=config.topology_threshold,
        top_k=config.topology_top_k,
        metric=config.similarity_metric,
    )

    node = graph.get("nodes", {}).get(profile_name)

    if not node:
        return TopologyPosition(
            available=False,
            reason="Profile not found in population topology graph.",
        )

    return TopologyPosition(
        available=True,
        degree=int(node.get("degree", 0)),
        weighted_degree=float(node.get("weighted_degree", 0.0)),
        component=node.get("component"),
        community=node.get("community"),
        degree_centrality=float(node.get("degree_centrality", 0.0)),
        weighted_degree_centrality=float(
            node.get("weighted_degree_centrality", 0.0)
        ),
        closeness_centrality=float(node.get("closeness_centrality", 0.0)),
    )


def build_evidence(
    population_position: PopulationPosition,
    statistical_position: StatisticalPosition,
    topology_position: TopologyPosition,
) -> list[EvidenceRecord]:
    """Assemble evidence records from existing subsystem outputs."""
    evidence: list[EvidenceRecord] = []

    if population_position.nearest_neighbors:
        top_neighbor = population_position.nearest_neighbors[0]
        evidence.append(
            EvidenceRecord(
                claim="nearest_neighbor_available",
                source="population_validation.nearest_neighbors",
                value=top_neighbor,
                weight=0.25,
            )
        )

    if population_position.centroid_distance is not None:
        evidence.append(
            EvidenceRecord(
                claim="population_outlier_position_available",
                source="population_validation.outlier_scores",
                value={
                    "outlier_rank": population_position.outlier_rank,
                    "centroid_distance": population_position.centroid_distance,
                },
                weight=0.25,
            )
        )

    if statistical_position.cluster is not None:
        evidence.append(
            EvidenceRecord(
                claim="cluster_assignment_available",
                source="statistical_intelligence.kmeans_clusters",
                value=statistical_position.cluster,
                weight=0.20,
            )
        )

    if statistical_position.silhouette is not None:
        evidence.append(
            EvidenceRecord(
                claim="cluster_coherence_available",
                source="statistical_intelligence.silhouette_scores",
                value=statistical_position.silhouette,
                weight=0.15,
            )
        )

    if topology_position.available:
        evidence.append(
            EvidenceRecord(
                claim="topology_role_available",
                source="population_topology.build_population_topology_graph",
                value={
                    "degree": topology_position.degree,
                    "weighted_degree": topology_position.weighted_degree,
                    "component": topology_position.component,
                    "community": topology_position.community,
                    "degree_centrality": topology_position.degree_centrality,
                    "weighted_degree_centrality": topology_position.weighted_degree_centrality,
                    "closeness_centrality": topology_position.closeness_centrality,
                },
                weight=0.15,
            )
        )

    return evidence


def build_confidence(evidence: list[EvidenceRecord]) -> ConfidenceSummary:
    """Build conservative confidence summary from evidence coverage."""
    total_weight = sum(float(item.weight) for item in evidence)
    score = max(0.0, min(1.0, total_weight))

    if score >= 0.85:
        label = "high"
    elif score >= 0.55:
        label = "moderate"
    elif score > 0.0:
        label = "low"
    else:
        label = "unavailable"

    return ConfidenceSummary(
        score=score,
        label=label,
        evidence_count=len(evidence),
    )


def build_provenance() -> list[ProvenanceRecord]:
    """Build static provenance records for the Intelligence Engine payload."""
    return [
        ProvenanceRecord(
            section="research_session",
            source="atlas.research.session.build_research_session",
            role="Builds the canonical research session for the selected profile.",
        ),
        ProvenanceRecord(
            section="population_position",
            source="atlas.research.validation.nearest_neighbors / outlier_scores",
            role="Provides nearest-neighbor and centroid-distance evidence.",
        ),
        ProvenanceRecord(
            section="statistical_position",
            source="atlas.research.statistical",
            role="Provides PCA coordinates, cluster assignment, and silhouette score.",
        ),
        ProvenanceRecord(
            section="topology_position",
            source="atlas.research.population_topology.build_population_topology_graph",
            role="Provides population graph role, community, component, and centrality.",
        ),
        ProvenanceRecord(
            section="summary",
            source="atlas.intelligence.explain",
            role="Converts evidence-backed metrics into readable summaries.",
        ),
        ProvenanceRecord(
            section="confidence",
            source="atlas.intelligence.engine.build_confidence",
            role="Summarizes available evidence coverage into conservative confidence.",
        ),
    ]


def build_intelligence_model(
    profile_dir: str | Path,
    config: IntelligenceEngineConfig | None = None,
) -> AtlasIntelligencePayload:
    """Build the canonical structured Intelligence Engine model."""
    config = config or IntelligenceEngineConfig()
    profile_path = Path(profile_dir)

    acf = load_acf(profile_path)
    profile_name = resolve_profile_name(profile_path, acf)

    research_session = build_research_session(
        profile_path,
        transit_date=config.transit_date,
    )

    population_matrix = load_population_matrix()
    profile_features = build_profile_feature_matrix(population_matrix)

    profile_ref = ProfileReference(
        name=profile_name,
        profile_dir=str(profile_path),
    )

    provenance = build_provenance()

    if profile_features.empty:
        confidence = ConfidenceSummary(
            score=0.0,
            label="unavailable",
            evidence_count=0,
        )
        summary = build_intelligence_summary(
            population_position=None,
            statistical_position=None,
            topology_position=None,
            confidence=confidence,
        )

        return AtlasIntelligencePayload(
            profile=profile_ref,
            research_session=research_session,
            population_position=None,
            statistical_position=None,
            topology_position=None,
            evidence=[],
            confidence=confidence,
            summary=summary,
            provenance=provenance,
            warnings=[
                "Population feature matrix is empty; population intelligence unavailable."
            ],
        )

    population_position = build_population_position(
        profile_name,
        profile_features,
        config,
    )

    statistical_position = build_statistical_position(
        profile_name,
        profile_features,
        config,
    )

    topology_position = build_topology_position(
        profile_name,
        profile_features,
        config,
    )

    evidence = build_evidence(
        population_position,
        statistical_position,
        topology_position,
    )

    confidence = build_confidence(evidence)

    summary = build_intelligence_summary(
        population_position=population_position,
        statistical_position=statistical_position,
        topology_position=topology_position,
        confidence=confidence,
    )

    return AtlasIntelligencePayload(
        profile=profile_ref,
        research_session=research_session,
        population_position=population_position,
        statistical_position=statistical_position,
        topology_position=topology_position,
        evidence=evidence,
        confidence=confidence,
        summary=summary,
        provenance=provenance,
        warnings=[],
    )


def build_intelligence_payload(
    profile_dir: str | Path,
    config: IntelligenceEngineConfig | None = None,
) -> dict[str, Any]:
    """Build a JSON-safe Atlas intelligence payload."""
    return build_intelligence_model(profile_dir, config=config).to_dict()