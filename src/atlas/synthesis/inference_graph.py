
"""Inference graph for Atlas Synthesis."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.synthesis.consensus import ConsensusReport
from atlas.synthesis.logic import CONFLICT_PAIRS, LOGIC_RULES, LogicRule


SYNTHESIS_INFERENCE_GRAPH_VERSION = "1.0"


@dataclass(frozen=True)
class InferenceNode:
    """Node in the synthesis inference graph."""

    node_id: str
    node_type: str
    label: str
    category: str
    confidence: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class InferenceEdge:
    """Directed relationship between inference graph nodes."""

    source: str
    target: str
    relation: str
    weight: float


@dataclass(frozen=True)
class InferenceGraph:
    """Graph of themes, conflicts, and derived inferences."""

    version: str
    profile_key: str
    nodes: tuple[InferenceNode, ...]
    edges: tuple[InferenceEdge, ...]
    applied_rules: tuple[str, ...]
    conflicts: tuple[tuple[str, str], ...]


def build_inference_graph(consensus: ConsensusReport) -> InferenceGraph:
    """Build inference graph from consensus themes."""
    themes = (
        list(consensus.dominant_themes)
        + list(consensus.strong_themes)
        + list(consensus.moderate_themes)
    )

    feature_map = {theme.feature: theme for theme in themes}

    nodes: list[InferenceNode] = []
    edges: list[InferenceEdge] = []
    applied_rules: list[str] = []

    for theme in themes:
        nodes.append(
            InferenceNode(
                node_id=f"theme:{theme.feature}",
                node_type="theme",
                label=theme.feature,
                category=theme.category,
                confidence=theme.consensus_score,
                evidence=tuple(theme.engines),
            )
        )

    for rule in LOGIC_RULES:
        matched = match_rule(rule, feature_map)

        if not matched:
            continue

        confidence = confidence_from_features(matched)
        inference_id = f"inference:{rule.inference}"

        nodes.append(
            InferenceNode(
                node_id=inference_id,
                node_type="inference",
                label=rule.inference,
                category=rule.category,
                confidence=confidence,
                evidence=tuple(theme.feature for theme in matched),
            )
        )

        applied_rules.append(rule.inference)

        for theme in matched:
            edges.append(
                InferenceEdge(
                    source=f"theme:{theme.feature}",
                    target=inference_id,
                    relation="supports",
                    weight=theme.consensus_score,
                )
            )

    conflicts = detect_conflicts(feature_map)

    for left, right in conflicts:
        edges.append(
            InferenceEdge(
                source=f"theme:{left}",
                target=f"theme:{right}",
                relation="tension",
                weight=0.5,
            )
        )

    return InferenceGraph(
        version=SYNTHESIS_INFERENCE_GRAPH_VERSION,
        profile_key=consensus.profile_key,
        nodes=tuple(nodes),
        edges=tuple(edges),
        applied_rules=tuple(applied_rules),
        conflicts=tuple(conflicts),
    )


def match_rule(rule: LogicRule, feature_map: dict[str, Any]) -> list[Any]:
    """Return matching themes for a rule."""
    if any(required not in feature_map for required in rule.required_all):
        return []

    matched = [
        feature_map[name]
        for name in rule.required_all
        if name in feature_map
    ]

    matched.extend(
        feature_map[name]
        for name in rule.required_any
        if name in feature_map and name not in rule.required_all
    )

    return matched if len(matched) >= 2 else []


def confidence_from_features(features: list[Any]) -> float:
    """Compute inference confidence from supporting features."""
    base = sum(float(feature.consensus_score) for feature in features) / max(len(features), 1)
    support_bonus = min(0.15, len(features) * 0.025)
    return round(min(1.0, base + support_bonus), 6)


def detect_conflicts(feature_map: dict[str, Any]) -> list[tuple[str, str]]:
    """Detect known feature tensions."""
    output = []

    for left, right in CONFLICT_PAIRS:
        if left in feature_map and right in feature_map:
            output.append((left, right))

    return output


def inference_graph_to_dict(graph: InferenceGraph) -> dict[str, Any]:
    """Convert graph to JSON-safe dict."""
    return {
        "version": graph.version,
        "profile_key": graph.profile_key,
        "nodes": [asdict(node) for node in graph.nodes],
        "edges": [asdict(edge) for edge in graph.edges],
        "applied_rules": list(graph.applied_rules),
        "conflicts": [list(item) for item in graph.conflicts],
    }
