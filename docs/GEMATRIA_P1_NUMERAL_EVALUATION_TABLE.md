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

## Evidentiary role (the define / presuppose / implement axis)

Orthogonal to tier and to coverage. It distinguishes *descriptive definition*,
*normative establishment*, and *executable implementation* without conflating
them.

| Candidate | Defines | Presupposes | Implements |
|---|---|---|---|
| Gesenius §5k | ✓ (describes the mapping as understood) | | |
| CLDR `%hebrew` | | ✓ | ✓ |
| Academy | ? | ? | ? |

> **These are inspection results, not intrinsic properties of the works.** Each
> cell states what the current inspection supports, as of inspection — this is
> a research notebook, not a ledger of settled facts. Any cell can change on
> further reading: if Gesenius turns out to cite an earlier authority, or to be
> summarizing a long-established convention, or to distinguish numeral writing
> from gematria elsewhere, its role classification moves. Do not treat the
> table as the authority; it records evidence and its own uncertainty.

A subtlety this column makes explicit: Gesenius **describes** the mapping,
which is evidence the convention *existed and was understood* — it is **not**
automatically evidence that Gesenius is the authority the convention *derives
from*. That distinction is why the evaluation stopped before admission (F3).

## Findings

### F1 — the above-400 policy is settled, and it is *not* final-letter values

Both inspected candidates specify the additive/compositional convention
(500 = ת + ק), and neither assigns the extended final-letter values (final
kaf = 500, …). So the *mispar gadol* convention is a **different method**, and a
value method that used it would need a **different source** — the standard
numeral authorities positively exclude it.

### F2 — the Encoding–Interpretation Direction Gap (the central finding)

**A named finding, because it will recur whenever an encoding standard is
compared with an interpretive tradition.**

```text
numeral specification    integer → Hebrew letters   (writing)
gematria evaluation      Hebrew letters → integer   (reading)
```

Mathematically these look like inverses; historically they are not. The
numeral-writing tradition **deliberately avoids** situations — final forms,
certain spellings (יה, יו) — that gematria must nonetheless evaluate, because
gematria reads **arbitrary lexical forms**, not just well-formed numerals. So an
encoding standard **underspecifies its own inverse** for interpretive use. That
is a property of the historical sources, not a software issue, and no amount of
implementation closes it.

Here it is exactly requirement 4: the 1–400 mapping inverts cleanly and
transfers to the reading direction, but the final-form value does not, because
the writing convention never uses it. Whether a final kaf in a word is worth 20
(*mispar hechrachi*) or 500 (*mispar gadol*) is a gematria-method choice the
numeral-writing sources do not address.

> **Consequence:** for a value method scoped to *mispar hechrachi* with finals
> taking base values, Gesenius/CLDR settle five requirements, and the sixth
> (final-form treatment) follows from the additive convention — finals are not
> numeral letters, so a final kaf reads as kaf = 20. For any method using
> extended finals, no inspected source supports it.

### F3 — unresolved provenance, *not* a tier conflict

An earlier draft framed this as a tension between Gesenius and the tier model.
That was too strong. The accurate statement is narrower and does not threaten
the tier model:

> Gesenius is evidence that the mapping **existed and was understood**. It is
> **not automatically** evidence that Gesenius is the authority the mapping
> **derives from**.

So there is no need to reclassify Gesenius or to conclude that the tier matrix
rejects good evidence. The evaluation simply has **not yet established the
evidentiary chain** — from where does the standard mapping actually derive? If
Gesenius turns out to be *describing* a convention established elsewhere (an
official standard, or an older attested usage), the tier model survives
unchanged: Gesenius corroborates, and the deriving authority licenses. The
evaluation stopping before admission is the framework behaving correctly in the
uncomfortable middle — *we have evidence, but not yet the evidentiary chain
required for admission.*

The `normative_standard`-tier candidates remain **CLDR** (an implementation in
the writing direction, with the F2 gap) and the **Academy** standard
(uninspected). Identifying the deriving authority is the open provenance
question, and it is exactly what the table was built to surface.

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

## Two questions this raises (for review, not enacted)

1. **From where does the standard mapping derive?** The open question is a
   provenance one, not a tier reclassification (F3). Gesenius shows the mapping
   was understood; the deriving authority is still to be identified — most
   likely the Academy standard or an older attested usage. Resolve the chain,
   and the tier model applies unchanged.
2. **Scope is a provenance decision, not an implementation choice.** Committing
   the value method to *mispar hechrachi* does not merely choose an algorithm:
   it determines **which sources are relevant** and **which historical
   conventions are in scope** (F1/F2 only settle under that commitment). Scope
   should therefore be recorded as part of the method's provenance, so
   "gematria" is never left ambiguous between hechrachi and gadol — and so the
   choice of sources to admit follows from the scope, not the reverse.

## The deriving-authority question — a located hypothesis, not a closed chain

Question 1 narrows to: *what is the earliest identifiable authority that
explicitly specifies the standard Hebrew alphabetic numeral mapping?* A first
investigation suggests an **emergent-convention provenance model** — but the
finding must be held at the strength the inspected evidence actually supports,
which is less than a demonstrated transmission chain.

**Securely supported (directly inspectable):**

- Greek alphabetic numerals **precede** the surviving Hebrew evidence
  (Chrisomalis abstract: Greek numerals from ~600 BC).
- Hebrew alphabetic numerals are **attested by the late 2nd c. BCE**, with
  fuller decimal-system evidence ~78 BCE.
- The Hebrew system is **structurally related** to the Greek alphabetic system.
- **No single authoring authority is presently identified** in the inspected
  evidence. *(Not identified ≠ shown not to exist.)*

**Provisional (a located hypothesis, pending direct inspection):**

- A direct Greek→Hebrew **adaptation/transmission** (as opposed to precedence +
  affinity).
- The **200–78 BCE** span read as a *derivation window* (78 BCE is an
  attestation date, not a derivation date).
- **"Emergent convention with no establishing authority"** as a demonstrated
  conclusion.

**Access status:** Chrisomalis (*Numerical Notation*, Cambridge UP 2010) is
**paywalled** — only the abstract was visible, and it states that "important
historical questions remain unresolved." Gandz (*Proc. AAJR*, 1932–33) is not
yet inspected. The stronger formulation was originally surfaced via Wikipedia
used strictly as a **locator** (inadmissible; points to references, never
licenses them). So the transmission claim is a hypothesis these two specialist
sources must be read to settle.

### Provenance shape, every edge marked by evidentiary status

```text
Greek alphabetic system  (attested ~600 BC)
    | proposed historical influence     [INFERRED from precedence + affinity;
    |                                    NOT demonstrated transmission]
Hebrew alphabetic numeral convention
    | earliest SURVIVING attestations   [CORROBORATED ~late 2nd c. BCE / 78 BCE;
    |                                    attestation != moment of origin]
later grammatical description (Gesenius §5k)
    | describes                         [CORROBORATED — directly inspected]
modern implementation (CLDR %hebrew)
    | implements                        [CORROBORATED — directly inspected]
```

Two silent slides this prevents: **earliest surviving attestation → moment of
origin**, and **chronological precedence → demonstrated derivation**. Neither
inference is licensed by the evidence in hand.

### The secure statement, and the working model

The narrowest statement the inspected evidence supports:

> The presently inspected evidence **does not identify a defining authority**
> for the Hebrew alphabetic numeral mapping, and instead presents later
> descriptions, implementations, and historical attestations.

That is secure. On top of it sits a **working provenance model** — not a
settled historical classification:

```text
Doctrine-shaped provenance    seek an establishing text or authority
Convention-shaped provenance  seek origin context, transmission evidence,
                              attestations, later codification, implementations
```

The mapping behaves convention-shaped under this model, which is why P1 treats
the value table as a normative convention. But "the mapping *is* a convention
with no authority" is not yet a settled historical finding — only that no
authority is presently identified. Whether numerology or Jyotiṣa constructs are
convention- or doctrine-shaped is the cross-domain comparison to watch, and it
too will be a working classification until the sources are read.

### Next move — a bounded acquisition task

Not architectural or computational. Acquire direct access to, and extract from,
two specialist sources:

1. **Stephen Chrisomalis, *Numerical Notation*** — the alphabetic-systems
   section. *(Attempted: Cambridge Core, **paywalled**; abstract only.)*
2. **Solomon Gandz**, study of Hebrew numerals (*Proc. AAJR*, 1932–33).
   *(Attempted: not on Internet Archive; likely JSTOR/institutional.)*

Both require library or institutional access not available here. For **each**,
record only:

- the exact historical claim made;
- the evidence cited for that claim;
- whether Greek→Hebrew transmission is stated as **explicit** or **inferred**;
- the earliest attestation actually discussed;
- whether the author **identifies**, **denies**, or **does not discuss** an
  establishing authority.

Then annotate each provenance edge above as *explicitly argued*, *inferred*,
*corroborated*, or *unresolved*. Until those passages are inspected, this
section — graph and model alike — remains a well-formed research hypothesis,
not a settled provenance chain.

## What was not done

No source admitted. No value table transcribed or compiled. No code, tier, or
dataclass changed. The deliverable is this table and its findings — including
the honest gap that the strongest candidate remains uninspected.
