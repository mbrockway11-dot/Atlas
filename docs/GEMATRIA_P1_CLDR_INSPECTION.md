# P1 CLDR `%hebrew` Ruleset Inspection — the Value-Table Tier Split

**Status:** completed inspection · **Type:** first-hand source finding, not an
admission · **Milestone:** [1E-G-P1-NORMATIVE-SOURCE-EVALUATION](GEMATRIA_P1_NORMATIVE_SOURCE_EVALUATION.md)

The evaluation table assessed candidate normative authorities against the six
`MANDATORY_NUMERAL_REQUIREMENTS` from summaries. This record goes one step
further for the one machine-readable candidate: a **first-hand inspection of the
actual CLDR `%hebrew` RBNF ruleset**, and the conclusion it forces about *which
tier can license which requirement*. Nothing is admitted here. No code or
admission state is touched.

## Route taken

The highest-value candidate, the Academy of the Hebrew Language, remained
**HTTP 403** on every automated route (WebFetch and an in-app browser load) —
confirming and hardening the eval's "403" note. The Academy is therefore a
**print / offline** acquisition target (an official published copy, verified and
double-transcribed per the protocol), not a web-fetchable one.

The pivot was to the one normative numeral authority that *is* fetchable and
machine-readable: **Unicode CLDR's `%hebrew` rule-based number-format ruleset**
in `common/rbnf/root.xml`, inspected directly (not via a summary of it).

## What the ruleset actually establishes (inspected)

| Requirement | What CLDR `%hebrew` does |
|---|---|
| units 1–9 | א–ט map to 1–9 |
| tens 10–90 | י–צ map to 10–90 |
| hundreds 100–400 | ק ר ש ת map to 100–400 |
| **above-400 policy** | **additive**: 500 = `ת״ק` (400+100), 800 = `ת״ת`, 900 = `תת״ק` |
| **final-form treatment** | the five sofit letters (ך ם ן ף ץ) are **never used** as numeral values |
| thousands | 1000 = `אלף` (spelled); higher via a separate thousands ruleset |

So CLDR settles above-400 as **additive** — which structurally **excludes**
mispar gadol (finals valued 500–900): you write 500 as `ת״ק`, never as `ך`.

## The Encoding–Interpretation Direction Gap, sharpened to a conclusion

The eval *named* this gap; the first-hand inspection turns it into a verified
structural conclusion:

- A numeral-writing standard runs **integer → letters**. To *write* 500 you
  emit `ת״ק`; a final letter **never appears**. CLDR is silent on sofit values
  not by omission but by **direction** — it never meets one.
- Gematria runs the **inverse**: **letters → integer**. A final kaf `ך` at a
  word's end *is present*, and its value (20 in mispar hechrachi, 500 in mispar
  gadol) is a **method choice**, not an encoding fact.

Therefore **no normative source can define the final-form reading value** — it
is the wrong kind of question for that tier. This is now established by reading
the rules, not inferred.

## Consequence: the value table splits by tier

| Sub-requirement | Answerable by | Where it stands |
|---|---|---|
| base 22-letter values (1–400) | **normative** (CLDR fixes the encoding) | inspected; licensable pending the judgment below + protocol |
| above-400 policy (additive) | **normative** (CLDR: additive) | inspected |
| **final-form *reading* value** | **primary_traditional** (a gematria method text) | still an acquisition — Pardes Rimmonim retained (1E-G-SOURCE-B/-C) |

Phase 1 (`gematria-value-method`) was scoped as one normative acquisition. This
finding shows it is **two claims of two tiers**: the base table + above-400 are
normative and now inspectable; the final-form reading value is provably
primary_traditional and cannot be sourced normatively.

## The one open judgment (not resolved here)

Whether CLDR *fixing the encoding* counts as **defining** the base value table
(licensable) or merely **presupposing + implementing** it (the eval's cautious
read) is a genuine human judgment. For the narrow COMPUTATION claim — "what
integer does this letter encode" — a normative standard that fixes the encoding
is arguably exactly the licensing evidence required. But the define-vs-presuppose
call is deliberately left to a human; the assistant does not resolve admission.

## Evidentiary status / provenance

- CLDR `%hebrew` rules: **inspected first-hand** via the `unicode-org/cldr`
  `common/rbnf/root.xml` on the `main` branch (unversioned at read time). This
  is verified *content*, but **not yet a pinned citeable copy**: admission would
  require pinning a released CLDR version, recording the file hash, and
  double-transcribing the rule fragments.
- Academy of the Hebrew Language: **not inspectable** (403 on all automated
  routes). Reclassified from "web candidate" to "print acquisition target."
- The additive-500 finding independently agrees with the eval table's summary
  read, now confirmed against the source itself.

## Next moves (source events, not code)

1. A human resolves the define-vs-presuppose judgment for CLDR licensing the
   base table + above-400.
2. If yes: pin a CLDR version, hash it, double-transcribe, run the capability
   gate — admitting the base value table as a normative computation claim.
3. The final-form reading value stays a **primary_traditional** acquisition (a
   gematria method passage), tracked separately, not blocked on the normative
   base-table work.

No admission has occurred. This document is a finding.
