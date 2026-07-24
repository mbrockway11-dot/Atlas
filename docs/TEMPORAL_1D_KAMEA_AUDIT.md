# Temporal 1D — Kamea Information-Loss and Scale Audit

**Status:** open · **Type:** characterization, not hypothesis testing ·
**Blocked by:** none — [1C](TEMPORAL_1C_KAMEA_SPECIFICATION.md) is closed ·
**Blocks:** Temporal 2B

1C froze the representation. 1D measures what it costs. The milestone
deliberately does **not** search for a better sampling rule — that search
ended when the constraint was shown to be structural rather than a tuning
failure.

---

## The question

R1 is a deterministic function of the astronomical state, so it cannot add
information in the Shannon sense. The R0 audit already established that the
state occupies a low-dimensional manifold: 140 nominal dimensions carrying
~6 effective ones. R1 is a further, deliberately lossy, projection of that.

So the question is not "how much information does R1 carry" but:

> How much of R0 does R1 discard, what kind of structure does it retain, and
> is any of that structure attributable to the *Kamea geometry* rather than to
> coarse longitude binning?

That last clause is what makes the audit falsifiable, and it is the reason for
the baselines below.

---

## Baseline encodings

Every measurement is reported against all four. Without them a positive result
about R1 is uninterpretable, because quantization alone would produce one.

```text
B0   current Kamea cell only          -- no path, no order
B1   ordered sequence of Kamea cells  -- path, no reduction
B2   reduced / core geometry          -- the R1 claim
B3   longitude-bin encoding, no Kamea -- same bins, no geometry
```

**B2 versus B3 is the decisive comparison.** B3 uses each body's identical bin
widths and identical sample times, and simply omits the magic-square lookup.
If B2 performs no differently from B3, the geometry is adding nothing beyond
quantization, and R1's symbolic content carries no statistical content.

B0 versus B1 separates the value of *path* from the value of *position*.

---

## Measurements, per body and per scale

Across `R1-W3D`, `R1-W30D`, `R1-W180D`, `R1-W1Y`:

```text
collision rate over time            distinct instants, identical R1 state
duration of identical R1 states     how long a state persists
transition frequency                cell changes per unit time
effective dimensionality            participation ratio, as in the R0 audit
core-shape diversity                distinct shapes observed / possible
entropy of raw and reduced paths    before and after reduction
sensitivity near cell boundaries    stability conditioned on distance to a bin edge
dependence on year or era           the 2A confound, in R1 space
reconstructability of longitude     how coarsely R0 can be recovered from R1
redundancy with R0                  variance of R1 explained by R0
```

Two deserve emphasis.

**Boundary sensitivity.** Aggregate path stability passed at 1 minute, but the
aggregate hides conditioning: an instant sitting a hair from a bin edge is
exactly where a shift flips a cell. The measurement is stability *given*
distance to the nearest boundary, and the reportable quantity is the fraction
of instants inside the fragile band.

**Reduction's effect.** Comparing entropy before and after reduction answers
the question left open in 1C: whether reduction absorbs cell-level
discontinuity or merely hides it.

---

## Representation occupancy

Distinct from collision rate, and the distinction is load-bearing: collisions
say whether *different inputs map together*; occupancy says *how much of the
representation space is reached at all*. A body can have few collisions and
still only ever produce a handful of shapes — and that handful is its real
capacity.

Per body and per scale: fraction of reachable reduced geometries observed,
their frequency distribution, effective support (exponentiated Shannon
entropy), and dominant-core versus long-tail behaviour.
`representation_occupancy()` implements it.

### Preliminary measurement

400 instants at 13-day spacing from 1970. Not the full audit — no baselines,
one cohort — but it sizes the effect:

```text
                 R1-W3D                          R1-W1Y
body      shapes  eff_supp  top1  stat     shapes  eff_supp  top1  stat
saturn         4      1.07 0.990 0.990          8      5.75 0.338 0.145
jupiter        9      1.21 0.970 0.970         41     31.54 0.105 0.000
mars           9      2.51 0.757 0.757        390    386.37 0.005 0.000
sun           29     13.96 0.395 0.395        200    130.24 0.025 0.000
venus         12      4.82 0.505 0.140        400    400.00 0.003 0.000
mercury      114     56.91 0.175 0.175        400    400.00 0.003 0.000
moon         217    178.12 0.020 0.000        400    400.00 0.003 0.000
```

`eff_supp` = effective number of shapes in play; `top1` = share of the most
common shape; `stat` = fraction of stationary paths.

**Effective support spans three orders of magnitude.** At R1-W3D, Saturn's
effective support is **1.07** — 99% of instants produce the identical shape,
so R1-W3D Saturn is very nearly a constant and carries almost no information.
The Moon at the same scale reaches 178.

**Caveat, and it matters:** at R1-W1Y, Venus, Mercury and the Moon all report
400 shapes from 400 instants with a singleton share of 1.0. That is saturation
of the *sample*, not measurement of the space — high capacity and
"sample too small" are indistinguishable there. The full audit needs a cohort
large enough to un-censor it, and must report where the ceiling was hit rather
than treating 400/400 as a result.

**This already sharpens the era concern below.** Saturn reaches only 5.75
effective shapes across 55 years at R1-W1Y — roughly an era label, exactly as
the 3.27-year cell-crossing time predicts.

---

## B0–B3 audit — first results

```bash
.venv/Scripts/python.exe scripts/run_kamea_baseline_audit.py
```

80 instants, deterministic irregular cohort plus a 13-day lattice. Effective
support per encoding, with the reduction's collapse ratio and entropy
retention:

```text
--- R1-W3D ---
body       B0_eff  B1_eff  B2_eff  B3_eff  collapse  H_kept  measurable
saturn       7.76    7.76    1.00    7.76      9.00   0.000  True
jupiter     14.35   15.16    1.14   15.16      6.00   0.049  True
mars        22.08   33.57    2.44   33.57      6.83   0.253  True
sun         29.69   65.26   10.91   65.26      2.88   0.572  True
venus       37.47   75.95    3.96   75.95     11.00   0.318  True
mercury     44.76   78.63   42.12   78.63      1.49   0.857  True
moon        47.15   80.00   75.95   80.00      1.04   0.988  False

--- R1-W1Y ---
saturn       7.76   53.99    6.12   53.99      6.78   0.454  True
jupiter     14.35   77.27   33.57   77.27      1.95   0.808  True
mars        22.08   80.00   78.63   80.00      1.01   0.996  False
sun         29.69   53.58   53.58   53.58      1.00   1.000  False
venus       37.47   80.00   80.00   80.00      1.00   1.000  False
mercury     44.76   80.00   80.00   80.00      1.00   1.000  False
moon        47.15   80.00   80.00   80.00      1.00   1.000  False
```

### The harness is sound

**`B3_eff == B1_eff` in every single row.** Cell lookup is a bijection and the
numbers confirm it exactly — identical effective support, identical entropy,
identical collision structure. The encodings are genuinely matched, and the
audit reports a harness fault rather than a finding if they ever diverge.

### B0 → B1: traversal adds substantially

Effective support rises from 7.76 to 53.99 for Saturn at R1-W1Y, and from
29.69 to 65.26 for the Sun at R1-W3D. Temporal traversal is not decoration;
the centre cell alone discards most of what the representation distinguishes.

### B1 → B2: reduction works only where the path revisits cells

This is the mechanism, and it is sharp:

- Where a body **revisits cells** — slow bodies, short windows — reduction
  collapses aggressively. Saturn at R1-W3D collapses 9 paths to 1 shape and
  retains **zero** entropy: its effective support is exactly 1.00, a literal
  constant.
- Where a body **never revisits a cell** — fast bodies, long windows —
  reduction is an **identity map**. Sun, Venus, Mercury and the Moon at
  R1-W1Y all show collapse 1.00 and `H_kept` 1.000. Core geometry *is* the
  path, so B2 carries exactly B3's information.

So the reduction's equivalence structure is not a fixed property of the
geometry. It is entirely a function of whether the sampling window lets the
body return to a cell it has already occupied.

### B2 ↔ B3D: the decisive comparison, answered

The earlier B2-vs-B3 gap conflated two mechanisms. Splitting them:

```text
B3   ordered bin sequence
 ├── B3D  dedup only, same rule, no square
 └── B2   Kamea projection + reduction
```

**A second bijection appears, and it locates the entire effect.** Dedup keeps
positions and value→cell is invertible, so deduplicating the bin sequence and
deduplicating the cell sequence produce the same partition. Measured:
`B3D` and `B2R` (core geometry before translation) agree exactly on class
count, entropy and collision structure in every body and scale.

Combined with `B1 ≡ B3`, that means:

> **Every information difference between B2 and B3D comes from translation
> normalization** — the single step that uses the grid's two-dimensional
> structure. Everything else in the Kamea pipeline is bijective relabelling.

### The measured answer

80 instants, irregular cohort. `cls` = equivalence classes; `merges` = pairs
B2 calls equal that B3D did not; `NMI` = normalized mutual information.

```text
--- R1-W3D ---
body      cls_B3D  cls_B2  refines  merges    NMI  dedup_act  transl_act
saturn          9       1     True    2723  0.000      0.960       0.889
jupiter        18       3     True    2811  0.049      0.959       0.833
mars           38       6     True    1792  0.257      0.950       0.842
sun            51      24     True     566  0.623      0.937       0.529
venus          44       7     True    1090  0.374      0.924       0.841
mercury        69      53     True      57  0.892      0.903       0.232
moon           77      77     True       0  1.000      0.253       0.000

--- R1-W1Y ---
saturn         21       9     True     402  0.641      0.932       0.571
jupiter        40      40     True       0  1.000      0.841       0.000
mars           79      79     True       0  1.000      0.257       0.000
sun            60      60     True       0  1.000      0.508       0.000
venus          80      80     True       0  1.000      0.121       0.000
mercury        80      80     True       0  1.000      0.122       0.000
moon           80      80     True       0  1.000      0.048       0.000
```

**H3 is false at the partition level.** `left_refines_right` holds in all 14
cases: B2 is a pure *coarsening* of B3D. The square never separates two
trajectories that dedup alone called equal — so it does not induce a different
*notion of closeness*, only fewer distinctions.

**H2 is true, but narrowly and in the wrong direction to be useful.** The
square does induce additional equivalence classes, via translation-invariance
of the core figure — and "which trajectories are translates" genuinely depends
on the arrangement, since longitude translation is *not* grid translation.
But:

- Where the representation actually discriminates — fast bodies, long windows
  — translation makes **zero merges** and NMI is exactly **1.000**. B2 ≡ B3D.
  The geometry does literally nothing in the regime that matters.
- Where translation is most active, it is *destructively* active. Saturn at
  R1-W3D coarsens 9 classes to **1**, NMI **0.000**. That is not structure
  being exposed; it is all information being removed.

The mechanism is figure size: translation only merges when core figures are
small enough to coincide, which happens exactly where paths are degenerate.
Jupiter at R1-W1Y has high dedup activity (0.841) yet zero translation merges,
because its figures are large and varied.

### What this establishes

> After removing repeated-cell elimination, the Kamea arrangement contributes
> **only a translation-invariant coarsening** — never a reorganization. That
> coarsening is inactive wherever the representation discriminates, and where
> it is active it collapses toward a single class.

For this representation, the geometry is **largely ornamental**, with the
caveat that where it acts it is subtractive rather than structuring. That is a
clean negative result about the square's statistical contribution, and it is
independent of any event outcome. It does not bear on the arrangement's
symbolic content, which is not a claim this audit can test.

### Cadence sensitivity caught a real artifact

The check was not decorative. Mercury at R1-W3D:

```text
mercury   irregular 42.12   regular_13d 29.42   spread 0.302   CONSISTENT: False
```

The 13-day lattice aliases against Mercury's period and *understates* its
effective support by roughly 30%. The Moon is borderline at 0.226. Every other
body agrees within 13%. Conclusion: **occupancy estimates from a single
regular cadence are not trustworthy for the fast bodies**, and the irregular
cohort is the one to report.

### Saturation

24 of the reported measurements are saturated (observed = samples) and are
flagged `capacity_measurable: false` rather than being read as capacity. All
fast bodies at R1-W1Y are in that set. Chao1 and Good–Turing are computed
alongside, so the uncensored run has estimators ready.

---

## Era predictability — the 2A confound, in R1 space

Accepting static slow bodies has a direct consequence: **a static cell is an
era marker, not an event marker.** Saturn's cell changes roughly every 3.3
years, so Saturn's cell *is* approximately a decade label.

That is the outer-planet era-leakage failure from Temporal 2 v1 reappearing in
R1 form, and it must be measured before any R1 event study runs:

> How well can R1 alone distinguish early-period from late-period timestamps?

### Measured

```bash
.venv/Scripts/python.exe scripts/run_kamea_era_predictability.py
```

120 instants inside 1970–1980 and 2010–2020, year-blocked 4-fold validation,
150 block permutations. `unseen` = share of test signatures never seen in
training.

```text
                              acc   unseen      MI       p
R1-W3D/saturn/B3            0.880    0.067   0.635   0.007   <-- leak
R1-W3D/saturn/B3D           0.887    0.052   0.635   0.007   <-- leak
R1-W1Y/saturn/B3D           0.881    0.420   0.693   0.007   <-- leak
R1-W3D/saturn/B2            0.507    0.000   0.012   0.291
R1-W1Y/saturn/B2            0.287    0.056   0.070   0.921
R1-W3D/jupiter/B3D          0.171    0.053   0.155   0.947
R1-W3D/moon/B3D             0.493    0.704   0.550   0.629
R1-W1Y/moon/B3              0.500    1.000   0.693   0.079
```

**Saturn leaks era, and only Saturn.** Its quantized trajectory separates two
decades forty years apart at **88% balanced accuracy, p = 0.007**, with a low
unseen-class rate — so the separation generalizes across held-out year blocks
rather than resting on the fallback. Precisely what the 3.27-year cell-crossing
time predicts. No other body exceeds the 0.70 threshold at any scale.

**Translation *masks* the Saturn era signal by collapsing the classes that
carry it.** Saturn's B2 falls to chance (0.507 at W3D; MI 0.635 → 0.012).

The wording is load-bearing, so state the contrast plainly:

```text
statistical adjustment:      preserve relevant information
                             remove nuisance association

translation normalization:   discard distinctions
                             nuisance association disappears as a consequence
```

B2 does not *correct* the era leak. It is not cleaner than B3D — it is
emptier. So **a null B2 diagnostic cannot certify a clean control design**,
and reading one as evidence of era-independence would invert the finding.

Two truths must both be preserved:

1. R1's quantized trajectory layer is era-sensitive for Saturn.
2. R1's translation-normalized geometry can conceal that sensitivity by
   destroying the relevant information.

### Mutual information is unusable under saturation

`MI = 0.693` is `ln 2`, the maximum for a balanced binary label, and it appears
wherever the unseen-class rate reaches 1.000. When every signature is unique,
MI is maximal *by construction*. The block-permutation null correctly declines
to call these significant (p = 0.079), which is what makes the pair
interpretable.

**So blocked accuracy plus the block-permutation null are the era diagnostics;
MI alone is not**, and `unseen_class_rate` must be reported beside any MI.

### Sub-chance accuracy is a fallback artifact, not anti-information

Jupiter's 0.171 at R1-W3D looks dramatic and is not a finding: classes learned
in one era do not recur in the other, so the majority fallback predicts wrongly
on held-out blocks. The p-values confirm it (0.947, 0.960). Recorded because a
reader meeting 0.171 without this note would reasonably assume signal.

**Consequence for 2B:** event/control balance must be checked in R1 space for
Saturn specifically, and the existing control-quality artifact must be extended
before 2B runs.

---

## R1 control quality — implemented and enforced

`r1_control_quality.py`. Stricter than the R0 gate, because R1 introduces a
failure mode R0 does not have.

### The structural rule

> **A downstream coarsening may not be used to certify balance in an upstream
> representation.**

Without it, this passes silently:

```text
events and controls differ strongly in Saturn phase
        ↓
B2 erases the distinction
        ↓
B2 balance check passes
        ↓
study appears properly controlled
```

`write_r1_result` refuses to write when events and controls are
distinguishable in B3 or B3D **even if B2 looks balanced**, and refuses again
when the upstream encodings fail on their own terms. A masked cohort produces
no output at all.

### Asymmetric thresholds, by failure category

One global threshold would miss most of these, because the bodies fail
differently:

| category | trigger | who fails this way |
|---|---|---|
| era leakage | blocked accuracy ≥ 0.70 with p < 0.05 | Saturn |
| saturation | unseen-class rate > 0.50; MI suppressed from interpretation | fast bodies |
| degeneracy | dominant class share > 0.90 | slow bodies, short scales |
| translation masking | B3D imbalanced or era-predictive while B2 is not | B2 |
| support mismatch | class-support overlap < 0.50 | any |

### The Saturn regression gate

The measured behaviour is now a permanent fixture in
`tests/test_r1_control_quality.py`:

- Saturn B3D **must** separate 1970–1980 from 2010–2020 above threshold, with
  a low unseen-class rate.
- Saturn B2 **must** show the documented information loss (gap > 0.2).
- The fast bodies **must not** spuriously exceed the threshold.

If any of these stops holding, the representation changed and the audit's
conclusions no longer follow from the code.

**Still to do:** prove that an era-matched *control generator* eliminates the
separability. The current study proves the representation contains era
information; it does not yet prove the matching procedure removes it.

### Reporting rules, frozen

Three quantities that the Moon case showed are genuinely distinct —
population association, sample memorization, held-out predictability:

- Never report MI without the unseen-class rate.
- Treat MI as uninterpretable above the saturation threshold.
- Blocked permutation significance is the authoritative era verdict.
- Report accuracy only alongside fallback behaviour and class coverage.
- `|balanced_accuracy − 0.5|` may be used descriptively for sub-chance cases,
  never as evidence on its own.

---

## The general principle

Beyond R1, and worth stating on its own:

> **A lossy representation can make a confounded dataset appear balanced.**

Balance must therefore be certified in the representation that carries the
information, not in whatever representation the analysis happens to consume.

---

## Deliverables

- [x] `representation_schema_hash` — R1 identity covering feature schema,
      trajectory spec, scale and reduction version
- [x] `representation_occupancy` — support, effective support, tail structure
- [x] B0–B3 baseline encoders, sharing sample times and bin widths, with the
      B1≡B3 bijection asserted as a harness check
- [x] Cohort generator: deterministic irregular plus coprime lattices,
      reported separately, with saturation flagged
- [x] Chao1 and Good–Turing estimators for saturated samples
- [x] Capacity / compression / stability measured together, never alone
- [x] **Dedup-matched B3D** — separates repeat-removal from the arrangement,
      and answers the decisive question
- [x] Equivalence-class refinement: partition comparison, not just entropy
- [x] `reduction_activity` — where each operation is an identity map
- [ ] Per-body, per-scale measurement suite, on a cohort large enough that
      occupancy is not censored at the sample size
- [ ] Boundary-conditioned stability, with the fragile-band fraction
- [ ] Entropy before and after reduction
- [ ] Era-predictability diagnostic per body and scale
- [ ] R1 control-quality artifact, gated like the R0 one
- [ ] Written finding on B2 versus B3

---

## Then, and only then: Temporal 2B

A nested comparison, not a standalone R1 test:

```text
Model A:  R0
Model B:  R1
Model C:  R0 + R1
```

The claim of interest is C over A. B alone is uninterpretable, because it
could reflect coarse longitude bins or era occupancy rather than geometry —
which is precisely what 1D is built to determine in advance.
