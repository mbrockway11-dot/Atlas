# P1 Normative-Source Evaluation Table — Hebrew Alphabetic Numeral System

**Status:** completed evaluation · **Type:** evidence table, not an admission ·
**Milestone:** [1E-G-P1-NORMATIVE-SOURCE-EVALUATION](GEMATRIA_P1_NORMATIVE_SOURCE_EVALUATION.md)

The single deliverable of the evaluation: candidate normative authorities
assessed against the six requirements, with citations and explicit coverage.
No source is admitted here. Where a candidate is silent or was not inspectable,
that is recorded as such rather than filled in.

## Candidates inspected

| # | Candidate | Kind | Tier | Inspected |
|---|---|---|---|---|
| 1 | Academy of the Hebrew Language, numeral-writing rules | official standard | normative_standard | **no — HTTP 403** |
| 2 | Gesenius' Hebrew Grammar §5k (Kautzsch–Cowley), via Wikisource | scholarly grammar | scholarly_reference | yes |
| 3 | Unicode CLDR root RBNF `%hebrew` ruleset (`common/rbnf/root.xml`) | implementation standard | normative_standard | yes |

*(CLDR's per-locale `he.xml` was inspected first and rejected: it holds
spelled-out number *words* — "אחת" for 1 — not the letter-value system. The
letter numerals are the algorithmic `hebr` system, whose ruleset is in root
RBNF.)*

## Coverage against the six requirements

`✓` explicitly specified · `~` addressed only in the writing direction /
by exclusion · `✗` absent · `?` not inspected

| Requirement | (1) Academy | (2) Gesenius §5k | (3) CLDR `%hebrew` |
|---|---|---|---|
| units א–ט → 1–9 | ? | ✓ | ✓ |
| tens י–צ → 10–90 | ? | ✓ | ✓ |
| hundreds ק–ת → 100–400 | ? | ✓ | ✓ |
| above-400 policy | ? | ✓ **additive** (תק = 500) | ✓ **additive** (ת״ק = 500) |
| final-form treatment | ? | ~ (additive; finals not used for values — writing direction) | ✗ (formatting output; no reading-direction final values) |
| thousands & punctuation | ? | ✓ thousands (two dots); 15=טו/16=טז | ✓ thousands; geresh/gershayim |

### Citations

- **Gesenius §5k:** "The units are denoted by א–ט, the tens by י–צ, 100–400 by
  ק–ת … the numbers from 500–900 by ת (=400), with the addition of the
  remaining hundreds, e.g. תק 500 … 15 is expressed by טו 9+6, not יה (which is
  a form of the divine name) … The thousands are sometimes denoted by the units
  with two dots."
- **CLDR root RBNF `%hebrew`:** maps א–ת to 1–400; forms 500–900 additively
  (500 → ת״ק, 600 → ת״ר …); inserts geresh/gershayim; `%%hebrew-thousands`
  handles thousands.

## Findings

### F1 — the above-400 policy is settled, and it is *not* final-letter values

Both inspected candidates specify the additive/compositional convention
(500 = ת + ק), and neither assigns the extended final-letter values (final
kaf = 500, …). So the *mispar gadol* convention is a **different method**, and a
value method that used it would need a **different source** — the standard
numeral authorities positively exclude it.

### F2 — the direction gap is exactly requirement 4 (the important one)

Every normative numeral source specifies how to **write a number as letters**
(number → letters), a direction in which final forms are conventionally
avoided. Gematria needs the **reading** direction — the value of letters as
they appear in **words**, which *do* contain final forms. Whether a final kaf in
a word is worth 20 (standard, *mispar hechrachi*) or 500 (*mispar gadol*) is a
**gematria-method choice the numeral-writing sources do not address**. The
mapping for 1–400 is invertible and so transfers to the reading direction; the
final-form value does not, because the writing convention never uses it.

> **Consequence:** for a value method scoped to *mispar hechrachi* with finals
> taking base values, Gesenius/CLDR settle five requirements, and the sixth
> (final-form treatment) follows from the additive convention — finals are not
> numeral letters, so a final kaf reads as kaf = 20. For any method using
> extended finals, no inspected source supports it.

### F3 — a tier/role tension the framework surfaced

The reclassification set the value table to require `normative_standard`
(licenses computation). But:

- The clearest **defining** source, Gesenius, is a **scholarly grammar** —
  `scholarly_reference` tier, which under the matrix licenses context/variants,
  **not** computation. It *defines* the system but cannot license the
  computation claim as currently tiered.
- The right-tier candidates are **CLDR** — `normative_standard`, but an
  *implementation* (formatting direction, final-form gap, F2) that *presupposes*
  and encodes the system rather than defining it — and the **Academy** standard,
  which is `normative_standard` and official but **could not be inspected**.

Along the define-vs-presuppose axis: **Gesenius defines**, **CLDR
implements/presupposes**, **Academy likely defines (uninspected)**.

## Verdict

**No inspected candidate cleanly and completely satisfies all six requirements
in the right tier and the right direction.** This is a real result, not a
failure:

- **Gesenius** covers the requirements and *defines* the system, but is
  scholarly_reference tier — it can corroborate, not license the computation.
- **CLDR** is normative tier and covers five requirements, but is an
  implementation in the writing direction and is silent on reading-direction
  final values.
- The **Academy of the Hebrew Language** standard is the strongest untested
  candidate — official, normative tier, and (from F1/F2) the numeral-writing
  authority most likely to specify the mapping, thousands, and the 15/16
  convention explicitly. **It must be inspected via an access route that is not
  403-blocked** before this evaluation can select it.

## Two decisions this raises (for review, not enacted)

1. **Does a definitive scholarly grammar that *defines* the numeral encoding
   count as a normative computational authority?** If a work that establishes
   "units are denoted by א–ט" is treated as scholarly_reference only, the
   framework may reject the clearest defining evidence on a tier technicality.
   This is the define-vs-presuppose axis interacting with the tier matrix, and
   it is a genuine classification question — surfaced, not resolved.
2. **Scope the value method to *mispar hechrachi* explicitly.** F1/F2 show the
   final-form and above-400 questions only settle once the method commits to
   the standard convention. That commitment should be recorded as part of the
   method, so "gematria" is never left ambiguous between hechrachi and gadol.

## What was not done

No source admitted. No value table transcribed or compiled. No code, tier, or
dataclass changed. The deliverable is this table and its findings — including
the honest gap that the strongest candidate remains uninspected.
