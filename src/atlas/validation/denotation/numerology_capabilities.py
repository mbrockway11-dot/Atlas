"""Positive capability flags for numerology denotation.

Every downstream numerology operation must gate on these rather than on
whether a dictionary happens to be non-empty. A non-empty dictionary is a weak
signal that fails open: it is equally satisfied by test-fixture meanings, a
stale cached artifact, output from the legacy unprovenanced adapter, a
partially ingested source, or a dictionary compiled against a corpus that has
since changed.

The flags are *derived from the corpus*, never set by hand, and
``concordance_eligible`` requires both every upstream state and agreement
between the hashes that produced them. A dictionary whose recorded corpus hash
no longer matches the corpus is not merely stale -- it describes evidence that
is no longer there, and the flag goes false regardless of how many entries it
holds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.validation.denotation.numerology_compiler import (
    AdmissibilityRules,
    CompilationReport,
)
from atlas.validation.denotation.numerology_corpus import (
    ConstructEquivalence,
    NumerologyCorpus,
)
from atlas.validation.denotation.numerology_dictionary import (
    NumerologyDictionary,
)
from atlas.validation.denotation.numerology_tradition import SourceRole


CAPABILITIES_SCHEMA = "atlas.validation.denotation.numerology-caps.v1"


@dataclass(frozen=True, slots=True)
class NumerologyCapabilities:
    """What the numerology branch is currently permitted to do."""

    source_copy_verified: bool
    construct_equivalence_established: bool
    direct_denotations_available: bool
    hashes_agree: bool
    corpus_hash: str
    dictionary_hash: str
    rules_hash: str
    blocking: tuple[str, ...]

    @property
    def concordance_eligible(self) -> bool:
        """Return whether numerology may enter a concordance study.

        True only when every upstream state holds *and* the hashes agree.
        Any one of them false means numerology contributes silence, not a
        degraded claim.
        """
        return (
            self.source_copy_verified
            and self.construct_equivalence_established
            and self.direct_denotations_available
            and self.hashes_agree
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema": CAPABILITIES_SCHEMA,
            "source_copy_verified": self.source_copy_verified,
            "construct_equivalence_established": (
                self.construct_equivalence_established
            ),
            "direct_denotations_available": (
                self.direct_denotations_available
            ),
            "hashes_agree": self.hashes_agree,
            "concordance_eligible": self.concordance_eligible,
            "corpus_hash": self.corpus_hash,
            "dictionary_hash": self.dictionary_hash,
            "rules_hash": self.rules_hash,
            "blocking": list(self.blocking),
            "cannot_claim": [
                "that implemented quantities correspond to any source's "
                "constructs",
                "that any source licenses 11, 22 or 33",
                "that any number maps to any ontology coordinate",
                "that numerology agrees or disagrees with Kamea",
            ],
        }


def derive_capabilities(
    corpus: NumerologyCorpus,
    rules: AdmissibilityRules,
    dictionary: NumerologyDictionary,
    report: CompilationReport,
    *,
    role: SourceRole = SourceRole.CANONICAL,
) -> NumerologyCapabilities:
    """Derive capability flags from the corpus and the compiled artifacts."""
    blocking: list[str] = []

    eligible = corpus.eligible_manifestations(role)
    source_copy_verified = bool(eligible) and bool(corpus.copies)

    if not source_copy_verified:
        blocking.append(
            "no transcription-eligible manifestation with a source copy"
        )

    passages = corpus.passages_for_role(role)
    construct_established = any(
        passage.construct_equivalence
        in {
            ConstructEquivalence.EXACT,
            ConstructEquivalence.COMPUTATIONALLY_EQUIVALENT,
        }
        for passage in passages
    )

    if not construct_established:
        blocking.append(
            "no passage establishes that a source construct is the code's"
        )

    denotations_available = bool(dictionary.entries)

    if not denotations_available:
        blocking.append("no compiled denotations")

    # The artifacts must describe the corpus as it stands now. A report
    # carrying a stale corpus hash describes evidence that has since changed.
    hashes_agree = (
        report.corpus_hash == corpus.corpus_hash()
        and report.rules_hash == rules.rules_hash()
        and report.dictionary_hash == dictionary.dictionary_hash()
    )

    if not hashes_agree:
        blocking.append(
            "compiled artifacts do not match the current corpus, rules or "
            "dictionary hash"
        )

    return NumerologyCapabilities(
        source_copy_verified=source_copy_verified,
        construct_equivalence_established=construct_established,
        direct_denotations_available=denotations_available,
        hashes_agree=hashes_agree,
        corpus_hash=corpus.corpus_hash(),
        dictionary_hash=dictionary.dictionary_hash(),
        rules_hash=rules.rules_hash(),
        blocking=tuple(blocking),
    )


# The legacy interpretive adapter maps computed numbers straight to structural
# evidence with no source provenance. It predates 1E and remains in the tree
# for other callers, but it is the largest accidental-entry path into the
# provenanced architecture: a later caller reaching for it would get meanings
# that no citation licenses.
LEGACY_UNPROVENANCED_INTERPRETATION: dict[str, Any] = {
    "module": "atlas.synthesis.adapters.numerology",
    "symbol": "evidence_from_number",
    "present": True,
    "permitted_in_1E": False,
    "reason": (
        "maps numbers to structural evidence with no source, tradition, "
        "edition, page or construct-equivalence verdict"
    ),
}
