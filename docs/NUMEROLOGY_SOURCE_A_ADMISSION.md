# 1E-N-SOURCE-A — Numerology denotation admitted (Juno Jordan)

**Date:** 2026-07-27
**Result:** Numerology's denotation layer is admitted. It is the **second
denoting system** in Representation 1E, so `concordance_ready()` is now `True`
and 1E-A can run.

This is a *source event*, not a code event: the capability gain rests on a
verified, appropriately-tiered source, not a new abstraction. Nothing was
fabricated to make the framework run — the discipline that gated gematria is the
same one that admitted this.

## The source

Juno Jordan, *Numerology: The Romance in Your Name (A Standard Work)*.
DeVorss & Company, **Eleventh Printing, 2003**, **ISBN 0-87516-227-4**
(copyright © 1965 J.F. Rowny Press; transferred to DeVorss 1988). Tier:
`primary_traditional` (licenses `MEANING`). Unlike the gematria value method —
which is *convention*, presupposed by every text and defined by none — Jordan
**defines**: her "Significance and Meaning of Numbers" chapter states each
number's denotation outright (watchword **Courage** for One … **Forgiveness**
for Nine, with positive/negative attribute lists).

## Copy verification (a digital surrogate, recorded as such)

The copy is the Internet Archive scan `numerology-the-romance-in-your-name`.
The framework's rule — *repository access is not copy verification* — was kept:
the copy-level checks were actually made, against the copy's own page images.

| Check | Evidence |
|---|---|
| Title page | leaf n4: *NUMEROLOGY / The Romance in Your Name / (A Standard Work) / Juno Jordan / DeVorss* |
| Copyright page | leaf n5: ISBN 0875162274, DeVorss 11th ptg 2003, ©1965 Rowny |
| Pagination | scan→printed map verified across 13 leaves (n30=p11 … n76=p57) |
| Manifestation exists (independent) | OpenLibrary ISBN 0875162274, DeVorss, work OL6095808W, 297pp |
| File hash | jp2.zip sha1 `62fa426f215a764dedeb5924831863930f89796d` |

This resolved the edition/pagination discrepancy `numerology_corpus_v1` flagged,
exactly as v1 instructed: *"resolve … from the title and copyright pages of the
copy transcribed, not by preferring a catalog."*

## Double transcription

The nine denotations were transcribed by two independent methods:
**transcriber A** = the repository machine OCR; **transcriber B** = a reading of
the page image. They agree on every watchword; the image is authoritative where
the OCR erred ("Co tors"→Colors, "Muisunderstanding"→Misunderstanding, and it
dropped "An Extrovert Number" on 8 and 9). This is a genuine double
transcription — two independent rendering pipelines, hash-compared — not one
transcription wearing two names.

## Construct and mapping

- **Quantity-independent.** Jordan states what a *number* means, not what one
  computed quantity means. A new `VALUE_ITSELF` sentinel keys the denotation to
  the reduced value itself; `lookup` applies it to any quantity that reduces to
  the value, and a quantity-specific entry always overrides it.
- **Construct equivalence: `computationally_equivalent`.** Jordan's Pythagorean
  chart (1=A-J-S … 9=I-R) and single-digit reduction match the code's arithmetic
  on values 1–9. Not `exact` — they differ on master-number handling, which the
  general chapter does not denote (so 11/22/33 compile to silence, correctly).
- **Ontology mapping: interpretive, made blind to Kamea.** Each denotation was
  placed on the shared ontology from Jordan's watchword and attribute lists
  alone, before Kamea's placements were consulted, so any concordance is earned.
  Coverage: 7 `domain`, 1 `dynamic` (5→expansion), 1 `behavioral_manifestation`
  (8→dominance). Every mapping is flagged `interpretive`; the null controls
  weight these down. The per-value basis is recorded in
  `numerology_corpus_v2.JORDAN_DENOTATIONS` for audit and revision.

## Verification

Compiles to **9 source-specific denotations**; `numerology_capabilities`
`concordance_eligible` is `True`; `admission.py` numerology/denotation is
`DENOTATION` + admitted; `concordance_ready()` is `True`. Live check: a subject
with life-path 5 (numerology `dynamic=expansion`) vs a Kamea `dynamic=expansion`
claim returns `relation=equivalent, agrees=True`. Full suite: **2144 passing.**

Six lattice tests that encoded "only Kamea denotes / concordance not ready" were
updated to the new state — the authors had flagged
`test_the_only_admitted_denotation_is_measurement_licensed` as the one a source
event must change.

## What is *not* claimed

- Not a physical copy — a digital surrogate, labelled as such.
- Not the deepest provenance of the letter-value chart, which Jordan credits
  upstream to L. Dow Balliett (a historical precursor, held in a separate
  stratum in the corpus, never joining a canonical consensus).
- Not quantity-specific meanings — Jordan's Heart's Desire / Personality /
  Destiny chapters remain un-transcribed; admitting them is future work.
- Not that numerology *agrees* with Kamea in general — only that the machinery
  to test it now runs on licensed evidence.
