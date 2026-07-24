"""System expressions and their translation into the shared ontology.

Independence is enforced here, structurally. A :class:`SystemExpression` is
the frozen output of one system for one subject, and it records which system
produced it. A :class:`DenotationClaim` is that expression translated onto one
ontology axis, and it may be built only from the expression plus a frozen
dictionary -- never from another system's output, and never from the subject's
outcome.

The type system carries the guarantee the milestone depends on: nothing in a
claim's construction has access to the thing it would need in order to cheat.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from atlas.validation.denotation.ontology import (
    MAPPING_KINDS,
    POLARITIES,
    ONTOLOGY_SCHEMA,
    ontology_hash,
    require_coordinate,
)


EXPRESSION_SCHEMA = "atlas.validation.denotation.expression.v1"

# The systems admitted to the audit. Frozen: a system not on this list has no
# validated generator, so it cannot contribute an expression.
SYSTEMS: tuple[str, ...] = ("numerology", "gematria", "kamea", "vedic")


class ExpressionError(ValueError):
    """A system expression or claim was constructed invalidly."""


@dataclass(frozen=True, slots=True)
class SystemExpression:
    """One system's frozen output for one subject.

    Deliberately opaque: the audit never inspects ``content`` directly. It is
    carried so a claim can cite its own basis, and so a control generator can
    shuffle or mismatch whole expressions without reaching inside them.
    """

    system: str
    subject_id: str
    # The system's raw output. Shape is the system's own business; the audit
    # treats it as evidence a dictionary reads, not as data it interprets.
    content: Mapping[str, Any]
    # Which reference object this expression is about, so that referential
    # comparability can be checked before any semantic comparison.
    reference_class: str

    def __post_init__(self) -> None:
        if self.system not in SYSTEMS:
            raise ExpressionError(
                f"{self.system!r} is not an admitted system. Admitted: "
                f"{', '.join(SYSTEMS)}."
            )


@dataclass(frozen=True, slots=True)
class DenotationClaim:
    """One system's expression, translated onto one ontology axis.

    Built only from a :class:`SystemExpression` and a frozen dictionary. The
    ``source_basis`` names the dictionary entry that licensed it, so any claim
    can be audited back to a rule that existed before the subject did.
    """

    system: str
    subject_id: str
    axis: str
    value: str
    polarity: str
    temporal_scope: str
    mapping_kind: str
    confidence: float
    source_basis: str

    def __post_init__(self) -> None:
        require_coordinate(self.axis, self.value)

        if self.polarity not in POLARITIES:
            raise ExpressionError(
                f"{self.polarity!r} is not a valid polarity."
            )

        if self.mapping_kind not in MAPPING_KINDS:
            raise ExpressionError(
                f"{self.mapping_kind!r} is not a valid mapping kind."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise ExpressionError("confidence must lie in [0, 1].")

        if not self.source_basis:
            raise ExpressionError(
                "A claim must cite the frozen dictionary entry that licensed "
                "it. An unsourced claim is indistinguishable from an "
                "after-the-fact interpretation."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "system": self.system,
            "subject_id": self.subject_id,
            "axis": self.axis,
            "value": self.value,
            "polarity": self.polarity,
            "temporal_scope": self.temporal_scope,
            "mapping_kind": self.mapping_kind,
            "confidence": self.confidence,
            "source_basis": self.source_basis,
        }


@dataclass(frozen=True, slots=True)
class SubjectDenotation:
    """Every system's claims for one subject, keyed by system.

    The unit a concordance audit consumes. Assembling it does not compare
    anything -- it only gathers independently generated claims, so the
    comparison step downstream cannot influence generation.
    """

    subject_id: str
    ontology_hash: str
    claims_by_system: dict[str, tuple[DenotationClaim, ...]] = field(
        default_factory=dict
    )

    def claims_on(self, axis: str) -> list[DenotationClaim]:
        """Return every system's claims on one axis."""
        return [
            claim
            for claims in self.claims_by_system.values()
            for claim in claims
            if claim.axis == axis
        ]

    def systems_present(self) -> tuple[str, ...]:
        """Return the systems that contributed any claim."""
        return tuple(sorted(self.claims_by_system))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": EXPRESSION_SCHEMA,
            "subject_id": self.subject_id,
            "ontology_hash": self.ontology_hash,
            "claims_by_system": {
                system: [claim.to_dict() for claim in claims]
                for system, claims in self.claims_by_system.items()
            },
        }


def assemble_subject(
    subject_id: str,
    claims_by_system: Mapping[str, list[DenotationClaim]],
) -> SubjectDenotation:
    """Gather independently generated claims for one subject.

    Validates that every claim belongs to the subject and to the system it is
    filed under -- a claim mis-filed across systems would silently break the
    independence the audit rests on.
    """
    assembled: dict[str, tuple[DenotationClaim, ...]] = {}

    for system, claims in claims_by_system.items():
        for claim in claims:
            if claim.system != system:
                raise ExpressionError(
                    f"claim from {claim.system!r} filed under {system!r}; "
                    "systems must stay independent."
                )

            if claim.subject_id != subject_id:
                raise ExpressionError(
                    f"claim for {claim.subject_id!r} filed under subject "
                    f"{subject_id!r}."
                )

        assembled[system] = tuple(claims)

    return SubjectDenotation(
        subject_id=subject_id,
        ontology_hash=ontology_hash(),
        claims_by_system=assembled,
    )
