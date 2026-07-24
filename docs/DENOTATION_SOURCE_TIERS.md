# Denotation Source Tiers and Acquisition Guidance

**Status:** governance reference · **Enforced by:**
`source_tiers.py`, `tests/test_source_tiers.py`

Different questions require different evidence. A source that answers one does
not answer another, so each source carries a **tier** that fixes what it may
license. Encoded as a matrix and enforced: a source may license only the claim
types its tier covers.

## The four tiers (plus inadmissible)

| Tier | Licenses | Best sources |
|---|---|---|
| **Normative standard** | symbol identity, encoding, computation | Unicode Standard, Swiss Ephemeris |
| **Primary traditional** | rules, methods, meanings, equivalence | historical texts/manuscripts of the tradition |
| **Scholarly reference** | context, variants, bibliography | academic books, critical editions, encyclopaedias |
| **Catalog / archive** | provenance of editions | WorldCat, Library of Congress, HathiTrust, Internet Archive |
| **Inadmissible** | *nothing* | AI summaries, Wikipedia, websites, angel-number sites, unsourced calculators, blogs, social media |

A **critical edition or scholarly translation of a primary text** is
`primary_traditional`, because it transmits the tradition's own claims.
`scholarly_reference` is for works that *describe* a tradition. An unknown
source is inadmissible until classified — silent unless admitted, at the source
level.

This validates every prior licensing decision: Unicode (normative) licensed
Hebrew letter identity, Swiss Ephemeris (normative) licensed the ayanamsa
offset, Open Library / WorldCat (catalog) established edition provenance and
nothing more. None of them could have licensed a meaning, and the matrix now
makes that structural.

---

## Acquisition guidance, by system

Recommended sources, recorded so acquisition targets the right tier. **None of
these is yet ingested**; this is a shopping list, not evidence.

### Numerology — verified primary sources, not websites

- Juno Jordan, *The Romance in Your Name* (once a verified edition is obtained)
- Florence Campbell
- Faith Javane & Dusty Bunker (modern, influential — if modern traditions are
  in scope)
- Earlier Western texts (Cheiro, etc.) if within scope

For each: verified edition, title page, copyright page, page numbers, and
direct passages **defining constructs** — not just examples.

### Gematria — three independent source needs

- **Letter values** — a source that *specifies* the mapping for the method
  being admitted (traditional Jewish reference works, classical discussions of
  *mispar hechrachi*, scholarly treatments), not one that merely uses it.
- **Transliteration** — a separate question, and the first admitted path avoids
  it by taking Hebrew script. If later admitted, use a published convention
  (ISO 259, ALA-LC, SBL) — those are orthographic standards (normative), *not*
  gematria authorities, and the tier matrix enforces that they cannot license
  a value.
- **Equivalence** — attested pairs from primary texts that discuss them, never
  modern web-generated lists.

### Vedic — the largest effort, each layer a different authority

- **Ayanamsa** — sources defining Lahiri, Raman, Krishnamurti, each justifying
  its reference frame.
- **House systems** — sources describing Whole Sign, Sripati, Bhava Chalit,
  rather than assuming one.
- **Dasha** — sources defining the Vimshottari sequence, period lengths, and
  starting rules.
- **Interpretation** — classical works: *Bṛhat Parāśara Horā Śāstra*, *Bṛhat
  Jātaka*, *Phaladīpikā*, *Jātaka Pārijāta*. Prefer critical editions or
  reputable scholarly translations, since these exist in multiple recensions.

### Bibliographic verification (every work)

Cross-check through independent catalogs — WorldCat, Library of Congress,
HathiTrust, Internet Archive, publisher records — matching the
work → manifestation → source-copy model already in place.

---

## Acquisition priority

1. **One verified gematria value-method source** — smallest acquisition,
   unlocks licensed Hebrew numeric evaluation. First non-Kamea system to move
   from licensed identity into licensed traditional computation.
2. **Numerology primary passages** — enables the first sourced denotations.
3. **Vedic SOURCE-A** — ayanamsa and house-system authorities (upstream of the
   other Vedic layers).
4. Remaining Vedic interpretive sources.

Shortest path from acquisition to a genuinely new capability, faithful to the
evidence-first architecture.
