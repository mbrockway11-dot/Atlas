"""The numerology citation corpus — bibliographic evidence, not denotation.

Editions are first-class, so different editions and traditions coexist without
blending, and a passage always resolves to a specific printing. A
:class:`SourcePassage` is one transcribed statement from one edition, tagged
with what kind of statement it is and — crucially — whether the construct the
source names is actually the construct the code computes.

That last field is what stops a shared phrase from doing the work of evidence:

    A passage cannot license a code quantity merely because both use the
    words "life path".

The corpus is evidence and licenses nothing on its own. The compiler applies
frozen admissibility rules to derive dictionary entries from it, so rules can
change and the dictionary rebuild deterministically without editing a single
citation.

This module contains **no numerological meanings**. It defines the shape a
citation must take.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from typing import Any, Sequence

from atlas.validation.denotation.numerology_tradition import (
    SourceRole,
    VerificationStatus,
)


NUMEROLOGY_CORPUS_SCHEMA = "atlas.validation.denotation.numerology-corpus.v2"


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


class ConstructEquivalence(str, Enum):
    """Whether the source's construct is the code's construct.

    The decisive field. Modern numerology's vocabulary is not standardized,
    so two authors may use one phrase for different computations, and the
    implementation's names may resemble a source's terminology without
    matching its arithmetic.
    """

    EXACT = "exact"
    COMPUTATIONALLY_EQUIVALENT = "computationally_equivalent"
    PARTIALLY_EQUIVALENT = "partially_equivalent"
    TERMINOLOGY_ONLY = "terminology_only"
    NOT_EQUIVALENT = "not_equivalent"
    UNRESOLVED = "unresolved"


class CorpusError(ValueError):
    """A source edition or passage was recorded invalidly."""


@dataclass(frozen=True, slots=True)
class SourceEdition:
    """One specific printing, addressable and independently checkable."""

    edition_id: str
    author: str
    title: str
    edition: str
    publisher: str
    publication_year: int
    copyright_year: int | None
    role: SourceRole
    source_type: SourceType
    authority_scope: AuthorityScope
    verification_status: VerificationStatus
    # Notes on how the bibliography was checked, and any discrepancy found.
    verification_note: str = ""
    # Hash of the scan or copy transcribed from, so a later transcription can
    # be shown to come from the same physical text.
    scan_hash: str = ""

    def __post_init__(self) -> None:
        missing = [
            field
            for field in ("edition_id", "author", "title", "edition",
                          "publisher")
            if not getattr(self, field)
        ]

        if missing:
            raise CorpusError(
                f"edition is missing bibliography: {', '.join(missing)}. A "
                "citation that cannot be located is not evidence."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "edition_id": self.edition_id,
            "author": self.author,
            "title": self.title,
            "edition": self.edition,
            "publisher": self.publisher,
            "publication_year": self.publication_year,
            "copyright_year": self.copyright_year,
            "role": self.role.value,
            "source_type": self.source_type.value,
            "authority_scope": self.authority_scope.value,
            "verification_status": self.verification_status.value,
            "verification_note": self.verification_note,
            "scan_hash": self.scan_hash,
        }


@dataclass(frozen=True, slots=True)
class SourcePassage:
    """One transcribed statement from one edition.

    Carries the locator, the verbatim excerpt, both the source's and the
    code's name for the quantity, and the verdict on whether those are the
    same construct.
    """

    passage_id: str
    edition_id: str
    page: str
    chapter_or_heading: str
    verbatim_excerpt: str
    quantity_as_named_by_source: str
    quantity_as_named_by_code: str
    construct_equivalence: ConstructEquivalence
    value: int
    granularity: SemanticGranularity
    proposed_axis: str
    proposed_coordinate: str
    polarity: str
    confidence: float
    transcriber: str

    def __post_init__(self) -> None:
        missing = [
            field
            for field in ("passage_id", "edition_id", "page",
                          "verbatim_excerpt", "transcriber")
            if not getattr(self, field)
        ]

        if missing:
            raise CorpusError(
                f"passage is missing provenance: {', '.join(missing)}. An "
                "untranscribed or unlocated passage is not evidence."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise CorpusError("confidence must lie in [0, 1].")

    @property
    def asserted(self) -> tuple[str, str, str]:
        """Return the (axis, coordinate, polarity) the source asserts."""
        return (self.proposed_axis, self.proposed_coordinate, self.polarity)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "passage_id": self.passage_id,
            "edition_id": self.edition_id,
            "page": self.page,
            "chapter_or_heading": self.chapter_or_heading,
            "verbatim_excerpt": self.verbatim_excerpt,
            "quantity_as_named_by_source": self.quantity_as_named_by_source,
            "quantity_as_named_by_code": self.quantity_as_named_by_code,
            "construct_equivalence": self.construct_equivalence.value,
            "value": self.value,
            "granularity": self.granularity.value,
            "proposed_axis": self.proposed_axis,
            "proposed_coordinate": self.proposed_coordinate,
            "polarity": self.polarity,
            "confidence": self.confidence,
            "transcriber": self.transcriber,
        }


@dataclass(frozen=True, slots=True)
class NumerologyCorpus:
    """Editions plus the passages transcribed from them, hashed."""

    corpus_id: str
    editions: tuple[SourceEdition, ...] = ()
    passages: tuple[SourcePassage, ...] = ()

    def __post_init__(self) -> None:
        edition_ids = {edition.edition_id for edition in self.editions}

        if len(edition_ids) != len(self.editions):
            raise CorpusError("duplicate edition_id in corpus.")

        seen: set[str] = set()

        for passage in self.passages:
            if passage.passage_id in seen:
                raise CorpusError(
                    f"duplicate passage_id {passage.passage_id!r}; each "
                    "citation must be individually addressable."
                )

            if passage.edition_id not in edition_ids:
                raise CorpusError(
                    f"passage {passage.passage_id!r} cites unknown edition "
                    f"{passage.edition_id!r}."
                )

            seen.add(passage.passage_id)

    def edition(self, edition_id: str) -> SourceEdition:
        """Return one edition by id."""
        for edition in self.editions:
            if edition.edition_id == edition_id:
                return edition

        raise CorpusError(f"unknown edition {edition_id!r}.")

    def passages_for_role(self, role: SourceRole) -> list[SourcePassage]:
        """Return passages from editions playing one role, in id order.

        Strata never mix: compiling the canonical dictionary must not be able
        to reach a historical precursor's passages.
        """
        allowed = {
            edition.edition_id
            for edition in self.editions
            if edition.role is role
        }

        return sorted(
            (p for p in self.passages if p.edition_id in allowed),
            key=lambda passage: passage.passage_id,
        )

    def keys_for_role(self, role: SourceRole) -> list[tuple[str, int]]:
        """Return (code quantity, value) keys present within one stratum."""
        return sorted(
            {
                (p.quantity_as_named_by_code, p.value)
                for p in self.passages_for_role(role)
            }
        )

    def corpus_hash(self) -> str:
        """Return a deterministic hash of every edition and passage."""
        payload = {
            "schema": NUMEROLOGY_CORPUS_SCHEMA,
            "corpus_id": self.corpus_id,
            "editions": sorted(
                json.dumps(edition.to_dict(), sort_keys=True)
                for edition in self.editions
            ),
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
            "corpus_id": self.corpus_id,
            "hash": self.corpus_hash(),
            "editions": [edition.to_dict() for edition in self.editions],
            "passages": [passage.to_dict() for passage in self.passages],
            "passage_count": len(self.passages),
        }


def build_corpus(
    corpus_id: str,
    editions: Sequence[SourceEdition],
    passages: Sequence[SourcePassage] = (),
) -> NumerologyCorpus:
    """Assemble a corpus in deterministic order."""
    return NumerologyCorpus(
        corpus_id=corpus_id,
        editions=tuple(sorted(editions, key=lambda e: e.edition_id)),
        passages=tuple(sorted(passages, key=lambda p: p.passage_id)),
    )
