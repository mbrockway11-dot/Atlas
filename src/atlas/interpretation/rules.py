"""Deterministic interpretation rules for Atlas signatures."""

from atlas.signatures.topology_signature import TopologySignature


def interpret_driver(signature: TopologySignature) -> str:
    """Interpret driver score."""
    if signature.driver >= 0.7:
        return "High driver: strong outward directional force."
    if signature.driver >= 0.35:
        return "Medium driver: moderate outward movement."
    return "Low driver: force is distributed rather than sharply directed."


def interpret_amplifier(signature: TopologySignature) -> str:
    """Interpret amplifier score."""
    if signature.amplifier >= 0.7:
        return "High amplifier: repetition and reinforcement dominate the field."
    if signature.amplifier >= 0.35:
        return "Medium amplifier: repeated structure is present but not overwhelming."
    return "Low amplifier: the topology is more varied than repetitive."


def interpret_regulator(signature: TopologySignature) -> str:
    """Interpret regulator score."""
    if signature.regulator >= 0.7:
        return "High regulator: strong containment, balance, and stabilizing structure."
    if signature.regulator >= 0.35:
        return "Medium regulator: partial balance with some structural containment."
    return "Low regulator: weak containment and low structural balance."


def interpret_pattern(signature: TopologySignature) -> str:
    """Interpret dominant pattern."""
    pattern_map = {
        "radiating": "Radiating pattern: influence emerges from central nodes and distributes outward.",
        "looping": "Looping pattern: the structure reinforces itself through repeated circulation.",
        "reciprocal": "Reciprocal pattern: feedback and mutual exchange are structurally emphasized.",
        "dense": "Dense pattern: many connections are compressed into a compact structure.",
        "linear": "Linear pattern: flow proceeds through sequence, chain, and progression.",
        "isolated": "Isolated pattern: nodes exist with little or no active relationship.",
        "empty": "Empty pattern: no active topology is present.",
    }

    return pattern_map.get(
        signature.dominant_pattern,
        f"Unclassified pattern: {signature.dominant_pattern}.",
    )


def interpret_motif(signature: TopologySignature) -> str:
    """Interpret dominant motif."""
    motif_map = {
        "chains": "Chain motif: sequential passage and transmission are emphasized.",
        "hubs": "Hub motif: central organizing points dominate the structure.",
        "loops": "Loop motif: recursive reinforcement and repetition are emphasized.",
        "bridges": "Bridge motif: connective passages between regions are emphasized.",
        "dead_ends": "Dead-end motif: flow terminates at certain nodes.",
        "reciprocal_pairs": "Reciprocal-pair motif: paired feedback relationships dominate.",
        "isolated_nodes": "Isolated-node motif: disconnected points are structurally emphasized.",
        "none": "No dominant motif detected.",
    }

    return motif_map.get(
        signature.dominant_motif,
        f"Unclassified motif: {signature.dominant_motif}.",
    )


def interpret_signature(signature: TopologySignature) -> list[str]:
    """Return deterministic interpretation lines for one signature."""
    return [
        interpret_driver(signature),
        interpret_amplifier(signature),
        interpret_regulator(signature),
        interpret_pattern(signature),
        interpret_motif(signature),
    ]