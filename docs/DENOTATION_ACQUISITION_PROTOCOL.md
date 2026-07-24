# Denotation Source Acquisition Protocol

**Status:** operational protocol (lab manual) · **Audience:** a researcher
admitting a new source, not necessarily the person who built the framework ·
**Companion to:** [source tiers](DENOTATION_SOURCE_TIERS.md),
[acquisition phase](DENOTATION_ACQUISITION_PHASE.md)

The framework is complete. What remains is evidence work, and this document
makes that work reproducible: a step-by-step procedure for moving one source
from "a book that exists" to "an admitted, capability-granting artifact",
where every step has a mechanical gate that either passes or produces honest
silence.

Nothing here licenses a shortcut. Each stage names the code that enforces it,
so the protocol cannot drift from what the software actually checks.

---

## Roles

- **Locator** — establishes the work and manifestation from catalogs.
- **Transcriber A / Transcriber B** — independently transcribe passages from
  the same source copy. They do not compare notes before submitting.
- **Compiler operator** — runs the compiler and reads the report; never edits
  a citation to make it compile.

One person may hold several roles across *different* sources, but Transcriber A
and B must be different people for any single passage — the disagreement check
is worthless otherwise.

---

## The chain

Each stage: **do**, **accept when**, **enforced by**, **silence if**.

### 1. Locate the work

- **Do:** identify author and title; confirm the work exists independently of
  any single catalog.
- **Accept when:** the work appears in at least two independent catalogs
  (WorldCat, Library of Congress, HathiTrust, Internet Archive, Open Library).
- **Enforced by:** `Work.work_identity` (numerology) / edition records.
- **Silence if:** only one catalog, or only tertiary mentions — `work_identity`
  stays unverified.

> Catalogs are tier `catalog_archive`: they license **provenance only**. A
> catalog can tell you the book exists; it cannot tell you what the book says.
> `source_tiers.require_licensing` enforces this.

### 2. Verify the manifestation

- **Do:** pin the specific printing — publisher, year, ISBN/OCLC, pagination,
  format.
- **Accept when:** the manifestation is settled at edition and pagination
  level, *from the copy itself*, not by preferring one catalog over another.
- **Enforced by:** `Manifestation.edition_identity`,
  `Manifestation.pagination_identity`.
- **Silence if:** catalogs disagree and no copy resolves them — record
  `DISCREPANT`, do not choose. (This is the real state of the Jordan and
  Balliett editions today.)

### 3. Verify the copy

- **Do:** obtain a full scan or physical copy; inspect the title page, the
  copyright page, and map printed pages to scan pages; record a file hash.
- **Accept when:** all three copy-level checks are done —
  `copy_title_page_verified`, `copy_copyright_page_verified`,
  `copy_pagination_verified`.
- **Enforced by:** `Manifestation.transcription_eligible` (requires all three
  plus verified identity); `SourceCopy.file_hash`.
- **Silence if:** any check missing — the manifestation is not
  transcription-eligible and no passage may cite it.

> A catalog assertion, however many catalogs repeat it, is **not** a title
> page. `ProvenanceLevel` separates `catalog_asserted` /
> `cross_catalog_correlated` (claims) from the three `copy_*_verified`
> (inspections). Only inspections confer eligibility.

### 4. Transcribe

- **Do:** transcribe the exact passage, with printed-page and scan-page
  locators and the verbatim excerpt.
- **Accept when:** the passage carries a locator and a transcriber.
- **Enforced by:** `SourcePassage.__post_init__` (rejects missing provenance).
- **Silence if:** paraphrase, snippet, or machine-extracted text without page
  verification — inadmissible input, never transcribe from it.

### 5. Double transcription

- **Do:** Transcriber A and B submit independently; the framework compares
  whitespace-normalized hashes.
- **Accept when:** the two transcriptions agree exactly.
- **Enforced by:** `SourcePassage.transcriptions_agree`; the compiler blocks a
  disagreeing passage.
- **Silence if:** they disagree — resolve against the page image, never by
  choosing one transcriber.

### 6. Construct identification

- **Do:** determine what the source's construct *is*, and whether it is the
  construct the code computes. Record both names.
- **Accept when:** `construct_equivalence` is `exact` or
  `computationally_equivalent`, established by comparing the source's stated
  computation to the code's, not by a shared phrase.
- **Enforced by:** `AdmissibilityRules` (only those two verdicts compile);
  `quantity_as_named_by_source` vs `quantity_as_named_by_code`.
- **Silence if:** `terminology_only`, `partially_equivalent`, `not_equivalent`,
  or `unresolved` — a shared word ("life path", "gematria") is not evidence.

> **Order matters inside the book.** Identify the computation, reproduce it in
> code, establish equivalence — *then* extract meanings. Never search first for
> "the meaning of 4" or "what Ketu signifies."

> **Standing question — define or presuppose?** Before a source is admitted for
> any construct, ask: *does this source establish the rule, or assume a rule
> established elsewhere?* A source that presupposes the construct is evidence of
> **usage**, not of the **definition**, and citing it to license the definition
> is mis-targeting. The P1 integration test caught exactly this: Pardes
> Rimmonim and the Talmud *use* gematria values without defining them, so they
> license equivalence, not the value table. Apply this to every source in every
> tradition — numerology and Jyotiṣa included — before acquisition, not after.

### 7. Semantic granularity

- **Do:** tag each statement as `direct_denotation`, `analogy`,
  `correspondence`, `recommendation`, `prediction`, or `commentary`.
- **Accept when:** the statement is a `direct_denotation` (for the concordance
  phase, 1E-A). Behavioural claims wait for 1E-B.
- **Enforced by:** `AdmissibilityRules.allowed_granularities`.
- **Silence if:** anything else — "4 signifies stability" is eligible; "people
  with 4 become reliable administrators" is a prediction, not a denotation.

### 8. Check the source tier

- **Do:** classify the source and confirm its tier may license the claim being
  made.
- **Accept when:** the tier covers the claim type — `primary_traditional` for
  a rule, method, meaning, or equivalence; `normative_standard` for identity or
  computation; `catalog_archive` for provenance only.
- **Enforced by:** `source_tiers.require_licensing`.
- **Silence if:** the source is `inadmissible` (AI summaries, Wikipedia,
  websites, unsourced calculators, blogs, social media) or an unknown source
  (inadmissible by default). A transliteration standard (ISO 259, ALA-LC, SBL)
  is `normative_standard` — it licenses orthography, never a value.

### 9. Compile

- **Do:** run the compiler over the corpus under the frozen admissibility
  rules.
- **Accept when:** the conflict verdict is `consensus` or `source_specific`.
  The verdict is *derived* from the admissible passages, never declared.
- **Enforced by:** `compile_dictionary`; `ConflictVerdict`.
- **Silence if:** `conflicting` (sources disagree), `insufficient` (too little
  evidence), or `none`. Silence is preferred to a forced reconciliation, and
  the completeness report says *which* silence it is.

### 10. Capability gate

- **Do:** derive capabilities from the compiled artifacts.
- **Accept when:** every upstream flag is true **and** the corpus, rules, and
  artifact hashes all agree.
- **Enforced by:** `derive_capabilities` (numerology),
  `derive_gematria_capabilities`; `concordance_eligible` /
  `numeric_evaluation_available`.
- **Silence if:** any flag false or any hash mismatched — a non-empty
  dictionary describing stale evidence is **not** eligible.

### 11. Regression tests

- **Do:** run the full suite; confirm the new admission did not regress a gate,
  and add adversarial cases for the new source.
- **Accept when:** the suite is green and the new source has both a positive
  test (it admits) and negative tests (a defective version is refused).
- **Enforced by:** the test suite; the lattice, quarantine, and laundering
  tests must still pass.
- **Silence if:** any gate regressed — the admission is not complete.

---

## The two independent axes

A source moves a system along **both** axes, and neither implies the other:

```text
capability axis   measurement → computation → identity → value →
                  equivalence → denotation → concordance

evidence axis     inadmissible → catalog → scholarly reference →
                  primary traditional → normative standard
```

A high evidence tier does not grant every capability (Swiss Ephemeris is
normative yet licenses no meaning); a high capability stage does not require
the top tier (Kamea denotes by measurement, needing no source). Check the cell,
not the axis.

---

## Anti-patterns — do not do these

- Transcribe from a snippet, catalog description, or machine OCR without page
  verification.
- Attribute one printing's pagination to a different declared edition.
- Admit a value or meaning because it is "well known" — knowing the answer is
  not citing it.
- Let a `catalog_archive` source license a meaning, or a `normative_standard`
  license a method. The matrix refuses this; do not route around it.
- Reconcile disagreeing sources informally. Record the conflict; it licenses
  silence.
- Rename a construct to force equivalence. A shared phrase is not a shared
  construct.
- Edit a citation to make the compiler pass.

---

## A dry run: gematria value method (the recommended first target)

To illustrate, *without* performing it (no verified copy is in hand):

1. Locate a work that **specifies** the *mispar hechrachi* value table — a
   traditional Jewish reference or a scholarly treatment that states the
   mapping, tier `primary_traditional`.
2. Verify the manifestation and copy (steps 2–3).
3. Transcribe the passage stating the letter→value mapping; double-transcribe.
4. Establish construct equivalence: the source's method must be the code's
   `ValueMethod` computation (absolute sum, final-letter policy, etc.).
5. Compile a `ValueMethod` with the source's `source_copy_hash` and
   `source_locator`; it admits automatically because those fields are present.
6. `derive_gematria_capabilities` flips `value_method_available` and
   `numeric_evaluation_available` to true; `direct_hebrew_value` begins
   returning totals, each carrying both provenance hashes.

Outcome: gematria moves from **licensed identity** to **licensed traditional
computation** — the first non-Kamea capability gain — and still denotes
nothing. That waits for 1E-G-SOURCE-B and -C.

---

## What this protocol is for

It exists so that the next capability gain is a **source event, not a code
event**. When someone brings a verified, appropriately-tiered source, this
procedure and the gates it names decide — mechanically — whether it admits,
what it licenses, and what stays silent. That decision no longer depends on the
judgement of whoever holds the source.
