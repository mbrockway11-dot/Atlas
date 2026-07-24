# 1E-G-CLASSIFY — Gematria Admission Classification

**Status:** complete · **Type:** architectural decomposition, not a dictionary
· **Produces:** no denotations · **Part of:**
[Representation 1E](REPRESENTATION_1E_CROSS_SYSTEM_DENOTATION.md)

The deliverable is a decomposition, not meanings. The question is which layers
of gematria owe which evidence, and which — if any — are admissible today.

This is also a test of the 1E governance architecture itself: if gematria's
decomposition had merely mirrored numerology's, that would suggest the
framework was overfit to numerology. **It does not mirror it.** Gematria
requires two layers numerology has no analogue for, and the current
implementation fuses them.

---

## What the code actually computes

`src/atlas/ciphers.py` exposes three ciphers over a Latin-normalized string:

```text
ordinal          A=1 … Z=26
hebrew_literal   Latin letter → Hebrew letter value, via a fixed table
hebrew_phonetic  greedy sound-group tokens (SCH, TCH, PH, TH, SH, CH,
                 CK, QU, WH, NG), falling back to hebrew_literal
```

Three measured properties of that implementation drive the classification.

### 1. `ordinal` is not gematria

A=1…Z=26 over the Latin alphabet is a modern English ordinal cipher. It shares
no tradition, alphabet or value assignment with Hebrew gematria. Classifying
it under gematria would be the same category error as merging Chaldean and
Pythagorean numerology — it belongs to a **separate system** with its own
admission problem, and is registered as such.

### 2. Hebrew source text is silently discarded

```text
Hebrew input (4 characters)
  normalize_text keeps : 4 chars      ← isalpha() is true for Hebrew
  hebrew_literal gives : []           ← table is keyed by Latin A–Z
```

The cipher named `hebrew_literal` **cannot process Hebrew**. It accepts the
input, drops every character at lookup, and returns an empty sequence rather
than refusing. Classical gematria operates on Hebrew text; this operates on
Latin text using Hebrew-derived values, which is a different object.

This is the same class of defect found in the identity encoder during Identity
2A, where non-A–Z characters were dropped and `Gödel ≡ Gdel`. Silent
truncation on in-domain input is a **blocking defect for computational
admission**: a layer that returns an empty result for text it was named after
is not reproducible in any useful sense, it is merely deterministic.

### 3. Transliteration and value assignment are fused, and lossy

`HEBREW_LITERAL_VALUES` maps Latin letters directly to Hebrew *values*, so two
separable decisions are welded into one uncited constant:

```text
which Hebrew letter does this Latin letter represent?   ← editorial convention
what value does that Hebrew letter carry?               ← attested tradition
```

The second is well attested. The first is a contestable choice, and it is
non-injective:

```text
value   6 ← U, V, W
value  10 ← I, J, Y
value  20 ← C, K
value  60 ← S, X
value  80 ← F, P
```

So the mapping cannot be inverted, and the transliteration cannot be
independently checked against a source because it is not separately
represented. `hebrew_phonetic` compounds this: `CHAIM → [20, …]` renders the
initial *ch* as Kaph (20), where the Hebrew חיים begins with Cheth (8). That
is a defensible convention, but it is a **convention**, and no citation
licenses it.

---

## Layer decomposition

Gematria decomposes into six layers. Numerology has analogues for only three.

```text
orthographic scope        which characters are text at all
        ↓
transliteration           Latin letter → Hebrew letter identity     ← no numerology analogue
        ↓
letter-value assignment   Hebrew letter → numeric value
        ↓
numeric computation       sequence and sum
        ↓
equivalence relation      text ≡ text by value                      ← no numerology analogue
        ↓
textual denotation        what a value or equivalence signifies
```

### The equivalence layer is gematria's characteristic operation

Numerology's semantic move is **denotation**: "4 signifies stability."
Gematria's is **equivalence**: two words sharing a value are held to be
connected. That is a relation between texts, not a property of a number, and
it needs machinery 1E does not currently have — a declared comparison corpus,
because "which texts may be compared" determines every equivalence found.

**The code implements no equivalence layer at all.** It returns sequences.
Any equivalence claim would be new work, and its corpus selection would be
textual authority, not computation.

---

## Admission classification

| layer | class | provenance owed | admissible now |
|---|---|---|---|
| orthographic scope | derived computation | computational reproducibility | **no** — silent drop |
| transliteration | textual interpretation | source provenance + construct equivalence | **no** — uncited, fused |
| letter-value assignment | textual interpretation | source provenance | **no** — fused with above |
| numeric computation | derived computation | computational reproducibility | **yes**, in isolation |
| equivalence relation | hybrid | both, independently | **no** — not implemented |
| textual denotation | textual interpretation | verified provenance | **no** — no corpus |

English ordinal is registered separately:

| system | layer | class | admissible |
|---|---|---|---|
| english_ordinal | ordinal computation | derived computation | **yes**, in isolation |

---

## An admissible layer does not launder an inadmissible input

Numeric computation is genuinely deterministic and reproducible — summing a
sequence of integers is not in doubt. But it consumes the output of the
transliteration layer, which is inadmissible.

> **A layer's admission covers its own operation, never its inputs.**

So gematria's numeric computation is admissible *in isolation* and contributes
nothing usable downstream, because everything it consumes is unlicensed. This
is the feed-forward invariant applied to data rather than imports, and it is
the reason "yes, in isolation" appears twice in the table above without
gematria becoming eligible for anything.

---

## What would unblock each layer

1. **Orthographic scope** — refuse out-of-alphabet input explicitly instead of
   returning an empty sequence, and declare the Latin-only boundary. This is a
   code fix, not an evidence problem.
2. **Transliteration** — separate it from value assignment into its own table,
   then cite the convention to a source under the 1E-N-SOURCE discipline. Until
   split, it cannot be verified even if a source were available.
3. **Letter-value assignment** — cite to a source; the values are well attested,
   so this is expected to be the easiest of the three.
4. **Equivalence relation** — specify it, including the comparison corpus,
   before implementing. Corpus selection is a source decision.
5. **Denotation** — a citation corpus under the same acquisition gate
   numerology is blocked on.

Steps 1 and 2 are prerequisites for everything below them and are **not**
blocked on acquiring any book.

---

## Result

Gematria is **not admitted at any denoting layer**. Two layers are admissible
in isolation and neither can feed a denotation.

The methodology test came out favourably: applying the 1E process to a
different symbolic system produced a **different decomposition** — six layers
rather than numerology's two, including a transliteration layer and an
equivalence relation with no numerology counterpart — and it surfaced a
concrete implementation defect (silent Hebrew truncation) that no amount of
reasoning by analogy from numerology would have found.

`concordance_ready` remains **false**. Only Kamea denotes.
