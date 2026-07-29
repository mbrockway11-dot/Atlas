# 1E-A — First cross-system concordance: numerology vs Vedic (null)

**Date:** 2026-07-29
**Result:** The first cross-system denotational concordance — numerology against
Vedic natal claims, over the accrued profile library — **does not exceed its
null controls.** Authentic agreement is statistically indistinguishable from
chance. By Representation 1E-A's own criterion, that is vocabulary breadth, not
denotation.

This is the framework's first *empirical* exercise, not another abstraction.
Three systems denote (Kamea, numerology, Vedic); with two of them natal-scoped
and axis-comparable, `run_denotation_profiles.py` assembles each subject's
claims from the canonical dictionaries and scores authentic agreement against
three generators of the null: `shuffled_systems`, `decoy_labels`,
`mismatched_pairs`. Nothing is fabricated; every claim comes from a
source-licensed dictionary.

## Method

- **Subjects:** 2,919 profiles carrying name + birth date (`profile.intake.json`).
- **Numerology:** natal claims from name + date (Jordan canonical dictionary).
- **Vedic:** no birth times exist in the corpus (12 of ~3,600), so the lagna
  lord is uncomputable. Uses the classical **Moon-sign (Chandra lagna)**
  fallback — the sidereal Moon sign's ruling graha's *karakatva* (BPHS). Vedic
  is **withheld** for the 1,419 subjects whose Moon is near a sign boundary that
  day (boundary-uncertain), leaving 1,500 with both systems.
- **Comparable pairs:** 4,267 (numerology meets Vedic-natal, same scope + axis).
- **Scoring:** authentic agreement rate minus each control's, at four RNG seeds.

## Result

Authentic agreement rate: **0.1465** (625 agreeing / 4,267 comparable, 0
contradictory). Gap = authentic − control:

| seed | shuffled_systems | decoy_labels | mismatched_pairs | exceeds every control |
|-----:|-----------------:|-------------:|-----------------:|:---------------------:|
| 1 | −0.0018 | +0.0248 | +0.0070 | **False** |
| 2 | −0.0055 | +0.0110 | −0.0021 | **False** |
| 3 | +0.0013 | +0.0120 | +0.0016 | True |
| 42 | −0.0012 | +0.0183 | +0.0044 | **False** |

The binding control is `shuffled_systems` (it preserves each system's marginal
label distribution and only breaks the subject↔subject pairing). The authentic
gap against it hovers at **zero**, changing sign with the seed — positive in 1
of 4 draws. The verdict is null: numerology and Vedic-Moon-lord natal claims do
not agree beyond chance.

## Why this is a real null, not a weak test

- The **date-derived** numerology quantities (life path, birthday) share an
  input with the Moon sign — a confound that would *inflate* agreement. Even
  with that thumb on the scale, the gap is ~0. A confound that should help and
  doesn't makes the null stronger, not weaker.
- Agreement is not *anti*-correlated either (0 contradictory pairs): the systems
  are simply orthogonal, meeting by chance at the rate their shared vocabulary
  predicts.

## Caveats (what this does not settle)

- **Moon-sign lord, not lagna lord.** Birth times would give the true ascendant;
  the corpus has almost none. This is the strongest test the available data
  supports, and it is null — but a time-rich cohort could differ.
- **Only numerology ↔ Vedic-natal** was exercised. The framework also admits
  **Kamea ↔ Vedic-transit** (dynamic axis), which this run does not compute; see
  the transit-scope work for why that edge has been hard to make non-vacuous.
- A null over one comparable pair is not a claim about the systems in general.

## Conclusion

Representation 1E is architecture-complete and now empirically exercised end to
end. Its first cross-system result is a **null**, consistent with every other
rigorous cross-system test in this project: the systems share a denotational
*vocabulary* but do not *agree* about specific subjects beyond chance. The
framework did its job — it made the null measurable and refused to read
breadth as meaning.
