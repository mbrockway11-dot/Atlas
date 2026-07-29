# 1E-V-SOURCE-A — Vedic ayanāṃśa admitted (Lahiri)

**Date:** 2026-07-27
**Result:** The Lahiri (Chitra-pakṣa) ayanāṃśa is admitted, licensed by the
Government of India standard. This licenses the sidereal **offset** (a
computation), so sidereal quantities naming the Lahiri choice are unblocked. It
does **not** make Vedic denote — that is a separate, larger acquisition.

Like numerology, this is a *source event*: a verified, appropriately-tiered
source, not a new abstraction, and nothing was fabricated. The three schemes'
offsets were always reproducible via swisseph; what was unlicensed was
*choosing* one. Lahiri now has an authority; Raman and Krishnamurti do not.

## The source

*Report of the Calendar Reform Committee*, Government of India, Council of
Scientific and Industrial Research, New Delhi, **1955**. Tier:
`normative_standard` (a governmental standards body; it licenses the ayanāṃśa as
a computational constant, never a Vedic meaning). N.C. Lahiri was the
committee's Secretary, which is why the scheme carries his name.

The verification turned on a distinction the framework exists to enforce: the
report contains **correspondents' letters** advocating positions (an individual
writing "23° 15' ayanāṃśa should be taken") *and* the **committee's own
recommendation**. Only the latter is the standard. The admitted passage is the
committee's:

> **Recommendations for Religious Calendar.** (5) The calculation of solar
> (saura) months … will start **23° 15′ ahead of the vernal equinoctial
> point**. … (7) … we have adopted a variable ayanāṃśa … The value of this
> ayanāṃśa would amount to **23° 15′ 0″ on 21st March, 1956**. Thereafter it
> would gradually increase … about **50″·27** [per year].
> — printed p. 7

## Copy verification (a digital surrogate)

| Check | Evidence |
|---|---|
| Committee voice (not a correspondent) | p.7 sits under "Final Recommendations of the Committee"; the surrounding text is "we have adopted…" |
| Page image | leaf n18 of IA `calendar_reform_comittee_report`, printed p.7, read directly and matched to OCR |
| Citeable edition | IA `dli.ministry.19933` — catalog metadata: CSIR, New Delhi, 1955 |
| Membership | p. (Annexure I) lists N.C. Lahiri, Member/Secretary |
| File hash | jp2.zip sha1 `a4a6e0753677eba7be774200a1cd0c85460b0252` |

## Construct equivalence

Swiss Ephemeris `SIDM_LAHIRI` implements this official Indian ayanāṃśa: its
recorded J2000 offset (23.857092°) is the committee's 1956 value (23°15′)
advanced by precession over ~44 years at ~50″·27/yr. The computation is
reproducible (a test recomputes every offset via swisseph); the *choice* is what
the source licenses.

## What changed in code

- `vedic_ayanamsa.py`: `LAHIRI.admitted=True` with `source_copy_hash` +
  `source_locator`; Raman/Krishnamurti stay unadmitted.
- `admission.py`: `vedic/ayanamsa_framework` → `SOURCE_VERIFICATION` + admitted.
- `source_tiers.py`: `calendar_reform_committee_report` = `normative_standard`.
- `acquisition_targets.py`: the target, a placeholder guessing
  `primary_traditional`/`RULE`, reclassified to `normative_standard`/
  `COMPUTATION` by the real source — the same pattern as the gematria P1 target.

Full suite: **2150 passing.**

## What is *not* claimed

- **Vedic does not denote.** `admitted_systems()` is still `['kamea',
  'numerology']`. The ayanāṃśa is a computation license; a meaning needs a
  verified Jyotiṣa denotation source and a corpus/compiler/dictionary scaffold
  that does not yet exist.
- Only **Lahiri** is admitted — not Raman or Krishnamurti.
- A digital surrogate (IA scan), recorded as such — not a physical copy.
- The house-system, dasha, and dignity layers remain blocked on their own
  sources.
