
"""Structural reasoning engine for Atlas Synthesis."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.synthesis.consensus import ConsensusReport
from atlas.synthesis.fusion import FusedTheme, fused_theme_to_dict


SYNTHESIS_REASONING_VERSION = "1.0"


@dataclass(frozen=True)
class StructuralInference:
    """One reasoned conclusion derived from fused evidence."""

    inference: str
    category: str
    confidence: float
    supporting_features: tuple[str, ...]
    supporting_theme_count: int
    explanation: str


@dataclass(frozen=True)
class ReasoningReport:
    """Reasoned conclusions from synthesis consensus."""

    version: str
    profile_key: str
    inference_count: int
    inferences: tuple[StructuralInference, ...]
    strongest_inferences: tuple[StructuralInference, ...]


def build_reasoning_report(consensus: ConsensusReport) -> ReasoningReport:
    """Build reasoned synthesis conclusions from consensus themes."""
    themes = (
        list(consensus.dominant_themes)
        + list(consensus.strong_themes)
        + list(consensus.moderate_themes)
    )

    by_feature = {theme.feature: theme for theme in themes}
    inferences: list[StructuralInference] = []

    rules = [
        persistent_builder_rule,
        systems_thinker_rule,
        visible_author_rule,
        symbolic_compression_rule,
        stabilizing_architecture_rule,
        catalytic_expression_rule,
        transformation_rule,
    ]

    for rule in rules:
        result = rule(by_feature)
        if result:
            inferences.append(result)

    inferences.sort(key=lambda item: item.confidence, reverse=True)

    return ReasoningReport(
        version=SYNTHESIS_REASONING_VERSION,
        profile_key=consensus.profile_key,
        inference_count=len(inferences),
        inferences=tuple(inferences),
        strongest_inferences=tuple(inferences[:8]),
    )


def persistent_builder_rule(themes: dict[str, FusedTheme]) -> StructuralInference | None:
    """Infer long-term system construction."""
    features = pick(
        themes,
        [
            "persistent_architecture",
            "long_horizon_planning",
            "durable_system_construction",
            "constraint_pattern",
            "continuity_preservation",
        ],
    )

    if len(features) < 2:
        return None

    return make_inference(
        inference="long_term_system_builder",
        category="identity_architecture",
        features=features,
        explanation=(
            "Multiple evidence streams indicate that this profile organizes effort around "
            "durable structures, continuity, delayed outcomes, and systems whose value compounds over time."
        ),
    )


def systems_thinker_rule(themes: dict[str, FusedTheme]) -> StructuralInference | None:
    """Infer cross-domain systems thinking."""
    features = pick(
        themes,
        [
            "distributed_integration",
            "information_routing",
            "complexity_tolerance",
            "cross_domain_linking",
            "parallel_context_management",
            "high_graph_complexity",
        ],
    )

    if len(features) < 2:
        return None

    return make_inference(
        inference="cross_domain_systems_thinker",
        category="cognitive_architecture",
        features=features,
        explanation=(
            "The profile shows evidence for handling multiple frameworks, routing information across domains, "
            "and tolerating dense conceptual environments."
        ),
    )


def visible_author_rule(themes: dict[str, FusedTheme]) -> StructuralInference | None:
    """Infer visible authorship."""
    features = pick(
        themes,
        [
            "visible_authorship",
            "expressive_catalysis",
            "signal_amplification",
            "message_propagation",
        ],
    )

    if len(features) < 2:
        return None

    return make_inference(
        inference="visible_authorship_through_structure",
        category="identity_architecture",
        features=features,
        explanation=(
            "Evidence indicates that expression is not merely performative; it becomes a vehicle for making "
            "internal structures visible, transmissible, and socially activating."
        ),
    )


def symbolic_compression_rule(themes: dict[str, FusedTheme]) -> StructuralInference | None:
    """Infer symbolic compression and pattern encoding."""
    features = pick(
        themes,
        [
            "symbolic_coherence",
            "reduction_stability",
            "recursive_patterning",
            "pattern_compression",
            "abstraction_pattern",
            "prime_structure",
        ],
    )

    if len(features) < 2:
        return None

    return make_inference(
        inference="symbolic_pattern_compression",
        category="symbolic_architecture",
        features=features,
        explanation=(
            "The symbolic layers converge around compression, recurrence, abstraction, and stable reductions, "
            "suggesting a tendency to encode complex meaning into reusable symbolic structures."
        ),
    )


def stabilizing_architecture_rule(themes: dict[str, FusedTheme]) -> StructuralInference | None:
    """Infer stabilizing behavior."""
    features = pick(
        themes,
        [
            "internal_stabilization",
            "stability_seeking",
            "constraint_sensitive_execution",
            "structural_selectivity",
        ],
    )

    if len(features) < 2:
        return None

    return make_inference(
        inference="stability_oriented_execution",
        category="emotional_architecture",
        features=features,
        explanation=(
            "The profile appears to regulate action through stability, selectivity, and awareness of constraint, "
            "favoring coherent execution over chaotic activation."
        ),
    )


def catalytic_expression_rule(themes: dict[str, FusedTheme]) -> StructuralInference | None:
    """Infer catalytic expressive behavior."""
    features = pick(
        themes,
        [
            "expressive_catalysis",
            "activation_driven_action",
            "energy_allocation",
            "signal_amplification",
        ],
    )

    if len(features) < 2:
        return None

    return make_inference(
        inference="activation_through_expression",
        category="motivational_architecture",
        features=features,
        explanation=(
            "The evidence suggests that action becomes strongest when expression, activation, and signal movement align."
        ),
    )


def transformation_rule(themes: dict[str, FusedTheme]) -> StructuralInference | None:
    """Infer transformational development pattern."""
    features = pick(
        themes,
        [
            "transformation_pattern",
            "iterative_refinement",
            "recursive_patterning",
            "abstraction_pattern",
        ],
    )

    if len(features) < 2:
        return None

    return make_inference(
        inference="recursive_transformation_path",
        category="growth_path",
        features=features,
        explanation=(
            "Growth appears to occur through repeated symbolic passes, recursive learning, abstraction, "
            "and eventual structural transformation."
        ),
    )


def pick(themes: dict[str, FusedTheme], names: list[str]) -> list[FusedTheme]:
    """Pick themes by name."""
    return [
        themes[name]
        for name in names
        if name in themes
    ]


def make_inference(
    *,
    inference: str,
    category: str,
    features: list[FusedTheme],
    explanation: str,
) -> StructuralInference:
    """Create one inference from supporting themes."""
    confidence = sum(theme.consensus_score for theme in features) / max(len(features), 1)
    support_bonus = min(0.12, len(features) * 0.025)
    confidence = min(1.0, confidence + support_bonus)

    return StructuralInference(
        inference=inference,
        category=category,
        confidence=round(confidence, 6),
        supporting_features=tuple(theme.feature for theme in features),
        supporting_theme_count=len(features),
        explanation=explanation,
    )


def reasoning_report_to_dict(report: ReasoningReport) -> dict[str, Any]:
    """Convert reasoning report to JSON-safe dict."""
    return {
        "version": report.version,
        "profile_key": report.profile_key,
        "inference_count": report.inference_count,
        "strongest_inferences": [
            inference_to_dict(item)
            for item in report.strongest_inferences
        ],
        "inferences": [
            inference_to_dict(item)
            for item in report.inferences
        ],
    }


def inference_to_dict(inference: StructuralInference) -> dict[str, Any]:
    """Convert inference to dict."""
    data = asdict(inference)
    data["supporting_features"] = list(inference.supporting_features)
    return data
