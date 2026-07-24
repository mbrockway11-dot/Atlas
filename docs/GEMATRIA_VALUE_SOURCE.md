# 1E-G-VALUE-SOURCE — Admit One Hebrew Value Method

**Status:** open · **Type:** acquisition gate, not interpretation ·
**Blocks:** numeric evaluation, and therefore all of 1E-G-SOURCE-B/C ·
**Follows:** [1E-G-SOURCE-A](GEMATRIA_SOURCE_A.md)

1E-G-SOURCE-A licensed Hebrew letter *identity* from the Unicode standard. It
could not license letter *values*, because Unicode assigns Hebrew letters no
numeric value — values are a traditional claim needing a traditional source.

This gate has one objective:

> Admit **one** precisely specified Hebrew-letter value assignment from a
> **verified source copy**.

Nothing more. No corpus search, no equivalence, no symbolic interpretation.

The dependency correction that makes this a gate rather than a design task:

```text
Hebrew identity licensed
      ↓ value method unlicensed
      ↓ numeric value unavailable
      ↓ equivalence cannot be instantiated
```

Equivalence requires an admitted value method. Designing it first would be the
downstream-to-upstream pressure the feed-forward invariant forbids, so
1E-G-SOURCE-B stays closed until this gate passes.

---

## Required evidence

```text
verified source copy
printed-page locator
letter-value table or explicit rule
final-letter treatment
normalization scope
method name used by the source
independent transcription agreement
```

The machinery already exists. `gematria_value_method.ValueMethod` carries every
field, and its `__post_init__` **refuses admission** without a
`source_copy_hash` and `source_locator`. So a method compiled from a verified
copy admits automatically; one without a source cannot be admitted however
attested its values.

---

## The endpoint

```text
Hebrew letters
      ↓
licensed numeric values
```

And no further. When one method is admitted, `derive_gematria_capabilities`
flips `value_method_available` and `numeric_evaluation_available` to true, and
`direct_hebrew_value` begins returning totals — each carrying **both** the
orthography standard hash and the value method hash, enforced at the one place
a total is produced.

`equivalence_search_available` and `denotation_available` stay false: those are
1E-G-SOURCE-B and -C.

---

## What may not populate a method

The same exclusions as numerology:

- search-result snippets or catalog descriptions
- machine-extracted text without page verification
- a different printing whose pagination is attributed to the declared edition
- remembered or paraphrased letter values
- the shipped `mispar-hechrachi-candidate`, which is uncited and stays a
  candidate

The values of standard absolute gematria are widely known, which is exactly
why the discipline matters: knowing the answer is not a substitute for citing
it, and the candidate method exists to prove the machinery, not to be quietly
admitted.

---

## Status

Acquisition pending. Until a verified source copy exists, the branch is frozen
here — as numerology is — and the next active milestone is **1E-V-CLASSIFY**,
which decomposes Vedic astrology's admission without needing any source.

The boundary this phase established is permanent:

> A normative standard can establish what a symbol *is* without establishing
> what a tradition says that symbol is *worth*.
