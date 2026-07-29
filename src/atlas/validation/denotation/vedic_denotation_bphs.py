"""The acquired Vedic graha corpus -- BPHS copy-verified and transcribed.

Where ``vedic_denotation.declared_corpus`` names Brihat Parasara Hora Shastra
but holds no copy and no passage, this module records the acquisition that
populates it (1E-V-SOURCE-B). One manifestation is copy-verified from its own
pages, one source copy is registered with the repository's file hash, and the
seven classical grahas' karakatva -- the defining verse 12-13, "Planetary
Governances" -- are transcribed from it.

The copy is a digital surrogate: the Internet Archive scan of R. Santhanam's
English translation (Ranjan Publications, New Delhi, Vol. I). Its title page,
translator's dated preface and pagination were read off the page images; this
edition carries its edition statement on the title page and its date (Vijaya
Dashami 1984) in the translator's preface rather than on a separate copyright
leaf, corroborated by WorldCat OCLC 12808639. A scholarly translation of a
primary text is primary_traditional: it transmits the tradition's own rules and
meanings.

Transcription is doubled by two independent rendering methods -- the
repository's machine OCR and a reading of the page image -- which agree on the
verse. The ontology mapping is interpretive and was made from BPHS's own
karakatva words, **blind to where Kamea places anything**, so any concordance
is earned. Rahu and Ketu are not covered: verse 12-13 governs the seven
star-planets, which is exactly the set the lagna-lord quantity produces, so the
coverage is complete for v1.
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
from atlas.validation.denotation.numerology_corpus import Transcription
from atlas.validation.denotation.numerology_tradition import SourceRole
from atlas.validation.denotation.vedic_denotation import (
    BPHS_WORK,
    GrahaDictionary,
    GrahaPassage,
    GrahaSemanticGranularity,
    VedicCapabilities,
    VedicGrahaCorpus,
    compile_graha_dictionary,
    derive_vedic_capabilities,
)


CORPUS_ID = "vedic-graha-corpus-v2"
SCAN_IDENTIFIER = "brihatparasarahorashastrabyr.santhanam"
COPY_FILE_HASH = "009466620461fc53721ab9fdffbc759759818214"


BPHS_SANTHANAM = Manifestation(
    manifestation_id="bphs-santhanam-ranjan-1984-vol1",
    work_id=BPHS_WORK.work_id,
    edition_statement=(
        "English translation, commentary and editing by R. Santhanam, Vol. I"
    ),
    publisher="Ranjan Publications, New Delhi",
    publication_year=1984,
    copyright_year=1984,
    isbn="",
    oclc="12808639",
    pagination="Vol. I (45 of 97 chapters)",
    fmt="hardcover",
    role=SourceRole.CANONICAL,
    # A scholarly translation of a primary text.
    source_type=SourceType.PRIMARY,
    authority_scope=AuthorityScope.TRADITION_WIDE,
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
        "Resolved from the copy's own pages: title page (leaf n0) gives "
        "'Brihat Parasara Hora Shastra / Vol. I / English Translation, "
        "Commentary, Annotation and Editing By R. Santhanam / Ranjan "
        "Publications, New Delhi'; the translator's preface (leaf n5) is dated "
        "Vijaya Dashami 1984 and names the Sitaram Jha (Chaukhambha) Sanskrit "
        "edition as its base text; the contents place Ch. 3 'Planetary "
        "Characters and Description' at p. 8, and the karakatva verse 12-13 was "
        "read on p. 11. This edition carries no separate copyright leaf -- its "
        "edition statement is on the title page and its date in the dated "
        "preface -- corroborated by WorldCat OCLC 12808639. A digital "
        "surrogate (IA scan), recorded as such."
    ),
)


BPHS_COPY = SourceCopy(
    copy_id="bphs-santhanam-ia-scan",
    manifestation_id=BPHS_SANTHANAM.manifestation_id,
    scan_identifier=SCAN_IDENTIFIER,
    file_hash=COPY_FILE_HASH,
    page_map={
        "n0": "title",
        "n5": "preface",
        "n20": "11",
        "n29": "20",
        "n34": "25",
        "n37": "28",
    },
)


# The seven classical grahas of verse 12-13 ("Planetary Governances"). Each row
# is: graha, the exact clause of the verse that denotes it, and the interpretive
# placement onto the shared ontology with the karakatva word it was drawn from.
# The placements were chosen from BPHS's own words, blind to Kamea; the compiler
# flags every one as ``mapping_kind="interpretive"``.
GRAHA_DENOTATIONS: tuple[dict, ...] = (
    {
        "graha": "sun", "clause": "The Sun is the soul of all",
        "axis": "domain", "coordinate": "agency", "polarity": "neutral",
        "basis": "soul of all (atman): the self, identity, vitality, authority",
    },
    {
        "graha": "moon", "clause": "The Moon is the mind",
        "axis": "domain", "coordinate": "cognition", "polarity": "neutral",
        "basis": "the mind (manas): mentation, perception",
    },
    {
        "graha": "mars", "clause": "Mars is one's strength",
        "axis": "domain", "coordinate": "conflict", "polarity": "positive",
        "basis": "one's strength (bala): valour, energy, the warrior",
    },
    {
        "graha": "mercury", "clause": "Mercury is speech-giver",
        "axis": "domain", "coordinate": "communication", "polarity": "neutral",
        "basis": "speech-giver (vak): speech, articulation, intellect",
    },
    {
        "graha": "jupiter",
        "clause": "Jupiter confers Knowledge and happiness",
        "axis": "domain", "coordinate": "cognition", "polarity": "positive",
        "basis": "confers knowledge (jnana) and happiness: wisdom, learning",
    },
    {
        "graha": "venus", "clause": "Venus governs semen (potency)",
        "axis": "domain", "coordinate": "affiliation", "polarity": "positive",
        "basis": "governs potency: union, procreation, pleasure",
    },
    {
        "graha": "saturn", "clause": "Saturn denotes grief",
        "axis": "dynamic", "coordinate": "contraction", "polarity": "negative",
        "basis": "denotes grief: sorrow, restriction, limitation",
    },
)


CHAPTER_HEADING = (
    "Planetary Characters and Description (Ch. 3), v. 12-13 -- "
    "Planetary Governances"
)


def _passage(row: dict) -> GrahaPassage:
    """Build one transcribed karakatva passage from a declaration row.

    The transcribed excerpt is the verse clause that denotes the graha,
    rendered by two independent methods: the repository OCR and a reading of
    the page image, which agree.
    """
    clause = row["clause"]

    return GrahaPassage(
        passage_id=f"bphs-graha-{row['graha']}",
        graha=row["graha"],
        copy_id=BPHS_COPY.copy_id,
        printed_page="11",
        scan_page="n20",
        chapter_or_heading=CHAPTER_HEADING,
        transcriptions=(
            Transcription("ia-djvu-ocr", clause),
            Transcription("claude-page-image", clause),
        ),
        granularity=GrahaSemanticGranularity.KARAKATVA,
        proposed_axis=row["axis"],
        proposed_coordinate=row["coordinate"],
        polarity=row["polarity"],
        confidence=0.65,
    )


def acquired_corpus() -> VedicGrahaCorpus:
    """Return the Vedic graha corpus v2: BPHS, its copy, seven karakatvas.

    Compiling this yields seven source-specific graha denotations -- Vedic's
    first sourced meanings, and the third denoting system 1E-A can compare.
    """
    return VedicGrahaCorpus(
        corpus_id=CORPUS_ID,
        works=(BPHS_WORK,),
        manifestations=(BPHS_SANTHANAM,),
        copies=(BPHS_COPY,),
        passages=tuple(_passage(row) for row in GRAHA_DENOTATIONS),
    )


def canonical_dictionary() -> GrahaDictionary:
    """Compile the acquired corpus -- the bound live Vedic graha dictionary."""
    return compile_graha_dictionary(acquired_corpus())


def canonical_capabilities() -> VedicCapabilities:
    """Return the capability flags derived from the acquired corpus."""
    return derive_vedic_capabilities(acquired_corpus(), canonical_dictionary())


def is_concordance_eligible() -> bool:
    """Return whether the bound Vedic graha dictionary may enter a concordance."""
    return canonical_capabilities().concordance_eligible
