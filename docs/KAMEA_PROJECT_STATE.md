# The Kamea / Structural-Identity Project — State of the Truth

**Purpose.** This is the "start here" record so the same conversation doesn't get
had again. It states, plainly, what the structural-identity system *is*, what has
been rigorously tested and found **null**, what is genuinely **real**, the one
bug that keeps recurring (and its fix), and what remains open. Written
2026-07-29, reconciled against the code and against a set of prior ChatGPT design
conversations on the same project.

If you are re-deriving any of the null results below, stop: they were
pre-registered or confound-controlled, and they came back null. New evidence
would have to clear that same bar, not a fresh exploratory pass.

---

## 1. What the system is

A name is turned into an analyzable structure:

```
name
 -> 3 ciphers (English ordinal, Hebrew literal, Hebrew phonetic)
 -> 7 planetary kameas (magic squares 3x3 Saturn ... 9x9 Moon), reduction ((n-1)%cap)+1
 -> 21 traversal graphs (3 ciphers x 7 planets), sequence + self-loops preserved
 -> features normalized WITHIN each cipher x planet group
 -> Identity Vector: 24 features x 21 groups -> 7 per-planet composites -> 1 vector
```

- **ACF is source, the compiled identity vector is runtime.** Adding features
  changes the compiled vector, not the source profiles.
- Two halves hide inside the project (the ChatGPT design flagged this too): (a) a
  symbolic transformation pipeline, and (b) the claim that it captures real
  differences between people or predicts outcomes. **(a) is built and sound.
  (b) is what all the testing below addresses.**

## 2. What is REAL (durable, within-system)

- **Planets are distinct structural operators.** The planet is recoverable from
  the shape alone at ~58% (p=0.003), and this is not confoundable. This is the
  one clean structural positive. (`planets-as-structural-operators`)
- **Within-group normalization is the load-bearing idea.** Comparing features
  only within a cipher x planet group makes the vector individual, reproducible,
  and corpus-independent. This is why the 24-feature vector discriminates people
  while the coarse labels do not.
- **Cross-cipher agreement is high (~0.99).** The three independent translations
  converge on the same signature, so a profile is not an artifact of one
  encoding. (Wired 2026-07-29.)
- **The fine-grained vector varies continuously and individually.** It is the
  real representation of a person in this system.

## 3. What is NULL (tested rigorously, keeps coming back null)

Every confound-controlled attempt to connect the structure to something
*external* has failed:

| Claim | Result | Detail |
|---|---|---|
| name-kamea vs birth-Vedic chart | **null** | Mantel r=+0.007, p=0.11, n=1885 |
| kamea flow vs historical catastrophes | **null** | p=0.36, n=86, era-controlled, pre-registered |
| civilization turning points vs planetary cycles | **null** | Rayleigh p=0.75 / 0.79, n=70 |
| occupation separation | **confounded** | separates by birth-month / name-demographics, not structure |
| longevity prediction | **collapses** | p=0.025 raw -> p=0.22 under nationality control |
| relationship similarity | **dead metric** | saturated ~0.999; rivals rank *most* alike |
| 1E-A cross-system concordance (numerology vs Vedic) | **null** | gap ~0, flips sign with RNG seed |
| entry-timing edge (range / momentum) | **null** | inverts out-of-sample on a disjoint cohort |

**The pattern is total: the durable positives are all within-system; nothing
reaches out and correlates with an external outcome — historical, behavioral,
occupational, or relational.** The framework's value is that it makes these
nulls measurable and refuses to read symbolic breadth as meaning.

## 4. The recurring bug (this is the loop-breaker)

The same failure appeared **three times in one session**, and has the same fix
every time:

> **Any coarse summary built by comparing raw scores across incomparable scales
> collapses to a constant — a scale artifact masquerading as a finding.**

| Summary | Collapsed to (everyone) | Cause |
|---|---|---|
| Functional role + structural state | Regulator + Adaptive | argmax over driver/amplifier/regulator on non-overlapping scales; state thresholds unreachable |
| v2 role classifier | Explorer | same disease, different constant |
| Planet ranking / top-3 "active stack" | Saturn/Jupiter/Mars, Saturn #1 | raw kamea_score is grid-size biased (small squares score higher) |

**The fix, applied to all three: normalize within the comparable group
(population-relative z-score) before ranking or argmax.** After the fix:
- roles distribute (Amplifier/Regulator/Driver/Hybrid ~30/28/24/18),
- states distribute (Adaptive/Fragile/Stable ~50/28/20),
- the top-3 stack varies (3 possible sets -> 33; all seven planets appear as
  someone's strongest; Saturn drops from 100% to the *rarest* standout).

**Lesson to keep:** the fine-grained, within-group-normalized *vector* was always
the real representation. Every coarse "which planet / which archetype" label
built on raw cross-scale scores is an artifact until it is normalized the same
way. Do real comparison on the vector; treat labels as lossy, population-relative
tags, clearly caveated.

Concrete illustration — the same person, before vs after the fix:
`Michael Elvis Brockway` read as **Regulator + Saturn-led top-3** (both
artifacts); after the fix, **Amplifier**, with an individual top-3 that is
actually his elevated planets. The pre-fix reading pointed the *wrong way*.

## 5. Reconciliation with the ChatGPT design conversations

- They were largely **re-derivations** of the architecture Atlas already had,
  usually less rigorously (no perturbation/confound/pre-registration machinery).
- They did prompt **two real improvements** that shipped: cross-cipher confidence
  wiring, and the extended graph/geometric feature set (17 -> 24 features).
- The vivid four-archetype story — "recursive system / directional weapon /
  radiant hub / network field" for four named people — **is not in the data**:
  three of the four classified identically before the fix, and the labels were
  the scale artifact above. Confident symbolic narration of images and sigils is
  precisely the failure mode the rigor exists to prevent.
- **No new science.** An independent designer converging on the same architecture
  is mild evidence the design is sound, not evidence the hypothesis is true.

## 6. What is genuinely OPEN

- **Sofit** (Hebrew final-form values 500-900) is missing from the literal
  cipher; a real correctness gap the design flagged as critical.
- **Baked calibration constants** (classification score baseline, per-planet
  ranking baseline) should become hashed calibration artifacts, not constants
  that drift as the corpus grows.
- The classification/ranking fixes apply to the **on-the-fly build path**; the
  stored ACF corpus still carries the old `essence.classification` until rebuilt.
- The standing empirical question — does the fine vector's continuous individual
  signal correlate with *anything* external? — remains open only in the sense
  that not every possible outcome has been tried. Everything tried so far is
  null, and the honest prior is that it will stay null.

## 7. Bottom line

The Kamea system is a rigorously-built, internally-consistent **symbolic topology
engine**. It produces individual, reproducible structural signatures, and the
planets behave as distinct operators. It **does not predict or correlate with
external outcomes** — every confound-controlled test returns null. The coarse
archetype labels were misleading scale artifacts (now made population-relative,
but still lossy next to the vector).

**Real as structure. Null as prediction.** That verdict is settled; treat it as
the baseline, not as something to re-open without evidence that clears the bar
the tests above already set.
