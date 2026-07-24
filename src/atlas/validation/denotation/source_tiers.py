"""Source tiers: what a kind of source may legitimately license.

Different questions require different evidence, and a source that answers one
does not thereby answer another. A catalog can establish that an edition
exists; it cannot say what a number means. A normative standard can fix a
symbol's identity; it cannot license a tradition's interpretation of that
symbol. Encoding this as a matrix turns "use good sources" from advice into a
constraint: a source of a given tier may license only the claim types its tier
covers, and nothing else.

The four tiers, plus an explicit inadmissible tier for sources that may locate
references but never establish provenance:

    normative_standard    symbol identity, encoding, computation
    primary_traditional   rules, methods, meanings, equivalence
    scholarly_reference   context, variants, bibliography
    catalog_archive       provenance of editions only
    inadmissible          nothing

This validates every licensing decision the project has already made: Unicode
(normative) licensed Hebrew letter identity, Swiss Ephemeris (normative)
licensed the ayanamsa offset computation, and Open Library / WorldCat
(catalog) established edition provenance and nothing more. It also makes the
avoid-list -- AI summaries, encyclopaedias-as-primary, numerology websites --
structurally unable to license a method or a meaning.
"""

from __future__ import annotations

from enum import Enum


SOURCE_TIER_SCHEMA = "atlas.validation.denotation.source-tiers.v1"


class SourceTier(str, Enum):
    """What class of authority a source carries."""

    NORMATIVE_STANDARD = "normative_standard"
    PRIMARY_TRADITIONAL = "primary_traditional"
    SCHOLARLY_REFERENCE = "scholarly_reference"
    CATALOG_ARCHIVE = "catalog_archive"
    # May help locate an original reference, but never establishes provenance.
    INADMISSIBLE = "inadmissible"


class ClaimType(str, Enum):
    """What a source is being asked to license."""

    IDENTITY = "identity"          # what a symbol is
    ENCODING = "encoding"          # how it is encoded or formatted
    COMPUTATION = "computation"    # a defining constant or algorithm
    RULE = "rule"                  # a tradition's rule (exaltation, dasha)
    METHOD = "method"              # a tradition's method (a value table)
    MEANING = "meaning"            # a denotation
    EQUIVALENCE = "equivalence"    # an attested textual equivalence
    CONTEXT = "context"            # scholarly context
    VARIANT = "variant"            # textual variants, recensions
    PROVENANCE = "provenance"      # that an edition exists


# The licensing matrix. A source may license a claim type only if it appears
# here under the source's tier.
#
# A critical edition or scholarly translation of a primary text is classified
# PRIMARY_TRADITIONAL, because it transmits the tradition's own rules and
# meanings; SCHOLARLY_REFERENCE is for works that *describe* a tradition
# (encyclopaedias, secondary analyses), which license context and variants but
# not the tradition's claims themselves.
TIER_LICENSES: dict[SourceTier, frozenset[ClaimType]] = {
    SourceTier.NORMATIVE_STANDARD: frozenset(
        {ClaimType.IDENTITY, ClaimType.ENCODING, ClaimType.COMPUTATION}
    ),
    SourceTier.PRIMARY_TRADITIONAL: frozenset(
        {
            ClaimType.RULE,
            ClaimType.METHOD,
            ClaimType.MEANING,
            ClaimType.EQUIVALENCE,
        }
    ),
    SourceTier.SCHOLARLY_REFERENCE: frozenset(
        {ClaimType.CONTEXT, ClaimType.VARIANT, ClaimType.PROVENANCE}
    ),
    SourceTier.CATALOG_ARCHIVE: frozenset({ClaimType.PROVENANCE}),
    SourceTier.INADMISSIBLE: frozenset(),
}


# Sources the project has used or named, classified once so a later citation
# cannot quietly reclassify them. Keyed by a stable source id.
#
# Access-route principle: a platform that *hosts* primary texts (Sefaria,
# GRETIL, Internet Archive) is an access route, not a source of its content's
# tier. It is classified catalog_archive -- it licenses that a text is
# locatable there, nothing more. The primary work it hosts keeps its own
# primary_traditional tier, and a citation must name the *work* (with its
# verified edition and copy), never the platform, to license a meaning. So
# "the value is on Sefaria" cannot license a value; "Pardes Rimmonim, edition
# X, p. Y, obtained via Sefaria" can, once the copy chain is complete.
KNOWN_SOURCES: dict[str, SourceTier] = {
    # Normative standards -- identity and computation, never meaning.
    "unicode_standard": SourceTier.NORMATIVE_STANDARD,
    "swiss_ephemeris": SourceTier.NORMATIVE_STANDARD,
    "iso_259": SourceTier.NORMATIVE_STANDARD,
    "ala_lc_hebrew_romanization": SourceTier.NORMATIVE_STANDARD,
    "sbl_hebrew_transliteration": SourceTier.NORMATIVE_STANDARD,
    # Scholarly references -- context, variants, bibliography; never a rule,
    # method or meaning. The Jewish Encyclopedia describes mispar hechrachi
    # but, as a scholarly reference, cannot license the value table.
    "jewish_encyclopedia_1906": SourceTier.SCHOLARLY_REFERENCE,
    "jewish_languages_transliteration_guide": (
        SourceTier.SCHOLARLY_REFERENCE
    ),
    # Catalogs and access routes -- provenance / location only. The text
    # platforms sit here too: they help locate and read a work, but the work's
    # tier governs what may be licensed.
    "worldcat": SourceTier.CATALOG_ARCHIVE,
    "library_of_congress": SourceTier.CATALOG_ARCHIVE,
    "hathitrust": SourceTier.CATALOG_ARCHIVE,
    "internet_archive": SourceTier.CATALOG_ARCHIVE,
    "open_library": SourceTier.CATALOG_ARCHIVE,
    "google_books": SourceTier.CATALOG_ARCHIVE,
    "sefaria": SourceTier.CATALOG_ARCHIVE,
    "gretil": SourceTier.CATALOG_ARCHIVE,
    "sanskrit_documents": SourceTier.CATALOG_ARCHIVE,
    # Primary traditional works -- may license rules, methods, meanings,
    # equivalence. Classification is not admission: a specific passage from a
    # specific verified edition, double-transcribed, is still required before
    # any of these licenses anything.
    "pardes_rimmonim": SourceTier.PRIMARY_TRADITIONAL,
    "talmud": SourceTier.PRIMARY_TRADITIONAL,
    "brihat_parasara_hora_shastra": SourceTier.PRIMARY_TRADITIONAL,
    "brihat_jataka": SourceTier.PRIMARY_TRADITIONAL,
    "phaladipika": SourceTier.PRIMARY_TRADITIONAL,
    "jataka_parijata": SourceTier.PRIMARY_TRADITIONAL,
    # Inadmissible -- may locate a reference, never license one.
    "ai_generated_summary": SourceTier.INADMISSIBLE,
    "wikipedia": SourceTier.INADMISSIBLE,
    "numerology_website": SourceTier.INADMISSIBLE,
    "angel_number_site": SourceTier.INADMISSIBLE,
    "unsourced_gematria_calculator": SourceTier.INADMISSIBLE,
    "astrology_blog": SourceTier.INADMISSIBLE,
    "social_media_post": SourceTier.INADMISSIBLE,
}


# Text-hosting platforms among the catalog-tier entries. Documented so the
# access-route principle is legible: these provide text, but licensing is
# governed by the hosted work's tier, not by the platform.
ACCESS_ROUTES: frozenset[str] = frozenset(
    {
        "internet_archive",
        "hathitrust",
        "google_books",
        "sefaria",
        "gretil",
        "sanskrit_documents",
    }
)


class SourceTierError(ValueError):
    """A source was asked to license a claim outside its tier."""


def can_license(tier: SourceTier, claim: ClaimType) -> bool:
    """Return whether a tier may license a claim type."""
    return claim in TIER_LICENSES[tier]


def require_licensing(tier: SourceTier, claim: ClaimType) -> None:
    """Raise unless a tier may license a claim type.

    The enforcement point. A catalog record cannot be made to license a
    meaning, and a normative standard cannot be made to license a tradition's
    method, however convenient either would be.
    """
    if not can_license(tier, claim):
        licensed = ", ".join(sorted(c.value for c in TIER_LICENSES[tier]))
        raise SourceTierError(
            f"a {tier.value} source cannot license a {claim.value} claim; it "
            f"may license only: {licensed or 'nothing'}."
        )


def tier_of(source_id: str) -> SourceTier:
    """Return the tier of a known source.

    An unknown source is treated as inadmissible until classified, so a new
    source cannot license anything by default -- silent unless admitted, at
    the source level.
    """
    return KNOWN_SOURCES.get(source_id, SourceTier.INADMISSIBLE)
