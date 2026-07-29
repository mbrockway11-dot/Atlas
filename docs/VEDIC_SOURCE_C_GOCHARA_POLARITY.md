# 1E-V-SOURCE-C — Gochara transit polarity admitted (Phaladīpikā)

**Date:** 2026-07-27
**Result:** The gochara transit-polarity table is sourced from Phaladīpikā and
wired into the transit substrate. A Vedic transit claim now carries its axis and
coordinate from the graha karakatva (BPHS, 1E-V-SOURCE-B) and its **polarity**
from the gochara table (Phaladīpikā): the same transit is benefic or malefic by
its house from the Moon.

This was a deliberate second source, not BPHS. BPHS states transit quality only
through the chart-specific Aṣṭakavarga (bindu) method, not a fixed table — so a
clean per-graha gochara polarity required a text that states one, which
Phaladīpikā does.

## The source

Mantreśvara's **Phaladīpikā**, English translation by **V. Subrahmanya Sastri**
(**2nd Edition, 1950**, Aruna Press, Bangalore). Tier: `primary_traditional` (a
scholarly translation of a primary text). WorldCat OCLC 459723994.

The passage is **Adhyāya 23 (Gocara), Ślokas 3–10**, printed pp. 258–261. Ślokas
3–9 give, per graha, the houses counted from the Moon in which its transit is
auspicious; Śloka 10 fixes the rest:

> Thus have been described the benefic positions; the rest are to be understood
> as malefic.

So the polarity is **total**: auspicious house → positive, every other → negative.

## The table (page-image verified)

| Graha | Benefic houses from Moon | Śloka | p. | leaf |
|---|---|---|---|---|
| Sun | 3, 6, 10, 11 | 3 | 258 | n294 |
| Moon | 1, 3, 6, 7, 10, 11 | 4 | 258 | n294 |
| Mars | 3, 6, 11 | 5 | 259 | n295 |
| Mercury | 2, 4, 6, 8, 10, 11 | 6 | 259 | n295 |
| Jupiter | 2, 5, 7, 9, 11 | 7 | 260 | n296 |
| Venus | 1, 2, 3, 4, 5, 8, 9, 11, 12 | 8 | 260 | n296 |
| Saturn | 3, 6, 11 | 9 | 261 | n297 |

All seven were read off the page images **and** cross-checked with the OCR — a
two-method transcription. This mattered: the OCR conflated some *from-Moon* lists
with *from-Sun* lists (it rendered Saturn's from-Moon as the from-Sun list), a
corruption only the page image disambiguates. Edition confirmed from the copy's
own "Preface to the Second Edition" (dated 13 September 1950, V. Subrahmanya
Sastri). A digital surrogate (IA scan `Phaladeepika2ndEd.1950ByVSubrahmanyaSastri`,
jp2.zip sha1 `ddaa647b…`), recorded as such.

## Code

- `vedic_gochara.py` — the sourced table with provenance, and
  `gochara_polarity(graha, house_from_moon)` → positive/negative (total, per
  Śloka 10). Source-layer: returns bare polarity literals, never imports the
  ontology. Nodes are out of scope (no rule invented).
- `vedic_transits.transit_claims` — now takes each transit claim's axis and
  coordinate from the BPHS karakatva and its polarity from the gochara table by
  the graha's house from the Moon; a graha without a sourced gochara rule is
  skipped, not given an invented quality.

Verified live: with the natal Moon in Aries, Saturn transiting the 3rd is
`contraction/positive` and the 1st is `contraction/negative` — the same graha,
opposite quality by gochara house. Full suite passing.

## What is *not* claimed

- The gochara here is the classical **from-the-Moon** table only. Phaladīpikā
  also gives from-Sun, from-Lagna and from-each-planet tables; those are not
  admitted.
- A transit claim still has **no comparison partner**: only Vedic has a transit
  mode, and the `event`-scope / 1E-B event-linking side is unbuilt. The transit
  denotation is complete and sourced; its consumer — correlating transit-timed
  claims with real dated events under null controls — is the remaining work.
- This makes transits *expressible on licensed evidence*, not that any transit
  predicts any event.
