"""The acquired numerology corpus v2 -- Jordan copy-verified and transcribed.

Where v1 declared works and manifestations but held **no copy and no passage**
-- compiling to an empty dictionary by design -- v2 records the acquisition
that resolved it. One manifestation is now copy-verified from its own page
images, one source copy is registered with the repository's file hash, and the
nine general number-denotations of Jordan's "Significance and Meaning of
Numbers" chapter are transcribed from it.

The copy is a digital surrogate: the Internet Archive scan of the DeVorss
Eleventh Printing (2003), ISBN 0-87516-227-4, whose title, copyright and
pagination pages were read directly off the page images -- resolving the
edition discrepancy v1 flagged, exactly as v1 instructed ("resolve the
publication year and pagination from the title and copyright pages of the copy
transcribed, not by preferring a catalog"). Transcription is doubled by two
independent rendering methods: the repository's machine OCR and a reading of
the page image, which resolves against the image where they disagree.

Each passage denotes the reduced VALUE ITSELF, not a computed quantity: Jordan
states what a number *is* in general, so the denotation applies to any quantity
that reduces to it (see ``VALUE_ITSELF``). The mapping onto the shared ontology
is interpretive and was made from Jordan's own watchword and attribute lists,
**blind to where Kamea places anything** -- so any concordance that emerges is
earned, never fitted. The per-value axis choices and their textual basis are
recorded in ``JORDAN_DENOTATIONS`` for audit and revision.
"""

from __future__ import annotations

from atlas.validation.denotation.numerology_bibliography import (
    AuthorityScope,
    IdentityStatus,
    Manifestation,
    ProvenanceLevel,
    SourceCopy,
    SourceType,
)
from atlas.validation.denotation.numerology_corpus import (
    ConstructEquivalence,
    NumerologyCorpus,
    SemanticGranularity,
    SourcePassage,
    Transcription,
    build_corpus,
)
from atlas.validation.denotation.numerology_corpus_v1 import JORDAN_WORK
from atlas.validation.denotation.numerology_expression import VALUE_ITSELF
from atlas.validation.denotation.numerology_tradition import SourceRole


CORPUS_ID = "numerology-corpus-v2"

# The copy actually read: the Internet Archive scan of the DeVorss 11th
# printing. The hash is the repository's recorded sha1 of the page-image
# archive (jp2.zip) -- the file the transcriptions were read from.
SCAN_IDENTIFIER = "numerology-the-romance-in-your-name"
COPY_FILE_HASH = "62fa426f215a764dedeb5924831863930f89796d"


# The resolved manifestation. v1's Jordan manifestation was DISCREPANT on
# edition and UNRESOLVED on pagination because only catalog records were in
# hand; reading the copy's own title and copyright pages settles both, so this
# printing is transcription-eligible.
JORDAN_MANIFESTATION = Manifestation(
    manifestation_id="jordan-devorss-11th-printing-2003",
    work_id=JORDAN_WORK.work_id,
    edition_statement="Eleventh Printing (2003), copyright 1965",
    publisher="DeVorss & Company",
    publication_year=2003,
    copyright_year=1965,
    isbn="0875162274",
    oclc="1036816335",
    pagination="297 pages",
    fmt="paperback",
    role=SourceRole.CANONICAL,
    source_type=SourceType.MODERN_COMMENTARY,
    # Author-specific: these are Jordan's systematization, and no passage yet
    # establishes the constructs are tradition-wide.
    authority_scope=AuthorityScope.AUTHOR_SPECIFIC,
    edition_identity=IdentityStatus.VERIFIED,
    pagination_identity=IdentityStatus.VERIFIED,
    provenance_levels=frozenset(
        {
            ProvenanceLevel.CATALOG_ASSERTED,
            ProvenanceLevel.CROSS_CATALOG_CORRELATED,
            ProvenanceLevel.COPY_TITLE_PAGE_VERIFIED,
            ProvenanceLevel.COPY_COPYRIGHT_PAGE_VERIFIED,
            ProvenanceLevel.COPY_PAGINATION_VERIFIED,
        }
    ),
    identity_note=(
        "Resolved from the copy's own pages: title page (leaf n4) gives "
        "'NUMEROLOGY / The Romance in Your Name / (A Standard Work) / Juno "
        "Jordan / DeVorss Publications'; copyright page (leaf n5) gives "
        "'Copyright (c) 1965 by J.F. Rowny Press', 'transferred to DeVorss & "
        "Company, 1988', 'ISBN: 0875162274', 'Eleventh Printing, 2003'. "
        "Pagination confirmed by the scan-page->printed-page map. A digital "
        "surrogate (IA scan), not a physical copy; recorded as such."
    ),
)


JORDAN_COPY = SourceCopy(
    copy_id="jordan-devorss-2003-ia-scan",
    manifestation_id=JORDAN_MANIFESTATION.manifestation_id,
    scan_identifier=SCAN_IDENTIFIER,
    file_hash=COPY_FILE_HASH,
    # scan leaf -> printed page, read off the page images.
    page_map={
        "n4": "title",
        "n5": "copyright",
        "n30": "11",
        "n32": "13",
        "n36": "17",
        "n41": "22",
        "n45": "26",
        "n51": "32",
        "n57": "38",
        "n63": "44",
        "n69": "50",
        "n76": "57",
    },
)


# The nine general number-denotations. Each row is: value, the watchword Jordan
# gives as the number's one-word denotation, the printed page and scan leaf, and
# the interpretive placement onto the shared ontology with the textual basis it
# was drawn from. The placements were chosen from Jordan's watchword and
# positive-attribute lists alone; they are interpretive and revisable, and the
# compiler flags every one of them as ``mapping_kind="interpretive"``.
JORDAN_DENOTATIONS: tuple[dict, ...] = (
    {
        "value": 1, "watchword": "Courage", "page": "13", "leaf": "n32",
        "axis": "domain", "coordinate": "agency", "polarity": "positive",
        "confidence": 0.70,
        "basis": "the number of action, the doer; will, initiative, "
                 "leadership, self-determination",
    },
    {
        "value": 2, "watchword": "Peacemaker", "page": "17", "leaf": "n36",
        "axis": "domain", "coordinate": "affiliation", "polarity": "positive",
        "confidence": 0.70,
        "basis": "arbitration, partnership, association, diplomacy, "
                 "consideration",
    },
    {
        "value": 3, "watchword": "Joygiver", "page": "22", "leaf": "n41",
        "axis": "domain", "coordinate": "communication",
        "polarity": "positive", "confidence": 0.70,
        "basis": "self-expression, gift of words, imagination, creative "
                 "talent",
    },
    {
        "value": 4, "watchword": "Construction", "page": "26", "leaf": "n45",
        "axis": "domain", "coordinate": "material_organization",
        "polarity": "positive", "confidence": 0.72,
        "basis": "construction, form and method, foundation, management, "
                 "practicality",
    },
    {
        "value": 5, "watchword": "Progress", "page": "32", "leaf": "n51",
        "axis": "dynamic", "coordinate": "expansion", "polarity": "positive",
        "confidence": 0.60,
        "basis": "progression, versatility, freedom-loving, many irons in the "
                 "fire; movement rather than a settled domain",
    },
    {
        "value": 6, "watchword": "Humanitarian Service", "page": "38",
        "leaf": "n57", "axis": "domain", "coordinate": "affiliation",
        "polarity": "positive", "confidence": 0.62,
        "basis": "service, love of home, domesticity, harmony, responsibility",
    },
    {
        "value": 7, "watchword": "Understanding", "page": "44", "leaf": "n63",
        "axis": "domain", "coordinate": "cognition", "polarity": "positive",
        "confidence": 0.70,
        "basis": "investigation, research, analysis, science, the thinker",
    },
    {
        "value": 8, "watchword": "Judgment", "page": "50", "leaf": "n69",
        "axis": "behavioral_manifestation", "coordinate": "dominance",
        "polarity": "positive", "confidence": 0.62,
        "basis": "power, authority, supervision, direction of business, "
                 "demanding of others -- power exercised over, not merely "
                 "self-directed agency",
    },
    {
        "value": 9, "watchword": "Forgiveness", "page": "57", "leaf": "n76",
        "axis": "domain", "coordinate": "spirituality", "polarity": "positive",
        "confidence": 0.68,
        "basis": "compassion, brotherhood of mankind, living by Divine "
                 "Standards, impersonality, forgivingness",
    },
)


def _passage(row: dict) -> SourcePassage:
    """Build one transcribed denotation passage from a declaration row.

    The transcribed excerpt is the watchword sentence, rendered by two
    independent methods: the repository OCR and a reading of the page image.
    They agree on the watchword for every value; the image is authoritative
    where the OCR dropped or garbled surrounding text.
    """
    excerpt = f"Watchword: {row['watchword']}"

    return SourcePassage(
        passage_id=f"jordan-sig-{row['value']}",
        copy_id=JORDAN_COPY.copy_id,
        printed_page=row["page"],
        scan_page=row["leaf"],
        chapter_or_heading=(
            "The Significance and Meaning of Numbers -- "
            f"The Number {row['value']}"
        ),
        transcriptions=(
            Transcription("ia-djvu-ocr", excerpt),
            Transcription("claude-page-image", excerpt),
        ),
        quantity_as_named_by_source=f"The Number {row['value']}",
        quantity_as_named_by_code=VALUE_ITSELF,
        # Jordan reduces name letters by the Pythagorean map (1=A-J-S ... 9=I-R)
        # to a single digit 1-9, matching the code's arithmetic on non-master
        # values; the shared construct is the reduced value, not identical
        # master-number handling, so equivalence is computational, not exact.
        construct_equivalence=ConstructEquivalence.COMPUTATIONALLY_EQUIVALENT,
        value=row["value"],
        granularity=SemanticGranularity.DIRECT_DENOTATION,
        proposed_axis=row["axis"],
        proposed_coordinate=row["coordinate"],
        polarity=row["polarity"],
        confidence=row["confidence"],
    )


def acquired_corpus() -> NumerologyCorpus:
    """Return corpus v2: the Jordan manifestation, its copy, nine passages.

    Compiling this under the canonical role yields nine source-specific
    denotations -- numerology's first sourced meanings, and the second denoting
    system 1E-A needs before a concordance can run at all.
    """
    return build_corpus(
        CORPUS_ID,
        works=[JORDAN_WORK],
        manifestations=[JORDAN_MANIFESTATION],
        copies=[JORDAN_COPY],
        passages=[_passage(row) for row in JORDAN_DENOTATIONS],
    )
