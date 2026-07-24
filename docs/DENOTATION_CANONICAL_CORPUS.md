# Denotation Canonical Acquisition Corpus

**Status:** acquisition plan (checked) · **Nothing acquired** · **Enforced by:**
`acquisition_targets.py`, `tests/test_acquisition_targets.py`

The bottleneck is no longer finding sources but choosing a canonical corpus.
One source per phase, in dependency order — narrow on purpose, because
collecting several traditions at once is what turns acquisition back into an
architecture exercise.

> The value of a source is proportional to the number of capability gates it
> unlocks, not the number of pages it contains.

Each target names the gate it unlocks. The plan is machine-checked for
coherence: a target's required tier must be able to license the claim its gate
needs, caught now rather than after a copy is in hand. Every target is
`NOT_ACQUIRED`; a target advances only by running the
[acquisition protocol](DENOTATION_ACQUISITION_PROTOCOL.md) against a verified
copy.

## The three phases

### Phase 1 — Gematria (one source)

- **Work:** Pardes Rimmonim (Sha'ar HaGematria)
- **Licenses:** method (the value table) — `primary_traditional`
- **Unlocks:** `value_method_available → numeric_evaluation_available`; the
  first non-Kamea move from licensed identity into licensed traditional
  computation
- **Located via:** Sefaria · **Verified via:** WorldCat, then a scan
- **Success criterion:** one admitted value method. Nothing about denotation.

### Phase 2 — Numerology (one corpus)

- **Work:** Juno Jordan, *The Romance in Your Name* (the machinery was built
  with this target in mind)
- **Licenses:** meaning — `primary_traditional`
- **Unlocks:** the first sourced numerology denotations; the first path toward
  a second independently denoting system
- **Located via:** Internet Archive / HathiTrust · **Verified via:** WorldCat
- **Acquire:** verified manifestation, verified copy, direct construct
  passages — not examples.

### Phase 3 — Vedic SOURCE-A (dependency order)

- **Work:** one ayanamsa authority *(not yet chosen — placeholder in the
  corpus, correctly showing an inadmissible work tier until named)*, then one
  house-system authority
- **Licenses:** rule — `primary_traditional`
- **Unlocks:** ayanamsa admitted → sidereal quantities become licensed; the
  upstream gate that unblocks every downstream Vedic layer
- **Do not** collect BPHS, Phaladīpikā and the rest simultaneously — without
  coordinate authority they cannot produce admitted output.

## Catalog vs repository

A refinement within the `catalog_archive` tier — **not** a fifth tier, enforced
by `catalog_role`:

| Role | Resources | Provides |
|---|---|---|
| catalog | WorldCat, Library of Congress, Open Library | manifestation **discovery** |
| repository | Internet Archive, HathiTrust, Google Books, Sefaria, GRETIL, Sanskrit Documents | **access** to a copy/text |

Both license provenance only. The distinction carries its own discipline:
**repository access is not copy verification.** A scan on Internet Archive or a
text on Sefaria is something to *verify* — the title-page, copyright-page and
pagination checks still have to be made. A target located via a repository
stays `NOT_ACQUIRED` until that chain completes.

## The week-one manifest

The goal of the first acquisition week is exactly four artifacts:

1. A verified copy of the chosen **Pardes Rimmonim** edition (or another single
   chosen gematria source if it better fits scope).
2. A verified copy of one **Juno Jordan** work.
3. A verified edition for one chosen **ayanamsa** authority.
4. A **manifest** recording, for each: edition metadata, page ranges, file
   hashes, and acquisition provenance.

The manifest is populated by the protocol, not now — its fields are exactly the
existing `Manifestation` and `SourceCopy` dataclasses plus an
`AcquisitionStatus`. Nothing else. Each artifact feeds directly into a gate
that already exists; there is no speculative acquisition and no new
architecture.
