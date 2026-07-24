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

## Finding 2 — no defining primary passage was identified (the structural one)

The deeper result. Stated with the epistemic care it warrants:

> **No defining primary passage has been identified.** The inspected scholarly
> reference (Jewish Encyclopedia) presents the standard values matter-of-factly
> — "א–ט as units, י–צ as tens, ק–ת as hundreds" — as the **assumed** Hebrew
> alphabetic numeral system, and identifies no source that *defines* the
> aleph-through-tav assignments. The primary sources it cites (Talmud Nedarim
> 32a; the midrashim; R. Eliezer b. Jose's 29th hermeneutic rule, c. 200)
> **presuppose** the numeral convention and demonstrate gematria *usage* —
> equal-value words treated as connected — rather than establish the values.

This is *not* the absolute claim "no primary text defines the value table";
that would assert universal nonexistence across a corpus one lookup cannot
survey. It is strong enough to reject the current acquisition target and to
motivate the reclassification, and no stronger.

The architectural insight the test was meant to find:

> The value-method layer's evidence model assumed a primary traditional text
> that **defines** the letter values. The known primary examples appear to
> presuppose them instead. The values are the standard Hebrew alphabetic
> numeral system — a convention independent of, and older than,
> gematria-as-interpretation. So the value table is a **normative** claim, and
> the primary-text effort belongs at the equivalence and denotation layers.

### Consequence: the layers were mis-assigned to sources

```text
Unicode
    → licenses Hebrew character identity and normalization ONLY.
      Unicode explicitly omits Numeric_Value from ordinary Hebrew letters
      and places numeric interpretation outside its scope, so it is NOT the
      value-table authority even though its tier permits computation claims.

Hebrew numeral-system authority  (to be identified)
    → licenses the standard letter-value assignment. Normative, computation.
      A DISTINCT source from Unicode.

primary traditional texts  (Pardes Rimmonim, Talmud, midrashim)
    → license gematria usage, equivalence, and denotation. 1E-G-SOURCE-B / -C,
      not the value method.
```

The three authorities are distinct. Unicode's tier *may* license a computation
claim in general, but Unicode the source makes no numeral claim, so it cannot
be cited for the values -- a separate Hebrew numeral-system authority is
required.

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
