# 1E-V-SOURCE-B — Vedic graha denotation admitted (BPHS)

**Date:** 2026-07-27
**Result:** The seven classical grahas' *karakatva* are admitted from a
copy-verified Bṛhat Parāśara Horā Śāstra. Vedic is now the **third denoting
system** in Representation 1E; concordance can run across Kamea, numerology, and
Vedic.

This built on 1E-V-SOURCE-A: the lagna-lord quantity is a *sidereal* ascendant
sign, so it depends on the admitted Lahiri ayanāṃśa. The ayanāṃśa unblocked the
computation; this source licenses the meaning. Nothing was fabricated.

## The source

Bṛhat Parāśara Horā Śāstra, **English translation and commentary by R.
Santhanam** (Ranjan Publications, New Delhi, **Vol. I, 1984**), based on the
Sitaram Jha (Chaukhambha) Sanskrit edition. A scholarly translation of a primary
text is `primary_traditional`: it transmits the tradition's own significations.

The defining passage is verse **12–13, "Planetary Governances"** (Ch. 3,
"Planetary Characters and Description," printed p. 11):

> The Sun is the soul of all. The Moon is the mind. Mars is one's strength.
> Mercury is speech-giver while Jupiter confers Knowledge and happiness, Venus
> governs semen (potency) while Saturn denotes grief.

This governs the **seven star-planets** — exactly the set the lagna-lord
quantity produces (Rāhu and Ketu rule no sign, so they never appear as a lagna
lord). The coverage is therefore complete for v1, not partial.

## Copy verification (a digital surrogate)

| Check | Evidence |
|---|---|
| Title page | leaf n0: *Bṛhat Parāśara Horā Śāstra / Vol. I / … by R. Santhanam / Ranjan Publications, New Delhi* |
| Date | translator's preface (leaf n5) dated Vijaya Daśamī **1984**; no separate copyright leaf in this edition |
| Pagination | contents place Ch. 3 at p. 8; verse 12–13 read on **p. 11** |
| Passage | leaf n20 (p. 11) read directly and matched to the OCR — a genuine two-method transcription |
| Independent catalog | WorldCat **OCLC 12808639** |
| File hash | jp2.zip sha1 `009466620461fc53721ab9fdffbc759759818214` |

This edition carries its edition statement on the title page and its date in the
dated preface rather than on a separate copyright leaf — documented as such, and
catalog-corroborated. A digital surrogate, recorded as such.

## The mapping (interpretive, blind to Kamea)

Each graha was placed on the shared ontology from BPHS's own karakatva word,
before Kamea's placements were consulted, so any concordance is earned. Every
entry is flagged `mapping_kind="interpretive"`; the null controls weight these
down. The per-graha basis is recorded in
`vedic_denotation_bphs.GRAHA_DENOTATIONS`.

| Graha | Karakatva (BPHS 12–13) | Ontology placement |
|---|---|---|
| Sun | soul of all (ātman) | domain=agency, neutral |
| Moon | the mind (manas) | domain=cognition, neutral |
| Mars | one's strength (bala) | domain=conflict, positive |
| Mercury | speech-giver (vāk) | domain=communication, neutral |
| Jupiter | knowledge and happiness | domain=cognition, positive |
| Venus | potency | domain=affiliation, positive |
| Saturn | grief | dynamic=contraction, negative |

## Code and verification

- `vedic_grahas.py` — the nine grahas, sign rulerships, and the `lagna_lord`
  quantity (sidereal ascendant → ruling graha; blind to the ontology).
- `vedic_denotation.py` — corpus / compiler / dictionary / capabilities for
  graha karakatva. `declared_corpus` compiles to empty (no source).
- `vedic_denotation_bphs.py` — the acquired corpus: the verified BPHS
  manifestation, its copy, and the seven doubly-transcribed karakatva passages;
  `canonical_dictionary()` binds it.
- `admission.py` — `vedic/denotation` → `DENOTATION` + admitted.

Compiles to **seven source-specific denotations**; `is_concordance_eligible()`
is `True`; `admitted_systems()` is `['kamea', 'numerology', 'vedic']`. Live
check: a Leo ascendant makes the Sun the lagna lord → `domain=agency`, which
meets a Kamea agency claim in a real cross-system verdict. Full suite passing.

## What is *not* claimed

- **Vedic denotes only via this layer.** The ephemeris/nakshatra/varga layers
  are computation; the house-system and dasha layers remain blocked on their own
  sources.
- Only the **seven star-planets**; Rāhu/Ketu are out of scope (and unreachable
  as a lagna lord).
- The lagna-lord is one, deliberately narrow, subject-varying selector; richer
  Vedic quantities (a graha's own placement, ātmakāraka) are future work.
- The legacy `knowledge/planets` and `vedic_interpreter` modules stay
  quarantined; the scaffold sources nothing from them.
- This makes Vedic *comparable on licensed evidence* — it does not claim Vedic
  agrees with any other system.
