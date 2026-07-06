
"""Declarative structural logic rules for Atlas Synthesis."""

from __future__ import annotations

from dataclasses import dataclass


SYNTHESIS_LOGIC_VERSION = "1.0"


@dataclass(frozen=True)
class LogicRule:
    """Declarative inference rule."""

    inference: str
    category: str
    required_any: tuple[str, ...]
    required_all: tuple[str, ...] = ()
    explanation: str = ""


LOGIC_RULES = (
    LogicRule(
        inference="compound_systems_builder",
        category="identity_architecture",
        required_any=(
            "persistent_architecture",
            "long_horizon_planning",
            "durable_system_construction",
            "constraint_pattern",
        ),
        required_all=("persistent_architecture",),
        explanation="Persistent structure combines with planning, constraint, or construction signals.",
    ),
    LogicRule(
        inference="cross_domain_synthesizer",
        category="cognitive_architecture",
        required_any=(
            "distributed_integration",
            "information_routing",
            "cross_domain_linking",
            "complexity_tolerance",
        ),
        required_all=("distributed_integration",),
        explanation="Distributed integration combines with information routing or complexity tolerance.",
    ),
    LogicRule(
        inference="symbolic_system_builder",
        category="symbolic_architecture",
        required_any=(
            "symbolic_coherence",
            "reduction_stability",
            "recursive_patterning",
            "pattern_compression",
            "abstraction_pattern",
        ),
        required_all=("symbolic_coherence",),
        explanation="Symbolic coherence combines with compression, recurrence, or abstraction.",
    ),
    LogicRule(
        inference="visible_structural_author",
        category="identity_architecture",
        required_any=(
            "visible_authorship",
            "expressive_catalysis",
            "message_propagation",
            "signal_amplification",
        ),
        required_all=("visible_authorship",),
        explanation="Visible authorship combines with expressive or propagating signals.",
    ),
    LogicRule(
        inference="stable_executor",
        category="emotional_architecture",
        required_any=(
            "internal_stabilization",
            "stability_seeking",
            "constraint_sensitive_execution",
            "structural_selectivity",
        ),
        required_all=("internal_stabilization",),
        explanation="Internal stabilization combines with execution discipline or selectivity.",
    ),
)


CONFLICT_PAIRS = (
    ("constraint_pattern", "activation_driven_action"),
    ("stability_seeking", "activation_driven_action"),
    ("structural_selectivity", "signal_amplification"),
    ("persistent_architecture", "innovation_pattern"),
)
