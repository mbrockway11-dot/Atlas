# P1 Acquisition — Integration Test Findings

**Status:** integration test run against a real source · **Outcome:** target
re-scoped, no admission (correctly) · **System under test:** the gematria
value-method acquisition path

The first real-source run of the acquisition protocol. The goal was not to
admit a value method but to see whether the protocol survives contact with an
actual text. It did — and it surfaced two structural findings and one hard
boundary, which is exactly what the exercise was for.

---

## What was attempted

Target: **Pardes Rimmonim**, to license the gematria value method
(*mispar hechrachi*), per the canonical corpus.

- **Step 1 (select manifestation):** queried Sefaria's index for Pardes
  Rimmonim.
- **Step 2–3 (verify copy, identify passage):** attempted to locate the
  section defining the value table.
- **Cross-check:** the Jewish Encyclopedia (1906) "Gematria" article
  (`scholarly_reference`) on where the value table is defined in the
  literature.

---

## Finding 1 — the named passage does not exist

Sefaria's index shows Pardes Rimmonim (Moses Cordovero) as **32 gates, with no
dedicated Gate of Gematria.** The nearest are Gate 27 (Gate of Letters,
mystical significance of the alphabet) and Gate 30 (Gate of Combination,
*tzeruf*). The canonical corpus named "Pardes Rimmonim (Sha'ar HaGematria)";
that section, as named, does not appear in the index.

*(Observed via the Sefaria index API; under the protocol this would still
require confirmation against a verified copy. But it is enough to show the
target was mis-specified.)*

## Finding 2 — no primary text defines the value table (the structural one)

The deeper result. The Jewish Encyclopedia presents the standard values
matter-of-factly — "א–ט as units, י–צ as tens, ק–ת as hundreds" — as the
**assumed** Hebrew alphabetic numeral system, and cites **no source that
defines** the aleph-through-tav assignments. The primary sources it does cite
(Talmud Nedarim 32a; the midrashim; R. Eliezer b. Jose's 29th hermeneutic
rule, c. 200) demonstrate gematria **usage** — that equal-value words are
treated as connected — not the value table.

This is the architectural insight the test was meant to find:

> The value-method layer's evidence model assumes a primary traditional text
> that **defines** the letter values. No such text exists. The values are the
> standard Hebrew alphabetic numeral system — an assumed convention,
> independent of and older than gematria-as-interpretation. Primary texts
> **use** the values (equivalence) and **interpret** results (denotation);
> they do not tabulate the values.

### Consequence: the layers were mis-assigned to sources

```text
letter value table (aleph=1 … tav=400)
    → the Hebrew alphabetic numeral system: a normative convention,
      not a tradition-specific method. Licensable like letter identity was
      (Unicode) — by a normative/reference authority, NOT by a primary
      Kabbalistic text.

equivalence practice ("equal value => connected")
    → THIS is what Pardes Rimmonim, the Talmud and the midrashim license.
      Primary_traditional, and it belongs to 1E-G-SOURCE-B, not the value
      method.

denotation ("this equivalence signifies X")
    → primary commentaries; 1E-G-SOURCE-C.
```

So Pardes Rimmonim is a real and appropriate source — but for the
**equivalence** layer, not the value method. The value method needs a
different kind of source than the corpus assumed.

## Finding 3 — the AI-agent boundary (the honest limit)

Independently of the above: I cannot complete admission regardless. The
protocol requires an independent **double transcription** and a human
inspection of the **title/copyright page and pagination** of a verified copy.
As a single agent I can be neither the second transcriber nor the copy
verifier, and fetching a scan is not certifying it. The framework correctly
refuses to admit without those, so no admission was attempted — and none would
have been legitimate.

---

## What this justifies changing now

- **Correct the P1 target.** The gematria value method is not sourced from
  Pardes Rimmonim, and not by a `method` claim against a primary Kabbalistic
  text. Recorded on the target as a finding; the target is re-scoped rather
  than left pointing at a passage that does not define what it claims.
- **Recommended for review (not done unilaterally):** treat the letter value
  table as a **normative** claim — the Hebrew alphabetic numeral system —
  admissible via a normative/reference authority the way letter identity was
  admitted via Unicode, rather than requiring a primary-text acquisition. If
  accepted, gematria numeric evaluation could unblock **without** a book
  acquisition at all, and the primary-source effort would move to the
  equivalence and denotation layers where the tradition's interpretive claims
  actually live. This changes a capability path, so it is surfaced for
  decision rather than implemented mid-test.

## What did *not* change

No admission, no fabricated value table, no new tier. The framework behaved
correctly throughout: it had nothing to admit, and it said so. The single
end-to-end run taught more about the value-method model than any number of
source-neutral tests — precisely as predicted.
