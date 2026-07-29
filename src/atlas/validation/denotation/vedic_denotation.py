"""Vedic graha denotation -- the scaffold, declared but not yet sourced.

The analogue of the numerology corpus/compiler/dictionary stack, collapsed into
one module because grahas are simpler than reduced numbers: there is no
reduction policy and no arithmetic construct to reconcile. A passage names a
graha, and the graha it names is by identity the graha the code computes (the
Sun of Brihat Parasara Hora Shastra is ``"sun"``), so construct equivalence is
established by the name rather than argued.

Everything else is the same discipline as numerology. A denotation is derived
from a transcribed passage, never authored; transcription is doubled; the
capability flags are computed from the corpus and go false the moment the
evidence changes. This module reuses the generic bibliographic primitives
(``Work``/``Manifestation``/``SourceCopy``/``Transcription``) rather than
duplicating them.

**No graha meaning lives here.** ``declared_corpus`` names Brihat Parasara Hora
Shastra and a manifestation but holds no copy and no passage, so it compiles to
an empty dictionary -- the correct output until a copy is verified and the nine
karakatvas are transcribed from it (1E-V-SOURCE-B). That is the provenance
system working, not a blocked implementation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Any, Sequence

from atlas.validation.denotation.expressions import DenotationClaim
from atlas.validation.denotation.numerology_bibliography import (
    AuthorityScope,
    IdentityStatus,
    Manifestation,
    SourceCopy,
    SourceType,
    Work,
    excerpt_hash,
)
from atlas.validation.denotation.numerology_corpus import Transcription
from atlas.validation.denotation.numerology_tradition import SourceRole
from atlas.validation.denotation.ontology import (
    MAPPING_KINDS,
    POLARITIES,
    require_coordinate,
)
from atlas.validation.denotation.vedic_grahas import (
    GRAHA_ITSELF,
    GRAHAS,
    VedicExpression,
)


VEDIC_DENOTATION_SCHEMA = "atlas.validation.denotation.vedic-graha.v1"
VEDIC_TRADITION_ID = "classical-jyotisa-parasari-v1"


class VedicCorpusError(ValueError):
    """A Vedic passage or corpus was constructed invalidly."""


class GrahaSemanticGranularity(str, Enum):
    """What kind of statement a graha passage makes.

    Only ``KARAKATVA`` -- a direct statement of a graha's natural signification
    -- is eligible. Placement rules ("Saturn in the 7th gives...") and
    predictive statements are real evidence but not a denotation of the graha
    itself, and admitting them would drift the audit into inferred biography.
    """

    KARAKATVA = "karakatva"
    PLACEMENT_RULE = "placement_rule"
    PREDICTION = "prediction"
    COMMENTARY = "commentary"


@dataclass(frozen=True, slots=True)
class GrahaPassage:
    """One transcribed karakatva statement for one graha, from one copy."""

    passage_id: str
    graha: str
    copy_id: str
    printed_page: str
    scan_page: str
    chapter_or_heading: str
    transcriptions: tuple[Transcription, ...]
    granularity: GrahaSemanticGranularity
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
            raise VedicCorpusError(
                f"passage is missing provenance: {', '.join(missing)}."
            )

        if self.graha not in GRAHAS:
            raise VedicCorpusError(
                f"{self.graha!r} is not a graha the code produces; a passage "
                "may not denote a construct outside the frozen set."
            )

        if not self.transcriptions:
            raise VedicCorpusError(
                "a passage needs at least one transcription."
            )

        if not 0.0 <= self.confidence <= 1.0:
            raise VedicCorpusError("confidence must lie in [0, 1].")

    @property
    def doubly_transcribed(self) -> bool:
        """Return whether at least two transcribers rendered this passage."""
        return len({t.transcriber for t in self.transcriptions}) >= 2

    @property
    def transcriptions_agree(self) -> bool:
        """Return whether every transcription hashes identically."""
        return len({t.text_hash for t in self.transcriptions}) == 1

    @property
    def asserted(self) -> tuple[str, str, str]:
        """Return the (axis, coordinate, polarity) the source asserts."""
        return (self.proposed_axis, self.proposed_coordinate, self.polarity)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "passage_id": self.passage_id,
            "graha": self.graha,
            "copy_id": self.copy_id,
            "printed_page": self.printed_page,
            "scan_page": self.scan_page,
            "chapter_or_heading": self.chapter_or_heading,
            "transcriptions": [t.to_dict() for t in self.transcriptions],
            "doubly_transcribed": self.doubly_transcribed,
            "transcriptions_agree": self.transcriptions_agree,
            "granularity": self.granularity.value,
            "proposed_axis": self.proposed_axis,
            "proposed_coordinate": self.proposed_coordinate,
            "polarity": self.polarity,
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class VedicGrahaCorpus:
    """Works, manifestations, copies and the karakatva passages transcribed."""

    corpus_id: str
    works: tuple[Work, ...] = ()
    manifestations: tuple[Manifestation, ...] = ()
    copies: tuple[SourceCopy, ...] = ()
    passages: tuple[GrahaPassage, ...] = ()

    def __post_init__(self) -> None:
        manifestation_ids = {m.manifestation_id for m in self.manifestations}
        work_ids = {w.work_id for w in self.works}
        copy_ids = {c.copy_id for c in self.copies}

        for manifestation in self.manifestations:
            if manifestation.work_id not in work_ids:
                raise VedicCorpusError(
                    f"manifestation {manifestation.manifestation_id!r} cites "
                    f"unknown work {manifestation.work_id!r}."
                )

        for copy in self.copies:
            if copy.manifestation_id not in manifestation_ids:
                raise VedicCorpusError(
                    f"copy {copy.copy_id!r} cites unknown manifestation "
                    f"{copy.manifestation_id!r}."
                )

        seen: set[str] = set()

        for passage in self.passages:
            if passage.passage_id in seen:
                raise VedicCorpusError(
                    f"duplicate passage_id {passage.passage_id!r}."
                )

            if passage.copy_id not in copy_ids:
                raise VedicCorpusError(
                    f"passage {passage.passage_id!r} cites unknown copy "
                    f"{passage.copy_id!r}; a passage may not cite a merely "
                    "declared manifestation."
                )

            seen.add(passage.passage_id)

    def eligible_manifestations(self) -> list[Manifestation]:
        """Return manifestations that may be transcribed from."""
        return [
            manifestation
            for manifestation in self.manifestations
            if manifestation.transcription_eligible
        ]

    def corpus_hash(self) -> str:
        """Return a deterministic hash of the whole corpus."""
        payload = {
            "schema": VEDIC_DENOTATION_SCHEMA,
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
            "schema": VEDIC_DENOTATION_SCHEMA,
            "corpus_id": self.corpus_id,
            "hash": self.corpus_hash(),
            "counts": {
                "works": len(self.works),
                "manifestations": len(self.manifestations),
                "copies": len(self.copies),
                "passages": len(self.passages),
            },
        }


@dataclass(frozen=True, slots=True)
class GrahaDictionaryEntry:
    """One source-licensed mapping from a graha to an ontology coordinate."""

    tradition: str
    graha: str
    axis: str
    coordinate: str
    polarity: str
    mapping_kind: str
    confidence: float
    source_passage_id: str
    citation: str

    def __post_init__(self) -> None:
        require_coordinate(self.axis, self.coordinate)

        if self.graha not in GRAHAS:
            raise VedicCorpusError(f"{self.graha!r} is not a graha.")

        if self.polarity not in POLARITIES:
            raise VedicCorpusError(f"{self.polarity!r} is not a polarity.")

        if self.mapping_kind not in MAPPING_KINDS:
            raise VedicCorpusError(
                f"{self.mapping_kind!r} is not a mapping kind."
            )

        if not (self.source_passage_id and self.citation):
            raise VedicCorpusError(
                "an entry needs a source passage id and a citation."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "tradition": self.tradition,
            "graha": self.graha,
            "axis": self.axis,
            "coordinate": self.coordinate,
            "polarity": self.polarity,
            "mapping_kind": self.mapping_kind,
            "confidence": self.confidence,
            "source_passage_id": self.source_passage_id,
            "citation": self.citation,
        }


@dataclass(frozen=True, slots=True)
class GrahaDictionary:
    """A frozen, single-tradition set of graha denotations."""

    tradition: str
    version: str
    entries: tuple[GrahaDictionaryEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        seen: set[str] = set()

        for entry in self.entries:
            if entry.graha in seen:
                raise VedicCorpusError(
                    f"duplicate graha {entry.graha!r}; a conflict must be a "
                    "verdict, not two competing entries."
                )

            seen.add(entry.graha)

    def lookup(self, graha: str) -> GrahaDictionaryEntry | None:
        """Return the licensing entry for a graha, or None for silence."""
        for entry in self.entries:
            if entry.graha == graha:
                return entry

        return None

    def dictionary_hash(self) -> str:
        """Return a deterministic hash of every entry."""
        payload = {
            "schema": VEDIC_DENOTATION_SCHEMA,
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
            "schema": VEDIC_DENOTATION_SCHEMA,
            "tradition": self.tradition,
            "version": self.version,
            "hash": self.dictionary_hash(),
            "entries": [entry.to_dict() for entry in self.entries],
        }


@dataclass(frozen=True, slots=True)
class VedicCapabilities:
    """What the Vedic denotation branch is currently permitted to do."""

    source_copy_verified: bool
    direct_denotations_available: bool
    hashes_agree: bool
    corpus_hash: str
    dictionary_hash: str
    blocking: tuple[str, ...]

    @property
    def concordance_eligible(self) -> bool:
        """Return whether Vedic graha denotation may enter a concordance."""
        return (
            self.source_copy_verified
            and self.direct_denotations_available
            and self.hashes_agree
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": VEDIC_DENOTATION_SCHEMA,
            "source_copy_verified": self.source_copy_verified,
            "direct_denotations_available": self.direct_denotations_available,
            "hashes_agree": self.hashes_agree,
            "concordance_eligible": self.concordance_eligible,
            "corpus_hash": self.corpus_hash,
            "dictionary_hash": self.dictionary_hash,
            "blocking": list(self.blocking),
        }


def compile_graha_dictionary(
    corpus: VedicGrahaCorpus,
    *,
    tradition: str = VEDIC_TRADITION_ID,
    version: str = "1.0.0",
    require_double_transcription: bool = True,
    minimum_confidence: float = 0.5,
) -> GrahaDictionary:
    """Compile a corpus into a graha dictionary, one entry per graha.

    A passage is admissible only from a transcription-eligible manifestation,
    doubly transcribed and agreeing, a KARAKATVA statement, above the
    confidence floor. Grahas with conflicting admissible passages are dropped
    to silence rather than reconciled.
    """
    eligible_copies = {
        copy.copy_id
        for manifestation in corpus.eligible_manifestations()
        for copy in corpus.copies
        if copy.manifestation_id == manifestation.manifestation_id
    }

    by_graha: dict[str, list[GrahaPassage]] = {}

    for passage in corpus.passages:
        if passage.copy_id not in eligible_copies:
            continue
        if not passage.transcriptions_agree:
            continue
        if require_double_transcription and not passage.doubly_transcribed:
            continue
        if passage.granularity is not GrahaSemanticGranularity.KARAKATVA:
            continue
        if passage.confidence < minimum_confidence:
            continue

        by_graha.setdefault(passage.graha, []).append(passage)

    entries: list[GrahaDictionaryEntry] = []

    for graha, passages in by_graha.items():
        if len({p.asserted for p in passages}) > 1:
            continue  # conflicting; licenses nothing

        representative = sorted(passages, key=lambda p: p.passage_id)[0]

        entries.append(
            GrahaDictionaryEntry(
                tradition=tradition,
                graha=graha,
                axis=representative.proposed_axis,
                coordinate=representative.proposed_coordinate,
                polarity=representative.polarity,
                mapping_kind="interpretive",
                confidence=min(p.confidence for p in passages),
                source_passage_id=representative.passage_id,
                citation=(
                    f"{representative.chapter_or_heading}, printed p. "
                    f"{representative.printed_page}"
                ),
            )
        )

    return GrahaDictionary(
        tradition=tradition,
        version=version,
        entries=tuple(sorted(entries, key=lambda e: e.graha)),
    )


def derive_vedic_capabilities(
    corpus: VedicGrahaCorpus, dictionary: GrahaDictionary
) -> VedicCapabilities:
    """Derive capability flags from the corpus and the compiled dictionary."""
    blocking: list[str] = []

    source_copy_verified = bool(corpus.eligible_manifestations()) and bool(
        corpus.copies
    )
    if not source_copy_verified:
        blocking.append(
            "no transcription-eligible manifestation with a source copy"
        )

    denotations_available = bool(dictionary.entries)
    if not denotations_available:
        blocking.append("no compiled denotations")

    # The dictionary must describe the corpus as it stands now.
    hashes_agree = dictionary.dictionary_hash() == compile_graha_dictionary(
        corpus, tradition=dictionary.tradition, version=dictionary.version
    ).dictionary_hash()
    if not hashes_agree:
        blocking.append("compiled dictionary does not match the corpus")

    return VedicCapabilities(
        source_copy_verified=source_copy_verified,
        direct_denotations_available=denotations_available,
        hashes_agree=hashes_agree,
        corpus_hash=corpus.corpus_hash(),
        dictionary_hash=dictionary.dictionary_hash(),
        blocking=tuple(blocking),
    )


def claim_from_expression(
    expression: VedicExpression,
    dictionary: GrahaDictionary,
    subject_id: str,
    *,
    temporal_scope: str = "natal",
) -> DenotationClaim | None:
    """Apply the dictionary to a computed graha, by graha identity.

    Returns silence when no licensing entry exists. The graha's karakatva
    denotes it wherever it was reached (``GRAHA_ITSELF``), so the lagna lord
    and any later selector share the same denotation.
    """
    entry = dictionary.lookup(expression.graha)

    if entry is None:
        return None

    return DenotationClaim(
        system="vedic",
        subject_id=subject_id,
        axis=entry.axis,
        value=entry.coordinate,
        polarity=entry.polarity,
        temporal_scope=temporal_scope,
        mapping_kind=entry.mapping_kind,
        confidence=entry.confidence,
        source_basis=(
            f"{entry.tradition}:{entry.source_passage_id}:"
            f"{GRAHA_ITSELF}={expression.graha}"
        ),
    )


# Brihat Parasara Hora Shastra, the foundational Parasari text. Declared, with
# a manifestation to be pinned when a copy is verified. No copy, no passage:
# this compiles to an empty dictionary until 1E-V-SOURCE-B transcribes the nine
# karakatvas from a verified copy.
BPHS_WORK = Work(
    work_id="brihat_parasara_hora_shastra",
    author="Parasara (attrib.)",
    title="Brihat Parasara Hora Shastra",
    work_identity=IdentityStatus.VERIFIED,
    identity_note=(
        "The foundational text of Parasari Jyotisa, widely represented in "
        "catalogs in Sanskrit and in translation. A specific critical edition "
        "or scholarly translation must be pinned and copy-verified before any "
        "passage licenses a denotation."
    ),
)


BPHS_MANIFESTATION = Manifestation(
    manifestation_id="bphs-edition-pending",
    work_id=BPHS_WORK.work_id,
    edition_statement="to be pinned at copy verification",
    publisher="",
    publication_year=None,
    copyright_year=None,
    isbn="",
    oclc="",
    pagination="",
    fmt="",
    role=SourceRole.CANONICAL,
    source_type=SourceType.PRIMARY,
    authority_scope=AuthorityScope.TRADITION_WIDE,
    edition_identity=IdentityStatus.UNRESOLVED,
    pagination_identity=IdentityStatus.UNRESOLVED,
    identity_note=(
        "No copy verified yet. The manifestation is not transcription-"
        "eligible, so the corpus compiles to silence -- the correct state "
        "until 1E-V-SOURCE-B."
    ),
)


def declared_corpus() -> VedicGrahaCorpus:
    """Return the Vedic graha corpus: BPHS declared, no copy, no passage.

    Compiling this yields an empty dictionary. That is the provenance system
    working: the scaffold is built, and it stays silent until a copy of the
    source is verified and the nine karakatvas are transcribed from it.
    """
    return VedicGrahaCorpus(
        corpus_id="vedic-graha-corpus-v1",
        works=(BPHS_WORK,),
        manifestations=(BPHS_MANIFESTATION,),
        copies=(),
        passages=(),
    )
