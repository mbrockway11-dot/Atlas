# 1E-G-P1-NORMATIVE-SOURCE-SELECTION

**Status:** open · **Replaces:** the original P1 (Pardes Rimmonim → value
method), re-scoped by the [P1 integration test](GEMATRIA_P1_INTEGRATION_FINDINGS.md)
· **Decision:** RECLASSIFY yes · ADMIT NOW no

The P1 integration test reclassified the gematria value table from a
primary-text method claim to a **normative computation** claim. This smaller
milestone finds the normative authority.

> **The question:** which published normative authority most completely
> specifies the Hebrew alphabetic numeral system this implementation needs?

## The three authorities are distinct

```text
Unicode                          identity + normalization ONLY
                                 (omits Hebrew Numeric_Value; numeric
                                 interpretation is out of Unicode's scope)
Hebrew numeral-system authority  the standard letter-value assignment
                                 (to be identified — a distinct source)
primary traditional texts        usage, equivalence, denotation
```

Unicode's tier permits computation claims in general, but Unicode the *source*
makes no numeral claim, so it cannot be cited for the values. A separate
authority is required.

## Acceptance gate

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

"Standard Hebrew numerals" and "every gematria method" are not identical, which
is why the mapping alone is not enough — the final-form and above-400 policies
must be explicit.

## Candidate authorities, in test order

`NUMERAL_AUTHORITY_CANDIDATES`. A lower candidate is considered only if the
ones above do not suffice.

1. **An official Hebrew-language or governmental style standard** — the
   strongest normative authority if one specifies the numeral system.
2. **A recognized scholarly grammar or reference work devoted to Hebrew
   numeration** — `scholarly_reference` describing the convention.
3. **Unicode CLDR Hebrew algorithmic numbering** — *only if* its
   machine-readable rules actually expose the mapping and the policies above.
   CLDR models Hebrew numerals as an algorithmic numbering system (TR35), so it
   may provide implementation evidence, but its exact rules must be inspected
   before it is treated as sufficient. Tested last, not first.

## Not in this milestone

- **Admission.** Even with a sufficient source identified, admission requires
  the source actually specify all mandatory items and pass the normal
  verification. This milestone selects and tests a candidate; it does not
  admit.
- **Pardes Rimmonim.** Retained for equivalence and denotation research
  (1E-G-SOURCE-B/-C), not for the value table.
- **Juno Jordan / Vedic.** Held. The same "does the source *define* or merely
  *presuppose* the construct?" question should be asked of each before
  acquisition — the lesson P1 taught.
