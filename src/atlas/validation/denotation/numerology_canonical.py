"""The canonical numerology denotation binding -- the live corpus and dictionary.

Compilation is caller-driven by design: the admissibility rules are separable
from the corpus so either can change and the dictionary rebuild
deterministically. That flexibility left one thing unbound -- *which* corpus is
the admitted one -- so every caller had to know to reach for
``numerology_corpus_v2.acquired_corpus``. This module names that choice once.

It adds no policy. It binds the copy-verified corpus (v2, 1E-N-SOURCE-A) to the
frozen admissibility rules and exposes the compiled dictionary as a single
discoverable artifact, so a concordance run consumes the verified evidence
rather than re-deriving it -- and so "the numerology dictionary" is a bound
thing a cross-system runner can pull, the pattern each admitted denoting system
will follow (Kamea by measurement, numerology here by source, Vedic once its
ayanamsa is licensed).
"""

from __future__ import annotations

from typing import Any

from atlas.validation.denotation.numerology_capabilities import (
    NumerologyCapabilities,
    derive_capabilities,
)
from atlas.validation.denotation.numerology_compiler import (
    AdmissibilityRules,
    CompilationReport,
    compile_dictionary,
)
from atlas.validation.denotation.numerology_corpus import NumerologyCorpus
from atlas.validation.denotation.numerology_corpus_v2 import (
    CORPUS_ID,
    acquired_corpus,
)
from atlas.validation.denotation.numerology_dictionary import (
    NumerologyDictionary,
)


# The admitted corpus. Named so a later corpus (a deeper transcription, a
# second author) is a deliberate rebind here rather than a silent divergence
# between callers.
CANONICAL_CORPUS_ID = CORPUS_ID


def canonical_corpus() -> NumerologyCorpus:
    """Return the admitted numerology corpus (1E-N-SOURCE-A, Jordan, v2)."""
    return acquired_corpus()


def canonical_rules() -> AdmissibilityRules:
    """Return the frozen admissibility rules the canonical dictionary uses."""
    return AdmissibilityRules()


def canonical_dictionary() -> tuple[NumerologyDictionary, CompilationReport]:
    """Compile the admitted corpus under the frozen rules.

    The single entry point a concordance run consumes for numerology, so it
    binds the copy-verified corpus rather than any caller re-deriving one.
    Deterministic: the same corpus and rules yield a byte-identical dictionary.
    """
    return compile_dictionary(canonical_corpus(), canonical_rules())


def canonical_capabilities() -> NumerologyCapabilities:
    """Return the capability flags derived from the canonical artifacts."""
    corpus = canonical_corpus()
    rules = canonical_rules()
    dictionary, report = compile_dictionary(corpus, rules)

    return derive_capabilities(corpus, rules, dictionary, report)


def is_concordance_eligible() -> bool:
    """Return whether the bound numerology dictionary may enter a concordance.

    The health assertion the wiring exists to make true: the live corpus is
    copy-verified, its construct equivalence is established, it compiles to
    non-empty denotations, and the artifact hashes agree.
    """
    return canonical_capabilities().concordance_eligible


def canonical_manifest() -> dict[str, Any]:
    """Return the bound numerology state, for the record."""
    corpus = canonical_corpus()
    rules = canonical_rules()
    dictionary, report = compile_dictionary(corpus, rules)
    capabilities = derive_capabilities(corpus, rules, dictionary, report)

    return {
        "corpus_id": CANONICAL_CORPUS_ID,
        "corpus_hash": corpus.corpus_hash(),
        "rules_hash": rules.rules_hash(),
        "dictionary_hash": dictionary.dictionary_hash(),
        "entries": report.entries_emitted,
        "axis_coverage": report.axis_coverage,
        "concordance_eligible": capabilities.concordance_eligible,
        "blocking": list(capabilities.blocking),
    }
