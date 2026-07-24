# 1E-G-SOURCE-A — Hebrew Orthography and Value Method

**Status:** complete · **Type:** source licensing (identity only) ·
**Produces:** licensed letter identities, no values, no meanings · **Follows:**
[1E-G-REPAIR](GEMATRIA_REPAIR.md) · **Precedes:** 1E-G-SOURCE-B (comparison
corpus and equivalence)

Narrow by design. The job is to license **one exact path from Hebrew symbols
to letter identities**, structure the value method precisely, and stop. No
values are admitted, no equivalence, no denotation.

The endpoint distinguishes three claims that legacy gematria collapses:

```text
the input is in scope           ← 1E-G-REPAIR
the letters are identified       ← licensed here, by Unicode
the value was computed           ← NOT licensed: no traditional source
```

---

## Direct Hebrew first, not transliteration

The first admitted path runs on **Hebrew script**, so it does not rest on an
editorial Latin-to-Hebrew convention. Latin input is blocked in this path.
Transliteration remains a separately sourced convenience layer, secondary to
direct Hebrew, still unadmitted.

```text
Hebrew text
  ↓ orthographic validation   Hebrew-only scope, fail-closed
  ↓ Hebrew letter identity     Unicode standard, verified at runtime
  ↓ licensed value assignment  BLOCKED — no admitted method
  ↓ numeric value
```

---

## Letter identity is sourced to Unicode — and that source is executable

`gematria_hebrew` maps each Hebrew character to a letter identity, sourced to
**The Unicode Standard, Hebrew block (U+0590–U+05FF)**. This is the one place a
source is *stronger* than a paginated copy: the claim is machine-verifiable. A
test checks every entry against `unicodedata.name`, so the table cannot drift
from the standard it cites.

```text
א → aleph      ...      ת → tav          (22 letters)
ך → kaf   ם → mem   ן → nun   ף → pe   ץ → tsadi   (5 final forms → base)
```

Final forms resolve to their base letter's identity — a final kaf *is* a kaf.
Niqqud (combining vowel points) are stripped by the scope normalization: they
carry no letter identity. A Hebrew-block character that is not one of the 22
letters (e.g. a punctuation mark) is **refused**, not skipped.

This is the first genuinely source-backed non-measurement layer in the whole
denotation system. Kamea entered by measurement; Hebrew letter identity enters
by a normative standard.

---

## Identity is not value

Unicode names every Hebrew letter but assigns **none of them a numeric value**
(`unicodedata.numeric` returns nothing). So values are a *traditional* claim,
and the source that fixes them must be a traditional gematria source — which
this phase does not have.

`gematria_value_method` supplies the machinery. A `ValueMethod` names every
choice that affects the number, so the first admitted method will be named
precisely rather than called "gematria":

```text
method_id · alphabet · letter_values · final_letter_policy · final_values ·
normalization_policy · word_boundary_policy · number_composition ·
source_copy_hash · source_locator
```

Standard absolute value (mispar hechrachi) is structured as a **candidate**,
`admitted=False`, with empty source fields — and a method **cannot** be
admitted without a source copy hash and locator. So it licenses nothing. This
is the same acquisition wall numerology hit, one layer along.

`final_letter_policy` is a real methodological fork the record captures:
`SAME_AS_BASE` (final kaf = 20) versus `EXTENDED_500_900`. A method that
values finals differently is a different method with a different hash.

---

## What is admitted, and what is not

| layer | class | admitted | why |
|---|---|---|---|
| orthographic_scope | derived computation | **yes** | fail-closed (1E-G-REPAIR) |
| hebrew_orthography | derived computation | **yes** | Unicode-sourced, runtime-verified |
| transliteration | textual interpretation | no | uncited convention, secondary |
| letter_value_assignment | textual interpretation | no | traditional claim, no source |
| numeric_computation | derived computation | yes (isolation) | arithmetic is not in doubt |
| equivalence_relation | hybrid | no | not implemented (1E-G-SOURCE-B) |
| denotation | textual interpretation | no | no corpus (1E-G-SOURCE-C) |

Three gematria layers are now admitted in isolation. **Gematria still denotes
nothing**, because letter *values* between identity and computation are
unlicensed. `concordance_ready` stays **false**: only Kamea denotes.

---

## Acceptance test

> Given verified Hebrew input and one source-backed value method, the pipeline
> reproducibly emits the same letter identities, values, total, method hash,
> and provenance record.

Passes, driven by a **fixture-admitted** method (the shipped candidate stays
unadmitted). `direct_hebrew_value("אבג", fixture)` → letters `[aleph, bet,
gimel]`, values `[1, 2, 3]`, total `6`, method hash, provenance — identical
across runs. This proves the default block is the admission gate at work, not
broken plumbing.

The default path, with the real candidate method, returns letter identities
and `total: None` with `letter_identity_licensed: true` — the honest first
result.

---

## Result

Gematria can now license one exact path from Hebrew symbols to **letter
identities**, reproducibly and from a verifiable standard. It cannot yet emit a
licensed *value*, because that needs a traditional source. That is precisely
the distinction 1E-G-CLASSIFY drew:

> A functioning arithmetic path is not yet a functioning gematria
> interpretation.

Next: **1E-G-SOURCE-B**, comparison corpus and equivalence claims — where an
equality becomes a statistical object (attested vs preregistered vs discovered)
and the comparison corpus is versioned and hashed as part of the method. Then
1E-G-SOURCE-C, historically licensed denotation.
