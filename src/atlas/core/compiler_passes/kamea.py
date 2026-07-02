"""Kamea/topology pass for the CSS compiler."""

from __future__ import annotations

from typing import Any

from atlas.core.canonical_structural_signature import KameaLayer
from atlas.core.compiler_passes.utils import extract_acf, extract_essence_graph, first_dict


def build_kamea_layer(*, profile_payload: dict[str, Any]) -> KameaLayer:
    """Build CSS Kamea/topology layer from ACF/profile payload."""
    acf = extract_acf(profile_payload)
    essence_graph = extract_essence_graph(profile_payload)

    identity_graph = first_dict(
        acf.get("identity_graph"),
        essence_graph.get("graph"),
        profile_payload.get("identity_graph"),
        profile_payload.get("graph"),
    )

    planetary_matrix = first_dict(
        acf.get("planetary_matrix"),
        profile_payload.get("planetary_matrix"),
    )

    essence = first_dict(
        acf.get("essence"),
        essence_graph.get("signature"),
        profile_payload.get("essence"),
        profile_payload.get("signature"),
    )

    invariant_analysis = first_dict(
        acf.get("invariant_analysis"),
        profile_payload.get("invariant_analysis"),
    )

    metadata = first_dict(acf.get("metadata"), profile_payload.get("metadata"))

    fingerprint = first_dict(
        essence.get("fingerprint") if isinstance(essence, dict) else None,
        identity_graph.get("fingerprint") if isinstance(identity_graph, dict) else None,
        metadata.get("fingerprint") if isinstance(metadata, dict) else None,
    )

    return KameaLayer(
        topology={**identity_graph, "topology_status": "compiled_from_acf"}
        if identity_graph
        else {},
        planetary_graphs={**planetary_matrix, "planetary_status": "compiled_from_acf"}
        if planetary_matrix
        else {},
        resonance={**essence, "resonance_status": "compiled_from_acf"}
        if essence
        else {},
        graph_metrics={**invariant_analysis, "metrics_status": "compiled_from_acf"}
        if invariant_analysis
        else {},
        fingerprint=fingerprint,
    )