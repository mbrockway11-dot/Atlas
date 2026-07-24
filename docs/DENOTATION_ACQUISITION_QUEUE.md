# Denotation Acquisition Queue — Candidate Online Sources

**Status:** acquisition reference · **These are locators, not evidence** ·
**Companion to:** [source tiers](DENOTATION_SOURCE_TIERS.md),
[acquisition protocol](DENOTATION_ACQUISITION_PROTOCOL.md)

Publicly accessible, citable resources for the acquisition phase, each
classified by what it may license. Every entry here is a **starting point for
the protocol**, not an admitted source: a URL is a locator, and admission still
requires the full chain (verify manifestation → verify copy → transcribe →
double-transcribe → construct equivalence → compile → capability gate).

Registered in `source_tiers.KNOWN_SOURCES`; the boundaries below are enforced,
not advisory.

## The access-route principle

A platform that *hosts* primary texts — Sefaria, GRETIL, Internet Archive — is
an **access route**, not a source of its content's tier. It is `catalog_archive`
(it licenses that a text is locatable there) and appears in
`source_tiers.ACCESS_ROUTES`. The hosted work keeps its own tier:

```text
"the value is on Sefaria"                              → cannot license a value
"Pardes Rimmonim, ed. X, p. Y, obtained via Sefaria"  → may license it,
                                                          once the copy chain is complete
```

So a citation must name the **work** (with its verified edition and copy),
never the platform.

## The queue, by tier

### Primary traditional — may license rules, methods, meanings

Located via the platforms below; each still needs a verified edition and copy.

- **Pardes Rimmonim** (Sha'ar HaGematria) — gematria value method / usage; via
  Sefaria
- **Talmud** — classical gematria usage; via Sefaria
- **Bṛhat Parāśara Horā Śāstra**, **Bṛhat Jātaka**, **Phaladīpikā**, **Jātaka
  Pārijāta** — Vedic rules and interpretation; via GRETIL / Sanskrit Documents,
  ideally in critical editions or respected translations

### Scholarly reference — context, variants, bibliography; never a method

- **Jewish Encyclopedia (1906), "Gematria"** (Internet Archive, Vol. 5,
  pp. 589–592) — describes standard methods including mispar hechrachi.
  Excellent context; **cannot** license the value table — a primary source
  must.
- **Jewish Languages transliteration guide** — compares ISO 259 / ALA-LC / SBL,
  explaining rather than mandating.

### Normative standards — identity and computation, never meaning

- **Unicode** — Hebrew letter identity, names, normalization (already in use)
- **Swiss Ephemeris** — astronomical computation (already in use); *not*
  Lahiri-vs-Raman, *not* interpretation

### Catalog / access route — provenance and location only

- **WorldCat**, **Library of Congress** — manifestations, editions, ISBNs
- **Internet Archive**, **HathiTrust**, **Google Books** — scans, title/copyright
  pages, pagination
- **Sefaria** — canonical Hebrew/English primary text, stable references,
  searchable; aligns closely with the `SourcePassage` model, but is an access
  route to works that retain their own tier
- **GRETIL**, **Sanskrit Documents** — Sanskrit editions for locating primary
  Jyotisha texts

## Recommended acquisition order

1. **Sefaria** — locate primary gematria references (Pardes Rimmonim, Talmud).
2. **Internet Archive** — obtain scans of the historical works.
3. **WorldCat** — verify the manifestation in hand.
4. **Unicode** — continue, orthography only.
5. **Swiss Ephemeris** — continue, astronomy only.

These five cover nearly every acquisition path the 1E architecture permits
without resorting to uncited tertiary websites.

## Numerology is the weakest online area

Most freely available numerology sites are exactly what the framework
classifies `inadmissible`. Digitized editions on Internet Archive, HathiTrust,
or Google Books (full/preview view) are the route — not numerology websites.
