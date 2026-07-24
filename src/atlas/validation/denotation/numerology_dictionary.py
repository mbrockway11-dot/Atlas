"""Numerology dictionary — source-licensed denotation, no subject.

This module defines *how* a numerology source is allowed to speak. It contains
no number meanings; those arrive in a separate commit, so architectural change
stays distinguishable from interpretive addition in the history.

A :class:`NumerologyDictionaryEntry` licenses a mapping from one (tradition,
quantity, value) key onto one ontology coordinate, and carries the source that
licenses it. The claim assembler applies an entry to an expression only by
**exact key** -- a generic "the number 4" cannot apply to every quantity, and
an entry for one reduction policy cannot apply to an expression reduced under
another.

Conflict is explicit. When admissible sources disagree, the disagreement is
represented; it is never reconciled informally, and it licenses no agreement.
Silence is preferable to forced consensus.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any

from atlas.validation.denotation.expressions import DenotationClaim
from atlas.validation.denotation.numerology_expression import (
    COMPUTABLE_QUANTITIES,
    NumerologyExpression,
    REDUCTION_POLICY,
)
from atlas.validation.denotation.ontology import (
    MAPPING_KINDS,
    POLARITIES,
    require_coordinate,
)


NUMEROLOGY_DICTIONARY_SCHEMA = "atlas.validation.denotation.numerology-dict.v1"


class ConflictVerdict(str, Enum):
    """How admissible sources stand on one key.

    Only ``consensus`` and ``source_specific`` license a claim. The rest
    produce silence -- which the policy prefers to a forced agreement.
    """

    CONSENSUS = "consensus"              # sources agree
    SOURCE_SPECIFIC = "source_specific"  # each source keeps its own mapping
    CONFLICTING = "conflicting"          # sources oppose; licenses nothing
    INSUFFICIENT = "insufficient"        # too little evidence
    NONE = "none"                        # no mapping


LICENSING_VERDICTS: frozenset[ConflictVerdict] = frozenset(
    {ConflictVerdict.CONSENSUS, ConflictVerdict.SOURCE_SPECIFIC}
)


class NumerologyDictionaryError(ValueError):
    """A dictionary entry or lookup was constructed invalidly."""


@dataclass(frozen=True, slots=True)
class SourceCitation:
    """The provenance of one denotation. No subject, no other system."""

    tradition: str
    source_id: str
    passage: str
    quantity_independent: bool = False

    def __post_init__(self) -> None:
        if not (self.tradition and self.source_id and self.passage):
            raise NumerologyDictionaryError(
                "A citation needs a tradition, a source id and a specific "
                "passage. Provenance that cannot be located is not "
                "provenance."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "tradition": self.tradition,
            "source_id": self.source_id,
            "passage": self.passage,
            "quantity_independent": self.quantity_independent,
        }


@dataclass(frozen=True, slots=True)
class NumerologyDictionaryEntry:
    """One source-licensed mapping from a numerology key to an ontology term.

    The key is (tradition, quantity, value, reduction_policy). The value maps
    to (axis, coordinate, polarity), licensed by a citation and a
    non-silent conflict verdict.
    """

    tradition: str
    quantity: str
    value: int
    reduction_policy: str
    axis: str
    coordinate: str
    polarity: str
    mapping_kind: str
    conflict_verdict: ConflictVerdict
    confidence: float
    citation: SourceCitation

    def __post_init__(self) -> None:
        require_coordinate(self.axis, self.coordinate)

        if self.polarity not in POLARITIES:
            raise NumerologyDictionaryError(
                f"{self.polarity!r} is not a valid polarity."
            )

        if self.mapping_kind not in MAPPING_KINDS:
            raise NumerologyDictionaryError(
                f"{self.mapping_kind!r} is not a valid mapping kind."
            )

        if not self.citation.quantity_independent and (
            self.quantity not in COMPUTABLE_QUANTITIES
        ):
            raise NumerologyDictionaryError(
                f"{self.quantity!r} is not a computable quantity. An entry "
                "may not address a construct the code does not produce."
            )

        if self.tradition != self.citation.tradition:
            raise NumerologyDictionaryError(
                "entry tradition and citation tradition disagree; a "
                "tradition boundary may not be crossed silently."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise NumerologyDictionaryError("confidence must lie in [0, 1].")

    @property
    def licenses_claim(self) -> bool:
        """Return whether this entry may produce a claim."""
        return self.conflict_verdict in LICENSING_VERDICTS

    def key(self) -> tuple[str, str, int, str]:
        """Return the exact licensing key."""
        return (self.tradition, self.quantity, self.value,
                self.reduction_policy)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "tradition": self.tradition,
            "quantity": self.quantity,
            "value": self.value,
            "reduction_policy": self.reduction_policy,
            "axis": self.axis,
            "coordinate": self.coordinate,
            "polarity": self.polarity,
            "mapping_kind": self.mapping_kind,
            "conflict_verdict": self.conflict_verdict.value,
            "licenses_claim": self.licenses_claim,
            "confidence": self.confidence,
            "citation": self.citation.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class NumerologyDictionary:
    """A frozen, single-tradition set of licensed entries."""

    tradition: str
    version: str
    entries: tuple[NumerologyDictionaryEntry, ...] = field(
        default_factory=tuple
    )

    def __post_init__(self) -> None:
        seen: set[tuple[str, str, int, str]] = set()

        for entry in self.entries:
            if entry.tradition != self.tradition:
                raise NumerologyDictionaryError(
                    f"entry tradition {entry.tradition!r} does not match "
                    f"dictionary tradition {self.tradition!r}."
                )

            key = entry.key()

            if key in seen:
                raise NumerologyDictionaryError(
                    f"duplicate key {key}; a conflict must be recorded as a "
                    "conflict verdict, not as two competing entries."
                )

            seen.add(key)

    def lookup(
        self, quantity: str, value: int, reduction_policy: str
    ) -> NumerologyDictionaryEntry | None:
        """Return the licensing entry for a key, or None for silence."""
        for entry in self.entries:
            if (
                entry.quantity == quantity
                and entry.value == value
                and entry.reduction_policy == reduction_policy
                and entry.licenses_claim
            ):
                return entry

        return None

    def dictionary_hash(self) -> str:
        """Return a deterministic hash of every entry.

        Enters the artifact hash: a change to a single mapping invalidates
        any concordance measured against the old dictionary.
        """
        payload = {
            "schema": NUMEROLOGY_DICTIONARY_SCHEMA,
            "tradition": self.tradition,
            "version": self.version,
            "entries": sorted(
                json.dumps(entry.to_dict(), sort_keys=True)
                for entry in self.entries
            ),
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": NUMEROLOGY_DICTIONARY_SCHEMA,
            "tradition": self.tradition,
            "version": self.version,
            "hash": self.dictionary_hash(),
            "entries": [entry.to_dict() for entry in self.entries],
        }


def claim_from_expression(
    expression: NumerologyExpression,
    dictionary: NumerologyDictionary,
    subject_id: str,
    *,
    temporal_scope: str = "natal",
) -> DenotationClaim | None:
    """Apply the dictionary to one expression, by exact key.

    Returns None -- silence -- when no licensing entry matches. Silence is a
    valid and common outcome: an unsupported quantity or value contributes
    nothing rather than an invented meaning.
    """
    if expression.reduction_policy != REDUCTION_POLICY:
        raise NumerologyDictionaryError(
            f"expression reduced under {expression.reduction_policy!r}, but "
            f"this build's policy is {REDUCTION_POLICY!r}; a mismatched "
            "reduction changes what the value denotes."
        )

    entry = dictionary.lookup(
        expression.quantity,
        expression.reduced_value,
        expression.reduction_policy,
    )

    if entry is None:
        return None

    return DenotationClaim(
        system="numerology",
        subject_id=subject_id,
        axis=entry.axis,
        value=entry.coordinate,
        polarity=entry.polarity,
        temporal_scope=temporal_scope,
        mapping_kind=entry.mapping_kind,
        confidence=entry.confidence,
        source_basis=(
            f"{entry.citation.tradition}:{entry.citation.source_id}:"
            f"{entry.quantity}={entry.value}"
        ),
    )
