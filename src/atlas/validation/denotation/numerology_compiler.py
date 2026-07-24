"""Compile a citation corpus into a numerology dictionary.

The dictionary is derived, never authored. Frozen admissibility rules decide
which passages may speak, and the conflict verdict is *computed* from what the
admissible passages say rather than declared by whoever wrote the entry:

    passages agree on a key        -> consensus
    passages disagree              -> conflicting (licenses nothing)
    a single admissible passage    -> source_specific
    too little admissible evidence -> insufficient (silence)

Compilation is stratified. Only the canonical stratum produces the code-facing
dictionary; a historical precursor compiles separately and can never join a
canonical consensus. Requiring precursor agreement would conflate historical
comparison with evidence sufficiency -- a single admissible canonical passage
is enough to license a ``source_specific`` entry.

Compilation is deterministic: the same corpus and rules produce a
byte-identical dictionary, so a rule change can be made and the dictionary
rebuilt without any hand editing.

This module contains **no numerological meanings**.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any

from atlas.validation.denotation.numerology_corpus import (
    AuthorityScope,
    ConstructEquivalence,
    NumerologyCorpus,
    SemanticGranularity,
    SourceEdition,
    SourcePassage,
    SourceType,
)
from atlas.validation.denotation.numerology_dictionary import (
    ConflictVerdict,
    NumerologyDictionary,
    NumerologyDictionaryEntry,
    SourceCitation,
)
from atlas.validation.denotation.numerology_expression import (
    COMPUTABLE_QUANTITIES,
    REDUCTION_POLICY,
)
from atlas.validation.denotation.numerology_tradition import (
    TRADITION_ID,
    SourceRole,
)


ADMISSIBILITY_SCHEMA = "atlas.validation.denotation.numerology-rules.v2"


@dataclass(frozen=True, slots=True)
class AdmissibilityRules:
    """Which passages may license a denotation.

    Separable from the corpus by design: tightening or relaxing these and
    recompiling is a reproducible operation on unchanged evidence.
    """

    version: str = "1.0.0"

    # Only direct denotations are eligible for 1E-A. Everything else is real
    # evidence about the tradition but is not a statement of what a value
    # means, and admitting it would drift the audit into inferred personality.
    allowed_granularities: frozenset[SemanticGranularity] = frozenset(
        {SemanticGranularity.DIRECT_DENOTATION}
    )

    # Secondary synthesis is excluded: it is where one system's reading of
    # another most often enters, which is the cross-system inheritance 1E
    # forbids.
    allowed_source_types: frozenset[SourceType] = frozenset(
        {
            SourceType.PRIMARY,
            SourceType.TRADITIONAL_COMMENTARY,
            SourceType.MODERN_COMMENTARY,
        }
    )

    allowed_authority_scopes: frozenset[AuthorityScope] = frozenset(
        {
            AuthorityScope.TRADITION_WIDE,
            AuthorityScope.SCHOOL_SPECIFIC,
            AuthorityScope.AUTHOR_SPECIFIC,
        }
    )

    # A shared phrase is not evidence. Only a construct the source and the
    # code genuinely share may license a mapping.
    allowed_construct_equivalence: frozenset[ConstructEquivalence] = (
        frozenset(
            {
                ConstructEquivalence.EXACT,
                ConstructEquivalence.COMPUTATIONALLY_EQUIVALENT,
            }
        )
    )

    minimum_confidence: float = 0.5

    # A key with fewer admissible passages than this compiles to silence.
    minimum_passages: int = 1

    def rejection_reason(
        self, passage: SourcePassage, edition: SourceEdition
    ) -> str | None:
        """Return why a passage was rejected, or None if admitted.

        Takes both the passage and its edition, because source type and
        authority scope are properties of the printing rather than of the
        sentence transcribed from it.

        Reported so a sparse dictionary is explicable: a reader can see that
        a key is silent because its only evidence was a prediction, or a
        terminology-only resemblance, rather than because the corpus lacked
        it.
        """
        if passage.granularity not in self.allowed_granularities:
            return f"granularity {passage.granularity.value!r} not eligible"

        if passage.construct_equivalence not in (
            self.allowed_construct_equivalence
        ):
            return (
                "construct equivalence "
                f"{passage.construct_equivalence.value!r} does not establish "
                "that the source's construct is the code's construct"
            )

        if edition.authority_scope not in self.allowed_authority_scopes:
            return (
                f"authority scope {edition.authority_scope.value!r} not "
                "admitted"
            )

        if edition.source_type not in self.allowed_source_types:
            return f"source type {edition.source_type.value!r} not admitted"

        if passage.confidence < self.minimum_confidence:
            return (
                f"confidence {passage.confidence} below "
                f"{self.minimum_confidence}"
            )

        if passage.quantity_as_named_by_code not in COMPUTABLE_QUANTITIES:
            return (
                f"quantity {passage.quantity_as_named_by_code!r} is not "
                "computed"
            )

        return None

    def admits(
        self, passage: SourcePassage, edition: SourceEdition
    ) -> bool:
        """Return whether one passage may license a denotation."""
        return self.rejection_reason(passage, edition) is None

    def rules_hash(self) -> str:
        """Return a deterministic hash of the admissibility rules."""
        payload = {
            "schema": ADMISSIBILITY_SCHEMA,
            "version": self.version,
            "granularities": sorted(
                g.value for g in self.allowed_granularities
            ),
            "source_types": sorted(
                t.value for t in self.allowed_source_types
            ),
            "authority_scopes": sorted(
                s.value for s in self.allowed_authority_scopes
            ),
            "construct_equivalence": sorted(
                c.value for c in self.allowed_construct_equivalence
            ),
            "minimum_confidence": self.minimum_confidence,
            "minimum_passages": self.minimum_passages,
        }

        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
                "utf-8"
            )
        ).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": ADMISSIBILITY_SCHEMA,
            "version": self.version,
            "hash": self.rules_hash(),
            "allowed_granularities": sorted(
                g.value for g in self.allowed_granularities
            ),
            "allowed_source_types": sorted(
                t.value for t in self.allowed_source_types
            ),
            "allowed_authority_scopes": sorted(
                s.value for s in self.allowed_authority_scopes
            ),
            "allowed_construct_equivalence": sorted(
                c.value for c in self.allowed_construct_equivalence
            ),
            "minimum_confidence": self.minimum_confidence,
            "minimum_passages": self.minimum_passages,
        }


@dataclass(frozen=True, slots=True)
class CompilationReport:
    """What the compiler did, including what it refused and why."""

    corpus_id: str
    corpus_hash: str
    rules_hash: str
    dictionary_hash: str
    role: str
    keys_seen: int
    entries_emitted: int
    passages_available: int
    verdicts: dict[str, int]
    rejections: dict[str, list[str]]
    axis_coverage: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "corpus_id": self.corpus_id,
            "corpus_hash": self.corpus_hash,
            "rules_hash": self.rules_hash,
            "dictionary_hash": self.dictionary_hash,
            "role": self.role,
            "keys_seen": self.keys_seen,
            "entries_emitted": self.entries_emitted,
            "passages_available": self.passages_available,
            "verdicts": self.verdicts,
            "rejections": self.rejections,
            "axis_coverage": self.axis_coverage,
            "note": (
                "Sparse coverage is expected and desirable. Agreement should "
                "emerge from independently licensed overlaps, not from a "
                "broad interpretive vocabulary. An empty dictionary means no "
                "admissible passage has been transcribed yet."
            ),
        }


def _verdict_for(
    passages: list[SourcePassage], rules: AdmissibilityRules
) -> tuple[ConflictVerdict, SourcePassage | None]:
    """Derive the conflict verdict for one key from its admissible passages.

    The verdict is computed, never declared. Disagreeing sources compile to
    ``conflicting``, which licenses nothing -- the policy prefers silence to
    an informal reconciliation.
    """
    if not passages or len(passages) < rules.minimum_passages:
        return ConflictVerdict.INSUFFICIENT, None

    if len({passage.asserted for passage in passages}) > 1:
        return ConflictVerdict.CONFLICTING, None

    # Deterministic representative: lowest passage_id among agreeing sources.
    representative = passages[0]

    if len(passages) == 1:
        return ConflictVerdict.SOURCE_SPECIFIC, representative

    return ConflictVerdict.CONSENSUS, representative


def compile_dictionary(
    corpus: NumerologyCorpus,
    rules: AdmissibilityRules,
    *,
    role: SourceRole = SourceRole.CANONICAL,
    tradition: str = TRADITION_ID,
    version: str = "1.0.0",
) -> tuple[NumerologyDictionary, CompilationReport]:
    """Compile one stratum of a corpus into a dictionary.

    Only passages from editions playing ``role`` are visible, so a historical
    precursor can never contribute to the canonical dictionary. Compiling the
    precursor stratum separately produces a comparison dictionary; any
    agreement between the two is a later, explicit finding rather than an
    assumption baked into compilation.
    """
    available = corpus.passages_for_role(role)

    entries: list[NumerologyDictionaryEntry] = []
    verdicts: dict[str, int] = {v.value: 0 for v in ConflictVerdict}
    rejections: dict[str, list[str]] = {}
    axis_coverage: dict[str, int] = {}
    keys_seen = 0

    for quantity, value in corpus.keys_for_role(role):
        keys_seen += 1

        candidates = [
            passage
            for passage in available
            if passage.quantity_as_named_by_code == quantity
            and passage.value == value
        ]

        admissible: list[SourcePassage] = []

        for passage in candidates:
            reason = rules.rejection_reason(
                passage, corpus.edition(passage.edition_id)
            )

            if reason is None:
                admissible.append(passage)
            else:
                rejections.setdefault(f"{quantity}={value}", []).append(
                    f"{passage.passage_id}: {reason}"
                )

        verdict, representative = _verdict_for(admissible, rules)
        verdicts[verdict.value] += 1

        if representative is None:
            continue

        edition = corpus.edition(representative.edition_id)

        entry = NumerologyDictionaryEntry(
            tradition=tradition,
            quantity=quantity,
            value=value,
            reduction_policy=REDUCTION_POLICY,
            axis=representative.proposed_axis,
            coordinate=representative.proposed_coordinate,
            polarity=representative.polarity,
            # Every compiled mapping is interpretive: it rests on what a
            # source says a value means, not on a measurement.
            mapping_kind="interpretive",
            conflict_verdict=verdict,
            confidence=min(passage.confidence for passage in admissible),
            citation=SourceCitation(
                tradition=tradition,
                source_id=representative.passage_id,
                passage=(
                    f"{edition.author}, {edition.title} "
                    f"({edition.edition}, {edition.publisher}, "
                    f"{edition.publication_year}), p. {representative.page}"
                ),
            ),
        )

        entries.append(entry)
        axis_coverage[entry.axis] = axis_coverage.get(entry.axis, 0) + 1

    dictionary = NumerologyDictionary(
        tradition=tradition,
        version=version,
        entries=tuple(sorted(entries, key=lambda entry: entry.key())),
    )

    report = CompilationReport(
        corpus_id=corpus.corpus_id,
        corpus_hash=corpus.corpus_hash(),
        rules_hash=rules.rules_hash(),
        dictionary_hash=dictionary.dictionary_hash(),
        role=role.value,
        keys_seen=keys_seen,
        entries_emitted=len(entries),
        passages_available=len(available),
        verdicts=verdicts,
        rejections=rejections,
        axis_coverage=axis_coverage,
    )

    return dictionary, report
