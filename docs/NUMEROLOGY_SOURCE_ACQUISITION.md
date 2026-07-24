# 1E-N-SOURCE — Numerology Source Acquisition Gate

**Status:** open · **Type:** acquisition gate, not interpretation ·
**Blocks:** every numerology denotation, and therefore the Kamea–numerology
pilot

The numerology denotation architecture is complete through source declaration.
**No numerology denotations exist because no verified source copy has been
ingested. The resulting silence is intentional and correct.**

```text
declared works:                 2
transcription-eligible sources: 0
admissible passages:            0
compiled meanings:              0
```

That is the first successful production behaviour of the provenance system,
not a blocked implementation. The next step is acquisition, not interpretation.

---

## Why "edition" was not enough

A passage locator belongs to a particular **copy**, not to an abstract
edition. Two scans catalogued under one work can differ in front matter,
pagination, OCR, omitted pages, printing date and publisher statement. So
identity resolves at four levels, each with its own verdict:

```text
Work           author + title
Edition stmt   catalog wording ("first paperback", "New Ed", …)
Manifestation  publisher · date · ISBN/OCLC · pagination · format
Source copy    scan id · file hash · scan-page → printed-page map
```

Citations point at the **source-copy hash and printed page**, with the scan
page as a secondary reproducibility field.

### Catalog facts are not copy facts

```text
catalog_asserted              a catalog says so
cross_catalog_correlated      several catalogs agree
copy_title_page_verified      the title page was read
copy_copyright_page_verified  the copyright page was read
copy_pagination_verified      printed pagination was mapped
```

Only the last three are inspections. Repeating a claim across catalogs does
not make it a title page, and catalog conflicts are **never** resolved by
choosing one catalog as authoritative — they are resolved from the copy
eventually transcribed, or they remain unresolved.

---

## Current state of the two declared sources

### Jordan — *Numerology: The Romance in Your Name*

| level | status |
|---|---|
| work identity | **verified** |
| edition identity | **discrepant** |
| pagination identity | unresolved |
| transcription eligible | **no** |

Open Library catalogs a June 1977 DeVorss "New Ed" paperback, 297 pages, ISBN
`0875162274`. WorldCat catalogs what appears to be the same OCLC lineage as a
1978 first paperback edition, copyright 1965. Both are catalog assertions.
Resolve the publication year and pagination from the title and copyright pages
of the copy transcribed.

### Balliett — *The Philosophy of Numbers: Their Tone and Colors*

| level | status |
|---|---|
| work identity | **verified** |
| edition identity | unresolved |
| pagination identity | unresolved |
| transcription eligible | **no** |

The 1908 edition's existence is verified across Open Library and WorldCat,
publisher given as the author and L. N. Fowler. What is open is the precise
manifestation and its pagination, on which records disagree. Later reprints
(e.g. 1969 Mokelumne Hill Press) are excluded by policy as corroboration.

Balliett sits in the **historical precursor** stratum and compiles separately.
It can neither join a canonical consensus nor contradict a canonical entry.

---

## Acceptance requirements for one source copy

All eight, in order:

1. Full readable scan or physical copy obtained
2. Title page inspected
3. Copyright / publication page inspected
4. Printed pagination mapped to scan pages
5. Stable copy identifier and file hash recorded
6. **Quantity definitions located before number meanings**
7. Excerpts manually checked against the page image
8. No dictionary compilation until construct equivalence is established

Enforced in code: `Manifestation.transcription_eligible` requires all three
copy-level provenance levels plus verified edition and pagination identity,
and `AdmissibilityRules.rejection_reason` refuses any passage from an
ineligible manifestation before it looks at what the passage says.

---

## Order of work inside the book

```text
identify computation
      ↓
reproduce computation in code
      ↓
establish construct equivalence
      ↓
extract direct denotations
      ↓
compile dictionary
```

**Do not search first for "the meaning of 4."** First determine whether the
source's construct corresponding to the code's `life_path` exists at all and
is computed identically. A shared phrase is not evidence — that is what
`construct_equivalence` records, and only `exact` or
`computationally_equivalent` may compile.

---

## Passages may not be populated from

- search-result snippets
- catalog descriptions
- machine-extracted plain text without page verification
- a different printing whose pagination is silently attributed to the declared
  edition
- remembered or paraphrased number meanings

---

## Transcription discipline

Two independent transcribers per passage. Their renderings are hashed after
whitespace normalization and compared, so a disagreement about a *word* is
visible while a disagreement about line breaks is not. A disagreement blocks
compilation and is resolved against the page image — never by preferring one
transcriber.

---

## Silence is reported by reason

`completeness_report` distinguishes four states a bare empty dictionary would
conflate:

```text
no_source_copy             no verified copy has been ingested
no_matching_construct      the source's construct is not the code's
no_direct_denotation       the source discusses but never denotes
conflicting_denotations    admissible sources disagree
```

The current corpus reports exactly one: `no_source_copy`.

---

## Source-neutral work that may proceed meanwhile

Complete: manifestation and source-copy schemas, printed-page/scan-page
mapping, transcription hash stability, the merely-declared-edition guard,
copy-verification gating, double-transcription disagreement handling, and the
four-reason completeness report.

**The first real numerological coordinate must wait for a verified copy.**
