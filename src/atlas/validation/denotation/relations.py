"""The relation algebra for cross-system denotational agreement.

Agreement is a relation, not a binary. Two systems may describe different
roles in one configuration -- strong constraint, repeated effort, delayed
materialization -- that are compatible without being identical. Reducing that
to match/no-match would let a broad word like "change" or "power" make nearly
every system look mutually confirming.

The comparison is always axis-local and reference-gated. Two claims are
compared only if they are about the same reference class; otherwise the
relation is ``not_comparable`` and no semantic verdict is even attempted. This
is the referential-agreement check from the milestone, enforced before any
symbolic reasoning can run.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from atlas.validation.denotation.expressions import DenotationClaim
from atlas.validation.denotation.ontology import are_compatible


class Relation(str, Enum):
    """How two denotation claims stand to each other on one axis."""

    EQUIVALENT = "equivalent"          # same value, same polarity
    COMPATIBLE = "compatible"          # same value, one polarity neutral
    COMPLEMENTARY = "complementary"    # frozen compatible pair of values
    CONTRADICTORY = "contradictory"    # same value, opposed polarity
    UNRELATED = "unrelated"            # different axes, or unlicensed values
    NOT_COMPARABLE = "not_comparable"  # different reference class


# Which temporal scopes may be compared at all. Enduring tendencies and acute
# activations denote different objects, so comparing them directly is a
# reference error, not a disagreement. Any pair outside this set is
# not_comparable until an explicit enduring<->temporary bridge is defined.
COMPARABLE_SCOPES: frozenset[tuple[str, str]] = frozenset(
    {
        ("natal", "natal"),
        ("event", "event"),
        ("transit", "transit"),
        ("natal", "developmental"),
        ("developmental", "natal"),
        ("developmental", "developmental"),
    }
)

# Relations that count as positive agreement when the concordance rate is
# scored. complementary is included deliberately: different-but-consistent
# roles are the denotational agreement the milestone is looking for, distinct
# from mere identity.
AGREEING_RELATIONS: frozenset[Relation] = frozenset(
    {Relation.EQUIVALENT, Relation.COMPATIBLE, Relation.COMPLEMENTARY}
)


def scopes_comparable(left_scope: str, right_scope: str) -> bool:
    """Return whether two temporal scopes may be compared at all."""
    return (left_scope, right_scope) in COMPARABLE_SCOPES


@dataclass(frozen=True, slots=True)
class RelationVerdict:
    """The relation between two claims, with the reason it was reached."""

    left_system: str
    right_system: str
    axis: str
    relation: Relation
    reason: str

    @property
    def agrees(self) -> bool:
        """Return whether this verdict counts as agreement."""
        return self.relation in AGREEING_RELATIONS

    @property
    def comparable(self) -> bool:
        """Return whether the two claims were comparable at all."""
        return self.relation is not Relation.NOT_COMPARABLE

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "left_system": self.left_system,
            "right_system": self.right_system,
            "axis": self.axis,
            "relation": self.relation.value,
            "agrees": self.agrees,
            "reason": self.reason,
        }


def relate(left: DenotationClaim, right: DenotationClaim) -> RelationVerdict:
    """Return the relation between two claims.

    Reference gate first, then axis, then value, then polarity. The order is
    the milestone's interpretive-load order in miniature: the cheapest,
    least symbolic distinction that can settle the pair is applied first.
    """
    # Referential agreement: are they even about the same kind of object?
    if not scopes_comparable(left.temporal_scope, right.temporal_scope):
        return RelationVerdict(
            left.system,
            right.system,
            left.axis,
            Relation.NOT_COMPARABLE,
            f"temporal scopes {left.temporal_scope!r} and "
            f"{right.temporal_scope!r} denote different reference objects; "
            "no enduring<->temporary bridge is defined.",
        )

    if left.axis != right.axis:
        return RelationVerdict(
            left.system,
            right.system,
            left.axis,
            Relation.UNRELATED,
            f"claims lie on different axes ({left.axis!r} vs {right.axis!r}); "
            "no shared semantic content.",
        )

    if left.value != right.value:
        # Different coordinates agree only when a frozen table licenses them
        # as compatible-but-distinct roles. Absent that, they are unrelated:
        # this is the guard that stops a broad vocabulary from making every
        # pairing confirm every other.
        if are_compatible(left.axis, left.value, right.value):
            return RelationVerdict(
                left.system,
                right.system,
                left.axis,
                Relation.COMPLEMENTARY,
                f"{left.value!r} and {right.value!r} are a frozen compatible "
                "pair: different roles in one configuration.",
            )

        return RelationVerdict(
            left.system,
            right.system,
            left.axis,
            Relation.UNRELATED,
            f"same axis, different coordinates ({left.value!r} vs "
            f"{right.value!r}) with no frozen compatibility; no shared "
            "denotation.",
        )

    # Same axis and same coordinate: polarity decides agreement vs conflict.
    if _opposed(left.polarity, right.polarity):
        return RelationVerdict(
            left.system,
            right.system,
            left.axis,
            Relation.CONTRADICTORY,
            f"same denotation {left.value!r} with opposed polarity "
            f"({left.polarity!r} vs {right.polarity!r}).",
        )

    if left.polarity == right.polarity:
        return RelationVerdict(
            left.system,
            right.system,
            left.axis,
            Relation.EQUIVALENT,
            f"same denotation {left.value!r} and polarity "
            f"{left.polarity!r}.",
        )

    return RelationVerdict(
        left.system,
        right.system,
        left.axis,
        Relation.COMPATIBLE,
        f"same denotation {left.value!r}; one polarity neutral, so "
        "consistent without being identical.",
    )


def _opposed(left_polarity: str, right_polarity: str) -> bool:
    """Return whether two polarities are directly opposed."""
    return {left_polarity, right_polarity} == {"positive", "negative"}
