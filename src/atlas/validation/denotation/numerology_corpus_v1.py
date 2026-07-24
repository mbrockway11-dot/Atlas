"""The declared numerology corpus v1 — works and manifestations, no copies.

Two works are declared. **No source copy has been ingested and no passage has
been transcribed**, so the corpus compiles to an empty dictionary.

That is the provenance system working, not a blocked implementation::

    declared works:              2
    transcription-eligible:      0
    admissible passages:         0
    compiled meanings:           0

Bibliographic identity is resolved separately at each level, because
collapsing them discards what *is* settled:

* **Jordan** — the work is verified; the manifestation is discrepant. Open
  Library catalogs a June 1977 DeVorss "New Ed" paperback, 297 pages, ISBN
  0875162274; WorldCat catalogs what appears to be the same OCLC lineage as a
  1978 first paperback edition with copyright 1965. Both are catalog
  assertions. Neither is a title page, and the conflict is not resolved by
  choosing a catalog -- it is resolved from the copy eventually transcribed.

* **Balliett** — the *work* is verified: a 1908 edition is independently
  represented in Open Library and WorldCat, with publisher information given
  as the author and L. N. Fowler. What remains unresolved is the precise
  manifestation and its pagination, on which catalog records disagree. So
  ``work_identity`` is verified while ``edition_identity`` and
  ``pagination_identity`` are not, and the manifestation is not
  transcription-eligible.

Passages may not be populated from search-result snippets, catalog
descriptions, machine-extracted text without page verification, a different
printing whose pagination is silently attributed to the declared edition, or
remembered number meanings.
"""

from __future__ import annotations

from atlas.validation.denotation.numerology_bibliography import (
    AuthorityScope,
    IdentityStatus,
    Manifestation,
    ProvenanceLevel,
    SourceType,
    Work,
)
from atlas.validation.denotation.numerology_corpus import (
    NumerologyCorpus,
    build_corpus,
)
from atlas.validation.denotation.numerology_tradition import SourceRole


CORPUS_ID = "numerology-corpus-v1"


JORDAN_WORK = Work(
    work_id="jordan-romance-in-your-name",
    author="Juno Jordan",
    title="Numerology: The Romance in Your Name",
    work_identity=IdentityStatus.VERIFIED,
    identity_note=(
        "Represented in both Open Library and WorldCat under DeVorss."
    ),
)


BALLIETT_WORK = Work(
    work_id="balliett-philosophy-of-numbers",
    author="L. Dow Balliett",
    title="The Philosophy of Numbers: Their Tone and Colors",
    work_identity=IdentityStatus.VERIFIED,
    identity_note=(
        "A 1908 edition is independently represented in Open Library and "
        "WorldCat, publisher given as the author and L. N. Fowler."
    ),
)


# The canonical source for the code-facing dictionary. One author and one
# manifestation, deliberately: drawing on several modern manuals at once would
# manufacture consensus out of heterogeneous sources marketed under one word.
JORDAN_MANIFESTATION = Manifestation(
    manifestation_id="jordan-devorss-paperback-1977-1978",
    work_id=JORDAN_WORK.work_id,
    edition_statement='"New Ed" (Open Library) / "1st paperback" (WorldCat)',
    publisher="DeVorss",
    publication_year=None,
    copyright_year=1965,
    isbn="0875162274",
    oclc="1036816335",
    pagination="297 pages (Open Library)",
    fmt="paperback",
    role=SourceRole.CANONICAL,
    source_type=SourceType.MODERN_COMMENTARY,
    # Author-specific until passages establish that the constructs are
    # tradition-wide rather than this author's systematization.
    authority_scope=AuthorityScope.AUTHOR_SPECIFIC,
    edition_identity=IdentityStatus.DISCREPANT,
    pagination_identity=IdentityStatus.UNRESOLVED,
    provenance_levels=frozenset(
        {
            ProvenanceLevel.CATALOG_ASSERTED,
            ProvenanceLevel.CROSS_CATALOG_CORRELATED,
        }
    ),
    identity_note=(
        "Open Library: June 1977 DeVorss 'New Ed' paperback, 297 pp, ISBN "
        "0875162274. WorldCat: apparently the same OCLC lineage as a 1978 "
        "first paperback edition, copyright 1965. Both are catalog "
        "assertions; resolve the publication year and pagination from the "
        "title and copyright pages of the copy transcribed, not by "
        "preferring a catalog."
    ),
)


# Held in a separate stratum. Balliett is a historical precursor, not
# corroboration: shared marketing under "Pythagorean" is not evidence that two
# authors' constructs, reductions or semantic scopes agree.
BALLIETT_MANIFESTATION = Manifestation(
    manifestation_id="balliett-1908",
    work_id=BALLIETT_WORK.work_id,
    edition_statement="1908 edition",
    publisher="the author and L. N. Fowler",
    publication_year=1908,
    copyright_year=None,
    isbn="",
    oclc="",
    pagination="disputed across catalog records",
    fmt="unknown",
    role=SourceRole.HISTORICAL_PRECURSOR,
    source_type=SourceType.PRIMARY,
    authority_scope=AuthorityScope.AUTHOR_SPECIFIC,
    # The work exists; which manifestation and pagination remain open.
    edition_identity=IdentityStatus.UNRESOLVED,
    pagination_identity=IdentityStatus.UNRESOLVED,
    provenance_levels=frozenset(
        {
            ProvenanceLevel.CATALOG_ASSERTED,
            ProvenanceLevel.CROSS_CATALOG_CORRELATED,
        }
    ),
    identity_note=(
        "The 1908 edition's existence is verified across catalogs. The "
        "precise manifestation and pagination are not; records disagree on "
        "page counts, and later reprints (e.g. 1969 Mokelumne Hill Press) "
        "are excluded by policy as corroborating sources."
    ),
)


def declared_corpus() -> NumerologyCorpus:
    """Return corpus v1: works and manifestations, no copies, no passages.

    Compiling this yields an empty dictionary. That is the correct output
    until a copy is acquired, its title, copyright and pagination pages are
    inspected, and passages are doubly transcribed from it.
    """
    return build_corpus(
        CORPUS_ID,
        works=[JORDAN_WORK, BALLIETT_WORK],
        manifestations=[JORDAN_MANIFESTATION, BALLIETT_MANIFESTATION],
        copies=[],
        passages=[],
    )
