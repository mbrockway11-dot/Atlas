"""Topological expression classification."""

from dataclasses import dataclass

from atlas.signatures.topology_signature import TopologySignature


@dataclass(frozen=True)
class TopologicalExpression:
    """How the topology expresses its function."""

    expression: str
    reason: str


def classify_topological_expression(
    signature: TopologySignature,
) -> TopologicalExpression:
    """Classify the topology expression layer."""
    pattern = signature.dominant_pattern
    motif = signature.dominant_motif

    if motif == "hubs":
        return TopologicalExpression(
            expression="Hub-Dominant",
            reason="Dominant motif is hubs, indicating centralized influence.",
        )

    if pattern == "radiating":
        return TopologicalExpression(
            expression="Radiating",
            reason="Dominant pattern radiates outward from active centers.",
        )

    if motif == "chains":
        return TopologicalExpression(
            expression="Linear-Sequential",
            reason="Dominant motif is chains, indicating sequential transmission.",
        )

    if motif == "loops":
        return TopologicalExpression(
            expression="Cyclic",
            reason="Dominant motif is loops, indicating recursive reinforcement.",
        )

    if motif == "bridges":
        return TopologicalExpression(
            expression="Bridge-Connector",
            reason="Dominant motif is bridges, indicating connective passage between regions.",
        )

    if signature.component_count > 1:
        return TopologicalExpression(
            expression="Fragmented",
            reason="Multiple connected components indicate separated graph regions.",
        )

    if signature.symmetry >= 0.70 and signature.edge_density >= 0.40:
        return TopologicalExpression(
            expression="Distributed",
            reason="High symmetry and density indicate distributed connectivity.",
        )

    if signature.compression_level == "high":
        return TopologicalExpression(
            expression="Convergent",
            reason="High compression indicates repeated convergence into limited structure.",
        )

    return TopologicalExpression(
        expression="Mixed",
        reason="No single expression dominates the topology.",
    )