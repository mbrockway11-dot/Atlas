# 1E-G-P1-NORMATIVE-SOURCE-EVALUATION

**Status:** open · **Replaces:** the original P1 (Pardes Rimmonim → value
method), re-scoped by the [P1 integration test](GEMATRIA_P1_INTEGRATION_FINDINGS.md)
· **Decision:** RECLASSIFY yes · ADMIT NOW no

The P1 integration test reclassified the gematria value table from a
primary-text method claim to a **normative computation** claim. This milestone
identifies and evaluates the normative authority.

It is framed as an **evaluation, not a search**. There is no frozen ranking of
candidate kinds: which authority is strongest is decided by how completely each
specifies the six requirements, not by whether it is a government standard, a
grammar, or an implementation standard. Freezing an ordering would make the
framework source-driven; the evaluation keeps it evidence-driven.

> **The question:** which published normative authority most completely and
> explicitly specifies the Hebrew alphabetic numeral system this implementation
> needs?

## The three authorities are distinct

```text
Unicode                          identity + normalization ONLY
                                 (omits Hebrew Numeric_Value; numeric
                                 interpretation is out of Unicode's scope)
Hebrew numeral-system authority  the standard letter-value assignment
                                 (to be identified by this evaluation)
primary traditional texts        usage, equivalence, denotation
```

Unicode's tier permits computation claims in general, but Unicode the *source*
makes no numeral claim, so it cannot be cited for the values.

## Acceptance gate — the six requirements

The value table stays closed until one source explicitly specifies
(`MANDATORY_NUMERAL_REQUIREMENTS`, enforced by `numeral_source_sufficient`):

- **units** — א–ט → 1–9
- **tens** — י–צ → 10–90
- **hundreds** — ק–ת → 100–400
- **final-form treatment** — how the five finals are valued
- **above-400 policy** — compositional, or extended final-letter values
  (500–900)

Conditional (only if in the method's scope):

- **thousands and punctuation** conventions

"Standard Hebrew numerals" and "every gematria method" are not identical, so
the mapping alone is not sufficient — the final-form and above-400 policies
must be explicit.

## Candidates to evaluate

`NUMERAL_AUTHORITY_CANDIDATES` — a set, not a ranking. Evaluate each against
the six requirements; the coverage decides.

- **An official Hebrew-language or governmental standard** (e.g. an Academy of
  the Hebrew Language publication) — potentially the strongest normative
  authority *if* it specifies the numeral system. Not automatically strongest.
- **A recognized scholarly grammar or reference devoted to Hebrew numeration**
  — may be the most appropriate if no official standard specifies the system.
- **Unicode CLDR Hebrew algorithmic numbering** — an *implementation* standard,
  not a historical authority. It models Hebrew numerals algorithmically
  (TR35), so it may supply implementation evidence, but its exact rules must be
  inspected. Its kind carries a caveat; its position carries no rank.

## Acceptance criteria for the evaluation

This milestone is complete when it has:

1. identified one or more candidate normative authorities;
2. evaluated each against the six mandatory requirements;
3. recorded, per candidate, which requirements are **explicitly specified** and
   which are **absent**;
4. produced a traceable rationale for selecting or rejecting each candidate;
5. admitted no source solely because it is convenient or machine-readable.

The deliverable is that evidence table, not a pre-chosen winner.

## Not in this milestone

- **Admission.** A sufficient source still passes the normal verification
  before anything is admitted.
- **Pardes Rimmonim.** Retained for equivalence and denotation research
  (1E-G-SOURCE-B/-C), not the value table.
- **Juno Jordan / Vedic.** Held. Apply the standing question first (below).

## Standing research question for every acquisition

The reusable pattern P1 exposed, now a required check at construct
identification for **every** source, in every tradition:

> **Does the source *define* the construct, or *presuppose* it?**
>
> Is this source *establishing* the rule, or *assuming* a rule established
> elsewhere? Those are different evidentiary roles. A source that presupposes
> the construct is evidence of *usage*, not of the *definition* — and citing it
> to license the definition is the mis-targeting the Pardes Rimmonim test
> caught.

Recorded in the [acquisition protocol](DENOTATION_ACQUISITION_PROTOCOL.md) at
Stage 6. Ask it of Juno Jordan and of every Jyotiṣa text before acquisition,
not after.
