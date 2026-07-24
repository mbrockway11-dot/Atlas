"""The declared numerology corpus v1 — editions only, no passages yet.

The two editions the corpus is scoped to are declared here. **No passages have
been transcribed**, because transcription requires a paginated copy of each
edition and none has been ingested. The corpus is therefore empty of evidence,
and the compiler correctly emits an empty dictionary.

That is the honest state, not a gap to be filled by paraphrase. Inventing
excerpts and page numbers would put fabricated bibliography into the one
artifact whose entire purpose is traceable provenance.

**Bibliographic verification.** The editions below were specified by the
project owner. Checking them against Open Library did not confirm either
cleanly, and both discrepancies are recorded on the edition rather than
resolved silently:

* Jordan — Open Library's records for this work list DeVorss with a first
  publication year of 1977, plus 1984 and 1991 printings. The specified
  1978 first-paperback / (c)1965 lineage was not confirmed there.
* Balliett — the record matching this author and title most closely is a
  1969 Mokelumne Hill Press printing, which is a later reprint of exactly the
  kind the policy excludes as a corroborating source. A 1908 edition appears
  among the results but was not individually confirmed.

Neither discrepancy blocks anything today, since no passage cites either
edition. Both must be resolved against the physical copy before a
transcription is admitted.
"""

from __future__ import annotations

from atlas.validation.denotation.numerology_corpus import (
    AuthorityScope,
    NumerologyCorpus,
    SourceEdition,
    SourceType,
    build_corpus,
)
from atlas.validation.denotation.numerology_tradition import (
    SourceRole,
    VerificationStatus,
)


CORPUS_ID = "numerology-corpus-v1"


# The canonical source for the code-facing dictionary. One author and one
# edition, deliberately: drawing on several modern manuals at once would
# manufacture consensus out of heterogeneous sources that happen to be
# marketed under the same word.
JORDAN_1978 = SourceEdition(
    edition_id="jordan-romance-1978-1st-paperback",
    author="Juno Jordan",
    title="Numerology: The Romance in Your Name",
    edition="1st paperback edition",
    publisher="DeVorss",
    publication_year=1978,
    copyright_year=1965,
    role=SourceRole.CANONICAL,
    source_type=SourceType.MODERN_COMMENTARY,
    # Author-specific until passages establish that the constructs are
    # tradition-wide rather than this author's systematization.
    authority_scope=AuthorityScope.AUTHOR_SPECIFIC,
    verification_status=VerificationStatus.DISCREPANT,
    verification_note=(
        "Open Library lists DeVorss with first publication 1977, plus 1984 "
        "and 1991 printings; the specified 1978 first-paperback / (c)1965 "
        "lineage was not confirmed there. Resolve against the physical copy "
        "before admitting any transcription."
    ),
)


# Held in a separate stratum. Balliett is a historical precursor, not
# corroboration: shared marketing under "Pythagorean" is not evidence that
# two authors' constructs, reductions or semantic scopes agree.
BALLIETT_1908 = SourceEdition(
    edition_id="balliett-philosophy-of-numbers-1908",
    author="L. Dow Balliett",
    title="The Philosophy of Numbers: Their Tone and Colors",
    edition="1908 edition",
    publisher="unconfirmed",
    publication_year=1908,
    copyright_year=None,
    role=SourceRole.HISTORICAL_PRECURSOR,
    source_type=SourceType.PRIMARY,
    authority_scope=AuthorityScope.AUTHOR_SPECIFIC,
    verification_status=VerificationStatus.DISCREPANT,
    verification_note=(
        "The closest Open Library record for this author and title is a 1969 "
        "Mokelumne Hill Press printing -- a later reprint, excluded by policy "
        "as a corroborating source. A 1908 edition appears among the results "
        "but was not individually confirmed, and the publisher is unknown."
    ),
)


def declared_corpus() -> NumerologyCorpus:
    """Return corpus v1: two declared editions, zero transcribed passages.

    Compiling this yields an empty dictionary. That is the correct output
    until a paginated copy is ingested and passages are transcribed.
    """
    return build_corpus(
        CORPUS_ID,
        editions=[JORDAN_1978, BALLIETT_1908],
        passages=[],
    )
