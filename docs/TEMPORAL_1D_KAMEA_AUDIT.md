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

## Era predictability — the 2A confound, in R1 space

Accepting static slow bodies has a direct consequence: **a static cell is an
era marker, not an event marker.** Saturn's cell changes roughly every 3.3
years, so Saturn's cell *is* approximately a decade label.

That is the outer-planet era-leakage failure from Temporal 2 v1 reappearing in
R1 form, and it must be measured before any R1 event study runs:

> How well can R1 alone distinguish early-period from late-period timestamps?

Fit a simple era classifier on R1 features alone and report its accuracy per
body and per scale. If Saturn and Jupiter cell occupancy strongly predicts era
— and it almost certainly will — then **event/control balance must be checked
in R1 space, not only in R0 space**, and the existing control-quality artifact
must be extended before 2B.

---

## R1 control quality (required before 2B)

Extending `control_quality.py` to R1. Every R1 event study reports, per body:

```text
cell occupancy imbalance      transition-rate imbalance
core-shape imbalance          stationary-path frequency
era predictability
```

Same enforcement as the R0 gate: a study that omits it produces no output. The
v1 failure is the reason that gate exists, and R1's degeneracy makes the same
failure *more* likely here, not less.

---

## Deliverables

- [x] `representation_schema_hash` — R1 identity covering feature schema,
      trajectory spec, scale and reduction version
- [x] `representation_occupancy` — support, effective support, tail structure
- [ ] B0–B3 baseline encoders, sharing sample times and bin widths
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
