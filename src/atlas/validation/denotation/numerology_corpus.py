"""The numerology citation corpus — bibliographic evidence, not denotation.

A :class:`SourcePassage` is one quoted statement from one edition of one work,
tagged with what kind of statement it is and how far its authority reaches.
The corpus is evidence; it licenses nothing on its own. The compiler applies
frozen admissibility rules to turn it into dictionary entries.

Keeping these apart is what makes the dictionary reproducible: an
admissibility rule can be tightened or relaxed and the dictionary rebuilt
deterministically, without editing a single citation. It also means a passage
that fails admissibility today remains in the corpus as data, rather than
being silently dropped and forgotten.

This module contains **no numerological meanings**. It defines the shape a
citation must take.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Sequence


NUMEROLOGY_CORPUS_SCHEMA = "atlas.validation.denotation.numerology-corpus.v1"


class SemanticGranularity(str, Enum):
    """What kind of statement a passage makes.

    Only :attr:`DIRECT_DENOTATION` is eligible for 1E-A. The rest are recorded
    because they are real evidence about the tradition, but admitting them
    would drift the audit from expression concordance into inferred
    personality -- "4 signifies stability" is a denotation; "people with 4
    become reliable administrators" is a behavioral claim wearing one.
    """

    DIRECT_DENOTATION = "direct_denotation"
    ANALOGY = "analogy"
    CORRESPONDENCE = "correspondence"
    RECOMMENDATION = "recommendation"
    PREDICTION = "prediction"
    COMMENTARY = "commentary"


class SourceType(str, Enum):
    """How close a source sits to the tradition it reports."""

    PRIMARY = "primary"
    TRADITIONAL_COMMENTARY = "traditional_commentary"
    MODERN_COMMENTARY = "modern_commentary"
    SECONDARY_SYNTHESIS = "secondary_synthesis"


class AuthorityScope(str, Enum):
    """How far a passage's authority is claimed to reach."""

    TRADITION_WIDE = "tradition_wide"
    SCHOOL_SPECIFIC = "school_specific"
    AUTHOR_SPECIFIC = "author_specific"


class CorpusError(ValueError):
    """A source passage was recorded invalidly."""


@dataclass(frozen=True, slots=True)
class SourcePassage:
    """One quoted statement licensing (or failing to license) a denotation.

    Carries both the bibliography and the claim: which quantity and value the
    passage speaks about, and which ontology coordinate it asserts. The
    coordinate is what the *source* says, not what the audit concludes -- the
    compiler decides whether it is admissible and whether it agrees with
    others.
    """

    passage_id: str
    tradition: str
    author: str
    work: str
    edition: str
    locator: str
    quotation: str
    granularity: SemanticGranularity
    source_type: SourceType
    authority_scope: AuthorityScope
    quantity: str
    value: int
    axis: str
    coordinate: str
    polarity: str
    confidence: float

    def __post_init__(self) -> None:
        missing = [
            field
            for field in ("passage_id", "tradition", "author", "work",
                          "edition", "locator", "quotation")
            if not getattr(self, field)
        ]

        if missing:
            raise CorpusError(
                f"passage is missing bibliography: {', '.join(missing)}. A "
                "citation that cannot be located is not evidence."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise CorpusError("confidence must lie in [0, 1].")

    @property
    def denotation_key(self) -> tuple[str, str, int]:
        """Return the (tradition, quantity, value) this passage speaks to."""
        return (self.tradition, self.quantity, self.value)

    @property
    def asserted(self) -> tuple[str, str, str]:
        """Return the (axis, coordinate, polarity) the source asserts."""
        return (self.axis, self.coordinate, self.polarity)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "passage_id": self.passage_id,
            "tradition": self.tradition,
            "author": self.author,
            "work": self.work,
            "edition": self.edition,
            "locator": self.locator,
            "quotation": self.quotation,
            "granularity": self.granularity.value,
            "source_type": self.source_type.value,
            "authority_scope": self.authority_scope.value,
            "quantity": self.quantity,
            "value": self.value,
            "axis": self.axis,
            "coordinate": self.coordinate,
            "polarity": self.polarity,
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class NumerologyCorpus:
    """A set of source passages, hashed for reproducibility."""

    passages: tuple[SourcePassage, ...] = ()

    def __post_init__(self) -> None:
        seen: set[str] = set()

        for passage in self.passages:
            if passage.passage_id in seen:
                raise CorpusError(
                    f"duplicate passage_id {passage.passage_id!r}; each "
                    "citation must be individually addressable."
                )

            seen.add(passage.passage_id)

    def for_key(
        self, tradition: str, quantity: str, value: int
    ) -> list[SourcePassage]:
        """Return every passage speaking to one denotation key.

        Sorted by ``passage_id`` so compilation order never depends on
        corpus insertion order.
        """
        return sorted(
            (
                passage
                for passage in self.passages
                if passage.denotation_key == (tradition, quantity, value)
            ),
            key=lambda passage: passage.passage_id,
        )

    def keys(self) -> list[tuple[str, str, int]]:
        """Return every denotation key present, in deterministic order."""
        return sorted({passage.denotation_key for passage in self.passages})

    def corpus_hash(self) -> str:
        """Return a deterministic hash of every passage.

        Enters the artifact hash alongside the admissibility-rule hash, so a
        dictionary can always be traced to the exact evidence and rules that
        produced it.
        """
        payload = {
            "schema": NUMEROLOGY_CORPUS_SCHEMA,
            "passages": sorted(
                json.dumps(passage.to_dict(), sort_keys=True)
                for passage in self.passages
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
            "schema": NUMEROLOGY_CORPUS_SCHEMA,
            "hash": self.corpus_hash(),
            "passages": [passage.to_dict() for passage in self.passages],
        }


def build_corpus(passages: Sequence[SourcePassage]) -> NumerologyCorpus:
    """Assemble a corpus from passages, in deterministic order."""
    return NumerologyCorpus(
        passages=tuple(
            sorted(passages, key=lambda passage: passage.passage_id)
        )
    )
