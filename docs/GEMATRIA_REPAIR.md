# 1E-G-REPAIR — Fail-Closed Pre-Denotational Gematria

**Status:** complete · **Type:** defect repair, not licensing · **Produces:**
no denotations, no admitted schemes · **Follows:**
[1E-G-CLASSIFY](GEMATRIA_ADMISSION_CLASSIFICATION.md) · **Precedes:**
1E-G-SOURCE

1E-G-CLASSIFY found two defects that block gematria **before** any provenance
work: silent orthographic truncation, and a fused transliteration/value table.
Both are source-neutral — fixable without acquiring any book — so they are
repaired here while the findings are fresh.

The repair builds a **new** pipeline under `validation/denotation/`. Legacy
`atlas.ciphers` is untouched: it feeds `kamea/identity_graph` and five other
callers, and rewriting it is out of scope. It is quarantined from 1E instead,
as `evidence_from_number` is.

> Repair establishes that the pipeline can *represent* a scheme correctly. It
> does **not** establish that any scheme is authoritative. Both registries
> ship with **zero admitted schemes**.

---

## 1. Orthographic scope, fail-closed

`gematria_orthography.check_scope` replaces silent character dropping. Each
scheme declares its `accepted_scripts`, and two states the legacy code
serialized identically are now distinct:

```text
EMPTY_INPUT            the input had no characters
NO_LICENSED_SYMBOLS    the input had characters, none in scope
```

Hebrew input to a Latin scheme now reports `NO_LICENSED_SYMBOLS` with all four
rejected characters named, and `require_usable()` raises — where the legacy
`hebrew_literal_sequence` returned `[]`. The audit record carries
`input_length`, `accepted_symbol_count`, and every `rejected_symbol` with its
script.

`Gödel` survives: normalization strips the combining mark so `ö` counts as
Latin `o` rather than being dropped, closing the identity-encoder defect from
Identity 2A at the scope level.

---

## 2. The fused table, split

`gematria_transliteration` separates the two welded decisions into two
independently versioned, independently hashed artifacts:

```text
TransliterationScheme   Latin token -> candidate Hebrew letters
ValueAssignment         Hebrew letter -> numeric value
```

Transliteration is **candidate-valued**: a token may resolve to one letter,
several, or none. A token with several candidates and no declared resolution
**stops computation** — where the legacy greedy scanner silently took the
first match, manufacturing certainty. The legacy fused table is recovered into
this split form and registered **not admitted**, so its non-injective
collisions (U/V/W→vav, I/J/Y→yod, C/K→kaf, S/X→samekh, F/P→pe) are inspectable
rather than hidden.

The pipeline is:

```text
input
  ↓ orthographic validation
  ↓ transliteration        (admitted scheme required)
  ↓ letter identities
  ↓ value assignment       (admitted scheme required)
  ↓ numeric result
```

---

## 3. Names are provenance claims

The legacy `hebrew_literal_sequence` and `hebrew_phonetic_sequence` names
assert Hebrew provenance the behaviour lacks — neither reads Hebrew, and the
phonetic scheme is uncited. They are recorded in `LEGACY_CIPHER_QUARANTINE`
as present but not permitted in 1E. The new pipeline uses honest names, and
the legacy scheme it recovers is labelled `legacy-latin-fused-unsourced`.

---

## 4. Repair is not licensing

| layer | before | after 1E-G-REPAIR |
|---|---|---|
| orthographic_scope | not admitted (silent drop) | **admitted** — fail-closed, reproducible |
| transliteration | not admitted, fused | not admitted, **split and representable** |
| letter_value_assignment | not admitted, fused | not admitted, **split**, candidate held |
| numeric_computation | admitted in isolation | admitted in isolation |
| equivalence_relation | not implemented | not implemented |
| denotation | no corpus | no corpus |

English ordinal stays admitted as its own self-contained system: a fixed rule
over the Latin alphabet, no transliteration, no external authority. It is the
one path that runs end-to-end today.

The Hebrew path is fully implemented and **fail-closes at the admitted-scheme
gate**, because no scheme is admitted. A fixture scheme flagged admitted drives
it end-to-end in tests, proving the block is the gate working rather than
broken plumbing.

---

## 5. Frozen adversarial regressions

`tests/test_gematria_repair.py` freezes every defect:

```text
Hebrew-script input to a Latin scheme   -> NO_LICENSED_SYMBOLS, raises
empty string                            -> EMPTY_INPUT (distinct)
punctuation-only string                 -> NO_LICENSED_SYMBOLS (distinct)
Gödel                                    -> accepted, diacritic folded
mixed Latin/Hebrew                      -> Latin kept, Hebrew rejections named
U/V/W, I/J/Y collisions                 -> visible in the split
ambiguous token, no resolution          -> stops computation
CHAIM                                   -> no authoritative Hebrew result
```

For `CHAIM` no "correct" Hebrew value is asserted — none is licensed. The
assertion is only that the legacy mapping cannot present one.

---

## Result

Two source-neutral defects are closed. Gematria's orthographic scope and
numeric computation are now admitted **in isolation**; neither can feed a
denotation, because transliteration and value assignment between them remain
unlicensed. So gematria still denotes nothing, and `concordance_ready` stays
**false** — but the pipeline is now explicit, fail-closed, and ready for
1E-G-SOURCE to cite schemes into, rather than carrying a silent defect.

Next: **1E-G-SOURCE**, which acquires and verifies, separately, a
transliteration convention, a Hebrew value assignment, a comparison-corpus
policy, an equivalence relation, and only then denotation. Gematria may become
able to compute *licensed values* well before it can make any *denotational
claim*.
