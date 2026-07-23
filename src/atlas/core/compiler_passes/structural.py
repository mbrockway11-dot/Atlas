"""Master graph and deterministic feature-vector compiler pass."""

from __future__ import annotations

from atlas.core.canonical_structural_signature import StructuralMeasurementLayer
from atlas.structural_measurement import build_structural_measurement


def build_structural_measurement_layer(
    *,
    astronomy: dict,
    normalized_kamea_graphs: dict,
) -> StructuralMeasurementLayer:
    result = build_structural_measurement(astronomy, normalized_kamea_graphs)
    return StructuralMeasurementLayer(
        master_graph=result["master_graph"],
        topology_classification=result["topology_classification"],
        feature_vector=result["feature_vector"],
        similarity=result["similarity"],
        cluster_membership=result["cluster_membership"],
    )
