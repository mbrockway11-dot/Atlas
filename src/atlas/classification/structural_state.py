"""Structural state classification."""

from dataclasses import dataclass

from atlas.signatures.topology_signature import TopologySignature


@dataclass(frozen=True)
class StructuralState:
    """Condition of the graph structure."""

    state: str
    reason: str


def classify_structural_state(signature: TopologySignature) -> StructuralState:
    """Classify the graph's structural state."""
    if signature.component_count > 2:
        return StructuralState(
            state="Fragmented",
            reason="More than two connected components indicate graph fragmentation.",
        )

    if signature.regulator >= 0.70 and signature.symmetry >= 0.60:
        return StructuralState(
            state="Stable",
            reason="High regulator score and symmetry indicate structural balance.",
        )

    if signature.driver >= 0.65 and signature.regulator < 0.40:
        return StructuralState(
            state="Transitional",
            reason="High driver with low regulator indicates active reorganization.",
        )

    if signature.amplifier >= 0.70 and signature.regulator < 0.45:
        return StructuralState(
            state="Emergent",
            reason="High amplification with weak regulation indicates new structure formation.",
        )

    if signature.edge_density >= 0.70 and signature.entropy < 0.35:
        return StructuralState(
            state="Saturated",
            reason="High density and low entropy indicate redundant structure.",
        )

    if signature.regulator < 0.35 and signature.symmetry < 0.35:
        return StructuralState(
            state="Fragile",
            reason="Low regulation and low symmetry indicate sensitivity to perturbation.",
        )

    return StructuralState(
        state="Adaptive",
        reason="The graph shows partial regulation with capacity for change.",
    )