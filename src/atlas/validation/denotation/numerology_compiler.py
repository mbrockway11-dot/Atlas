"""Compile a citation corpus into a numerology dictionary.

The dictionary is derived, never authored. Frozen admissibility rules decide
which passages may speak, and the conflict verdict is *computed* from what the
admissible passages say rather than declared by whoever wrote the entry:

    passages agree on a key        -> consensus
    passages disagree              -> conflicting (licenses nothing)
    a single admissible passage    -> source_specific
    too little admissible evidence -> insufficient (silence)

Compilation is deterministic: the same corpus and the same rules produce a
byte-identical dictionary, so a rule change can be made and the dictionary
rebuilt without any hand editing. Both the corpus hash and the rule hash enter
the compiled artifact, so an entry can always be traced to the exact evidence
and rules that produced it.

This module contains **no numerological meanings**.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from atlas.validation.denotation.numerology_corpus import (
    AuthorityScope,
    NumerologyCorpus,
    SemanticGranularity,
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


ADMISSIBILITY_SCHEMA = "atlas.validation.denotation.numerology-rules.v1"


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

    # Secondary synthesis is excluded by default: it is where one system's
    # reading of another most often enters, which is exactly the cross-system
    # inheritance 1E forbids.
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

    minimum_confidence: float = 0.5

    # A key with fewer admissible passages than this compiles to silence.
    minimum_passages: int = 1

    def admits(self, passage: SourcePassage) -> bool:
        """Return whether one passage may license a denotation."""
        return (
            passage.granularity in self.allowed_granularities
            and passage.source_type in self.allowed_source_types
            and passage.authority_scope in self.allowed_authority_scopes
            and passage.confidence >= self.minimum_confidence
            and passage.quantity in COMPUTABLE_QUANTITIES
        )

    def rejection_reason(self, passage: SourcePassage) -> str | None:
        """Return why a passage was rejected, or None if admitted.

        Reported so a sparse dictionary is explicable: a reader can see that
        a key is silent because its only evidence was a prediction, not
        because the corpus lacked it.
        """
        if passage.granularity not in self.allowed_granularities:
            return f"granularity {passage.granularity.value!r} not eligible"

        if passage.source_type not in self.allowed_source_types:
            return f"source type {passage.source_type.value!r} not admitted"

        if passage.authority_scope not in self.allowed_authority_scopes:
            return (
                f"authority scope {passage.authority_scope.value!r} not "
                "admitted"
            )

        if passage.confidence < self.minimum_confidence:
            return (
                f"confidence {passage.confidence} below "
                f"{self.minimum_confidence}"
            )

        if passage.quantity not in COMPUTABLE_QUANTITIES:
            return f"quantity {passage.quantity!r} is not computed"

        return None

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
            "minimum_confidence": self.minimum_confidence,
            "minimum_passages": self.minimum_passages,
        }


@dataclass(frozen=True, slots=True)
class CompilationReport:
    """What the compiler did, including what it refused and why."""

    corpus_hash: str
    rules_hash: str
    dictionary_hash: str
    keys_seen: int
    entries_emitted: int
    verdicts: dict[str, int]
    rejections: dict[str, list[str]]
    axis_coverage: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "corpus_hash": self.corpus_hash,
            "rules_hash": self.rules_hash,
            "dictionary_hash": self.dictionary_hash,
            "keys_seen": self.keys_seen,
            "entries_emitted": self.entries_emitted,
            "verdicts": self.verdicts,
            "rejections": self.rejections,
            "axis_coverage": self.axis_coverage,
            "note": (
                "Sparse coverage is expected and desirable. Agreement should "
                "emerge from independently licensed overlaps, not from a "
                "broad interpretive vocabulary."
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
    if len(passages) < rules.minimum_passages or not passages:
        return ConflictVerdict.INSUFFICIENT, None

    asserted = {passage.asserted for passage in passages}

    if len(asserted) > 1:
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
    tradition: str,
    version: str,
) -> tuple[NumerologyDictionary, CompilationReport]:
    """Compile a corpus into a dictionary under frozen rules.

    Deterministic: the same corpus and rules always produce the same
    dictionary, so recompiling after a rule change requires no hand editing
    and cannot silently diverge.
    """
    entries: list[NumerologyDictionaryEntry] = []
    verdicts: dict[str, int] = {v.value: 0 for v in ConflictVerdict}
    rejections: dict[str, list[str]] = {}
    axis_coverage: dict[str, int] = {}
    keys_seen = 0

    for key_tradition, quantity, value in corpus.keys():
        if key_tradition != tradition:
            continue

        keys_seen += 1
        candidates = corpus.for_key(key_tradition, quantity, value)

        admissible: list[SourcePassage] = []

        for passage in candidates:
            reason = rules.rejection_reason(passage)

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

        entry = NumerologyDictionaryEntry(
            tradition=tradition,
            quantity=quantity,
            value=value,
            reduction_policy=REDUCTION_POLICY,
            axis=representative.axis,
            coordinate=representative.coordinate,
            polarity=representative.polarity,
            # Every compiled mapping is interpretive: it rests on what a
            # source says a value means, not on a measurement.
            mapping_kind="interpretive",
            conflict_verdict=verdict,
            confidence=min(
                passage.confidence for passage in admissible
            ),
            citation=SourceCitation(
                tradition=tradition,
                source_id=representative.passage_id,
                passage=(
                    f"{representative.author}, {representative.work} "
                    f"({representative.edition}), {representative.locator}"
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
        corpus_hash=corpus.corpus_hash(),
        rules_hash=rules.rules_hash(),
        dictionary_hash=dictionary.dictionary_hash(),
        keys_seen=keys_seen,
        entries_emitted=len(entries),
        verdicts=verdicts,
        rejections=rejections,
        axis_coverage=axis_coverage,
    )

    return dictionary, report
