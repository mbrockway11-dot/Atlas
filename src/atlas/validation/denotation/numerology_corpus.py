"""The numerology citation corpus — transcribed evidence, not denotation.

A passage is transcribed from a **source copy**, not from an abstract edition,
and carries the printed-page locator as primary with the scan page as a
secondary reproducibility field. A passage may not cite a merely declared
manifestation: without a copy in hand there is nothing to have transcribed.

Transcription is doubled. Two independent transcribers produce the excerpt and
their normalized hashes are compared, so a disagreement about a word is
visible rather than silently resolved by whoever typed last.

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

from atlas.validation.denotation.numerology_bibliography import (
    AuthorityScope,
    Manifestation,
    SourceCopy,
    SourceType,
    Work,
    excerpt_hash,
)
from atlas.validation.denotation.numerology_tradition import SourceRole


NUMEROLOGY_CORPUS_SCHEMA = "atlas.validation.denotation.numerology-corpus.v3"


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


class ConstructEquivalence(str, Enum):
    """Whether the source's construct is the code's construct.

    Modern numerology's vocabulary is not standardized, so two authors may use
    one phrase for different computations, and the implementation's names may
    resemble a source's terminology without matching its arithmetic.
    """

    EXACT = "exact"
    COMPUTATIONALLY_EQUIVALENT = "computationally_equivalent"
    PARTIALLY_EQUIVALENT = "partially_equivalent"
    TERMINOLOGY_ONLY = "terminology_only"
    NOT_EQUIVALENT = "not_equivalent"
    UNRESOLVED = "unresolved"


class SilenceReason(str, Enum):
    """Why a key produced no denotation.

    Distinguishing these is the point of the completeness report: "we have no
    copy of the book" and "the book says something we cannot use" are very
    different states, and a bare empty dictionary conflates them.
    """

    NO_SOURCE_COPY = "no_source_copy"
    NO_MATCHING_CONSTRUCT = "no_matching_construct"
    NO_DIRECT_DENOTATION = "no_direct_denotation"
    CONFLICTING_DENOTATIONS = "conflicting_denotations"


class CorpusError(ValueError):
    """A transcription or corpus was constructed invalidly."""


@dataclass(frozen=True, slots=True)
class Transcription:
    """One transcriber's rendering of a passage."""

    transcriber: str
    text: str

    def __post_init__(self) -> None:
        if not (self.transcriber and self.text):
            raise CorpusError(
                "a transcription needs a transcriber and text."
            )

    @property
    def text_hash(self) -> str:
        """Return the whitespace-normalized hash of the text."""
        return excerpt_hash(self.text)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "transcriber": self.transcriber,
            "text_hash": self.text_hash,
        }


@dataclass(frozen=True, slots=True)
class SourcePassage:
    """One transcribed statement from one source copy."""

    passage_id: str
    copy_id: str
    printed_page: str
    scan_page: str
    chapter_or_heading: str
    transcriptions: tuple[Transcription, ...]
    quantity_as_named_by_source: str
    quantity_as_named_by_code: str
    construct_equivalence: ConstructEquivalence
    value: int
    granularity: SemanticGranularity
    proposed_axis: str
    proposed_coordinate: str
    polarity: str
    confidence: float

    def __post_init__(self) -> None:
        missing = [
            name
            for name in ("passage_id", "copy_id", "printed_page")
            if not getattr(self, name)
        ]

        if missing:
            raise CorpusError(
                f"passage is missing provenance: {', '.join(missing)}. An "
                "unlocated passage is not evidence."
            )

        if not self.transcriptions:
            raise CorpusError(
                "a passage needs at least one transcription; a citation "
                "nobody transcribed is a claim about a book, not evidence "
                "from it."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise CorpusError("confidence must lie in [0, 1].")

    @property
    def doubly_transcribed(self) -> bool:
        """Return whether at least two transcribers rendered this passage."""
        return len({t.transcriber for t in self.transcriptions}) >= 2

    @property
    def transcriptions_agree(self) -> bool:
        """Return whether every transcription hashes identically."""
        return len({t.text_hash for t in self.transcriptions}) == 1

    @property
    def verbatim_excerpt(self) -> str:
        """Return the agreed text, or raise if transcribers disagree."""
        if not self.transcriptions_agree:
            raise CorpusError(
                f"transcriptions of {self.passage_id!r} disagree; resolve "
                "against the page image rather than choosing one."
            )

        return self.transcriptions[0].text

    @property
    def asserted(self) -> tuple[str, str, str]:
        """Return the (axis, coordinate, polarity) the source asserts."""
        return (self.proposed_axis, self.proposed_coordinate, self.polarity)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "passage_id": self.passage_id,
            "copy_id": self.copy_id,
            "printed_page": self.printed_page,
            "scan_page": self.scan_page,
            "chapter_or_heading": self.chapter_or_heading,
            "transcriptions": [t.to_dict() for t in self.transcriptions],
            "doubly_transcribed": self.doubly_transcribed,
            "transcriptions_agree": self.transcriptions_agree,
            "quantity_as_named_by_source": self.quantity_as_named_by_source,
            "quantity_as_named_by_code": self.quantity_as_named_by_code,
            "construct_equivalence": self.construct_equivalence.value,
            "value": self.value,
            "granularity": self.granularity.value,
            "proposed_axis": self.proposed_axis,
            "proposed_coordinate": self.proposed_coordinate,
            "polarity": self.polarity,
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class NumerologyCorpus:
    """Works, manifestations, copies and the passages transcribed from them."""

    corpus_id: str
    works: tuple[Work, ...] = ()
    manifestations: tuple[Manifestation, ...] = ()
    copies: tuple[SourceCopy, ...] = ()
    passages: tuple[SourcePassage, ...] = ()

    def __post_init__(self) -> None:
        manifestation_ids = {m.manifestation_id for m in self.manifestations}
        work_ids = {w.work_id for w in self.works}
        copy_ids = {c.copy_id for c in self.copies}

        for manifestation in self.manifestations:
            if manifestation.work_id not in work_ids:
                raise CorpusError(
                    f"manifestation {manifestation.manifestation_id!r} cites "
                    f"unknown work {manifestation.work_id!r}."
                )

        for copy in self.copies:
            if copy.manifestation_id not in manifestation_ids:
                raise CorpusError(
                    f"copy {copy.copy_id!r} cites unknown manifestation "
                    f"{copy.manifestation_id!r}."
                )

        seen: set[str] = set()

        for passage in self.passages:
            if passage.passage_id in seen:
                raise CorpusError(
                    f"duplicate passage_id {passage.passage_id!r}."
                )

            # The guarantee that a declared edition cannot be cited: a
            # passage must come from a copy someone actually held.
            if passage.copy_id not in copy_ids:
                raise CorpusError(
                    f"passage {passage.passage_id!r} cites unknown copy "
                    f"{passage.copy_id!r}; a passage may not cite a merely "
                    "declared manifestation."
                )

            seen.add(passage.passage_id)

    def manifestation(self, manifestation_id: str) -> Manifestation:
        """Return one manifestation by id."""
        for manifestation in self.manifestations:
            if manifestation.manifestation_id == manifestation_id:
                return manifestation

        raise CorpusError(f"unknown manifestation {manifestation_id!r}.")

    def copy(self, copy_id: str) -> SourceCopy:
        """Return one source copy by id."""
        for copy in self.copies:
            if copy.copy_id == copy_id:
                return copy

        raise CorpusError(f"unknown copy {copy_id!r}.")

    def manifestation_for_passage(
        self, passage: SourcePassage
    ) -> Manifestation:
        """Return the manifestation a passage was transcribed from."""
        return self.manifestation(self.copy(passage.copy_id).manifestation_id)

    def passages_for_role(self, role: SourceRole) -> list[SourcePassage]:
        """Return passages from manifestations playing one role."""
        return sorted(
            (
                passage
                for passage in self.passages
                if self.manifestation_for_passage(passage).role is role
            ),
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

    def eligible_manifestations(self, role: SourceRole) -> list[Manifestation]:
        """Return manifestations in a stratum that may be transcribed from."""
        return [
            manifestation
            for manifestation in self.manifestations
            if manifestation.role is role
            and manifestation.transcription_eligible
        ]

    def corpus_hash(self) -> str:
        """Return a deterministic hash of the whole corpus."""
        payload = {
            "schema": NUMEROLOGY_CORPUS_SCHEMA,
            "corpus_id": self.corpus_id,
            "works": sorted(
                json.dumps(w.to_dict(), sort_keys=True) for w in self.works
            ),
            "manifestations": sorted(
                json.dumps(m.to_dict(), sort_keys=True)
                for m in self.manifestations
            ),
            "copies": sorted(
                json.dumps(c.to_dict(), sort_keys=True) for c in self.copies
            ),
            "passages": sorted(
                json.dumps(p.to_dict(), sort_keys=True) for p in self.passages
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
            "works": [w.to_dict() for w in self.works],
            "manifestations": [m.to_dict() for m in self.manifestations],
            "copies": [c.to_dict() for c in self.copies],
            "passages": [p.to_dict() for p in self.passages],
            "counts": {
                "works": len(self.works),
                "manifestations": len(self.manifestations),
                "copies": len(self.copies),
                "passages": len(self.passages),
            },
        }


def build_corpus(
    corpus_id: str,
    works: Sequence[Work] = (),
    manifestations: Sequence[Manifestation] = (),
    copies: Sequence[SourceCopy] = (),
    passages: Sequence[SourcePassage] = (),
) -> NumerologyCorpus:
    """Assemble a corpus in deterministic order."""
    return NumerologyCorpus(
        corpus_id=corpus_id,
        works=tuple(sorted(works, key=lambda w: w.work_id)),
        manifestations=tuple(
            sorted(manifestations, key=lambda m: m.manifestation_id)
        ),
        copies=tuple(sorted(copies, key=lambda c: c.copy_id)),
        passages=tuple(sorted(passages, key=lambda p: p.passage_id)),
    )
