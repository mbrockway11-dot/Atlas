# Temporal 1C — Planetary→Kamea Specification

**Status:** open · **Type:** design milestone, not validation · **Blocks:**
Temporal 1D and 2B · **Does not block:** Temporal 2A (raw-state baselines)

Milestone 2 is split, because its two halves ask different questions:

```text
2A   Raw-state event baselines (R0)
     Is there any detectable association in the astronomical state itself?
     STATUS: earthquake baseline complete, null under five sound controls

2B   Kamea event baselines (R1/R2)
     Does the Kamea representation expose anything beyond R0?
     STATUS: blocked on this specification
```

2A answers a question about the world. 2B answers a question about a
representation, and can only be asked once 2A has established what the
representation would have to improve on. The same separation between
characterization and hypothesis testing is what made the identity branch
tractable.

---

## Why this is a design milestone

Identity Validation 2A worked because the object under test already existed:

```text
name → ciphers → integers → Kamea projection
```

The temporal equivalent has a hole in it:

```text
planetary longitude → ??? → Kamea projection
```

`project_values_to_kamea` accepts `list[int]`. Nothing in Atlas converts a
planetary state into those integers, and no temporal module imports the Kamea
subsystem at all.

Filling that hole is a modelling decision. If it is made inside a validation
script, every subsequent result validates the mapping that script invented
rather than anything about Atlas. So the specification comes first, is frozen,
and only then is audited.

---

## Required invariants

A candidate mapping must satisfy all five before it is considered. These are
stated now, before any candidate is evaluated.

### 1. Deterministic

The same planetary state maps to the same Kamea state, always. No wall-clock
input, no iteration-order dependence, no floating-point path that varies with
platform. Testable exactly as the temporal compiler is: repeated runs produce
an identical `values_hash`.

### 2. Continuous where appropriate

Small longitude changes must not produce arbitrary jumps, except at
boundaries that are *explicitly declared* as part of the mapping.

This has teeth. The R0 audit measured continuity directly: median state
distance rises smoothly from 0.0008 at one minute to 1.10 at one day, with no
discontinuities. A mapping that introduces cliffs must declare where they are
and justify them, because an event study whose features jump across a
one-minute boundary will manufacture fragile results wherever timestamps are
uncertain.

**Acceptance:** the fraction of one-minute steps that cross a declared
boundary must be measured and reported, not discovered later.

### 3. Planet-local

Mars' mapping depends on Mars alone, unless a composite feature is
deliberately and separately defined. Cross-contamination would make per-planet
features uninterpretable and would silently smuggle relational information
into what reads as a single-body measurement.

### 4. Reversible enough

Given a Kamea state, the approximate longitude region that produced it must be
recoverable. This is what makes the representation auditable: a mapping whose
inverse is unbounded cannot be checked for information loss, only assumed.

**Acceptance:** median and 90th-percentile circular reconstruction error,
reported per body.

### 5. Symbolically meaningful

The mapping must correspond to an articulated Kamea interpretation, not an
arbitrary integer encoding chosen for convenience. If Atlas is following an
esoteric tradition, the mapping should be defensible within it. A mapping that
is mathematically tidy but symbolically arbitrary makes any downstream result
uninterpretable regardless of its statistics.

---

## Measured constraints

The candidates below were first written from intuition about what a magic
square does. Measuring the existing machinery removed two of them and changed
what the remaining question is. Pinned by `tests/test_kamea_locality.py`.

### Kamea projection is discontinuous by construction

Mean grid distance between consecutively valued cells, against the mean
distance between arbitrary cell pairs in the same square:

| kamea | size | cells | consecutive | random | ratio |
|---|---|---|---|---|---|
| saturn | 3 | 9 | 2.25 | 1.78 | **1.27** |
| jupiter | 4 | 16 | 2.93 | 2.50 | **1.17** |
| mars | 5 | 25 | 3.08 | 3.20 | 0.96 |
| sun | 6 | 36 | 3.94 | 3.89 | 1.01 |
| venus | 7 | 49 | 3.38 | 4.57 | 0.74 |
| mercury | 8 | 64 | 5.17 | 5.25 | 0.99 |
| moon | 9 | 81 | 3.52 | 5.93 | **0.59** |

Consecutive values land about as far apart as randomly chosen cells, and for
Saturn and Jupiter *further* apart than random. Not one square is
locality-preserving.

This is not a defect. A magic square is constructed so rows, columns and
diagonals sum equally, which requires scattering consecutive values; locality
and the magic property are in direct tension. The scattering is the thing.

**Consequence: invariant 2 is unsatisfiable by any mapping that feeds
near-adjacent integers into `reduce_value`.** The discontinuity lives in the
square, not in the quantizer, so no choice of quantizer avoids it. Degree
quantization would send longitudes 1° apart to effectively unrelated cells —
and so would every other scheme of that shape.

### The existing reduction is already modular

```python
def reduce_value(self, value: int) -> int:
    return ((value - 1) % self.max_value) + 1
```

Candidate C below described this as a design option. It is the current
behaviour of the pipeline, so it is not available to be chosen or rejected.

### A Kamea state is a path, not a cell

`project_values` consumes an ordered `list[int]` and returns a traversal:
`raw_values`, `reduced_values`, `coordinates`. A name supplies its order
naturally — letters in sequence. **Planetary positions at an instant are
simultaneous and carry no intrinsic order.**

This is the gap the original framing missed. The open question is not "how
does a longitude become a cell" but "what ordered integer sequence represents
an instant" — a question about sequence construction, which the candidates
below do not address at all.

### The machinery covers 7 of 10 bodies

`PLANETARY_TRANSFORM_WEIGHTS` and `KAMEAS` have identical keys: the seven
classical planets. Uranus, Neptune and Pluto have no square and no weights,
and `transform_values_for_planet` raises on them. R0 records 10 bodies.

Note this interacts with 2A's finding: the outer planets were exactly the
features that drove v1's spurious result. A representation that excludes them
is not obviously worse.

---

## Candidate mappings

Recorded with their trade-offs, **corrected against the measurements above**.
None is yet chosen, and the measurements suggest none is yet sufficient.

### A. Degree quantization — *fails invariant 2*

```text
longitude → integer 0-359 → Kamea lookup
```

Deterministic, and reversibility is excellent (±0.5°). But the locality
measurement rules it out as written: adjacent degrees land in unrelated cells,
so *every* degree boundary is a discontinuity. Declaring 360 boundaries per
body is not declaring boundaries; it is conceding the invariant.

### B. Cell interpolation — *survives, at a cost*

```text
longitude → continuous grid coordinate → weighted neighbouring cells
```

The only candidate that can satisfy invariant 2, because it never quantizes.
It does so by abandoning the discrete path the existing machinery consumes, so
it needs new downstream machinery — or a discretization step that reintroduces
exactly the boundaries it was adopted to avoid.

### C. Modular mapping — *not a candidate*

Struck. This is `reduce_value`, described above: existing behaviour, not a
choice.

### D. Planet-native squares

```text
Mars longitude → Mars square (5×5) → Mars cell geometry
Saturn longitude → Saturn square (3×3) → Saturn cell geometry
```

Each classical planet already has its traditional square in
`atlas.kamea.squares`, and `CLASSICAL_KAMEA_BODIES` in `atlas.astronomy`
already records which bodies have one. This satisfies invariant 3 by
construction and is the strongest fit for invariant 5, since it follows the
historical association rather than imposing a universal square.

Open question it must answer: the squares differ in size (Saturn 3×3 through
Moon 9×9), so per-planet resolution differs by design. That is either a
feature — different bodies measured at their traditional granularity — or a
confound, and the specification must say which and why.

**Note:** the modern bodies in the temporal state (Uranus, Neptune, Pluto)
have no traditional square. The specification must decide whether they are
excluded, assigned squares by some stated rule, or handled as a separate
class. Silently omitting them would make the Kamea state cover only 7 of the
10 bodies R0 records.

---

## How the choice must NOT be made

**Do not select the mapping that performs best on earthquakes.**

That leaks outcome information into representation design, and every
subsequent result would be conditioned on a choice made by looking at the
answer. It is the temporal analogue of the null-model failure caught in the
variant pilot, and it would be harder to detect because there would be no
mismatched control to notice.

Selection criteria, in order:

1. mathematical coherence
2. historical/symbolic consistency
3. continuity behaviour
4. reversibility
5. computational properties

Then freeze the mapping, record its version in the temporal schema hash, and
only then test events.

---

## What R0 already tells us about the likely answer

The raw-state audit found **140 nominal dimensions carrying ~6 effective
ones** (participation ratio 6.11; 10 components explain 90% of variance).

The astronomical state occupies a low-dimensional manifold. A deterministic
transform of it therefore **cannot add information** in the Shannon sense —
Kamea features are a function of the coordinates, so `I(raw; Kamea)` measures
retention, not contribution.

That reframes 1D's question. It is not "does Kamea add information" — it
cannot. It is:

> Does the Kamea transform reorganize those ~6 effective dimensions into a
> geometry that makes relationships more accessible to the analyses Atlas
> performs?

That is a representation-learning question, and it is answered by nested
model comparison, not information theory:

```text
Model A:  raw astronomy
Model B:  raw astronomy + Kamea features
```

If B does not beat A, the transform is a symbolic relabeling — which may still
be interpretively valuable, but carries no statistical claim.

---

## Resolution: trajectories, not instants

Both open questions dissolve together once the sequence stops being *the
bodies at one instant* and becomes *each body's own trajectory around that
instant*. For classical body `b` at instant `t`:

```text
S_b(t) = [ q_b(λ_b(t − mΔ_b)), …, q_b(λ_b(t)), …, q_b(λ_b(t + mΔ_b)) ]
```

```text
astronomical trajectory around t
        ↓  time-ordered longitude samples
        ↓  quantized integers
        ↓  that body's traditional Kamea
        ↓  existing reduction and path machinery
core geometry
```

**Time supplies the ordering**, so no convention has to be invented. Each body
is projected only onto its own square, so planet-locality holds by
construction — Mars never needs ordering relative to Venus. Implemented in
[temporal_kamea.py](src/atlas/validation/temporal_kamea.py).

### Invariant 2, replaced

Pointwise continuity is dropped as unobtainable. In its place:

> Nearby evaluation instants should produce similar reduced paths and core
> geometries, except at explicitly measured transition regions.

Measured at four levels, because reduction may *absorb* cell-level
discontinuity or may merely hide it, and which one it does is exactly what 1D
must find out:

```text
raw integer sequence     positional agreement before projection
projected path           positional agreement of coordinates
reduced occupancy        order-insensitive: same region visited
core geometry            dedup shape: same figure drawn
```

If coordinate agreement collapses while core geometry holds, the shape is the
stable object and the path is not.

### Ordering, resolved

Chronological. The three body-order candidates each had an avoidable defect —
Chaldean order carries no event-specific information, longitude order
double-encodes state and creates cross-body coupling that breaks invariant 3,
and `ORDERED_BODIES` is a serialization convention rather than a traversal.
`ORDERED_BODIES` may still serialize the seven independently computed body
summaries; it does not define the geometry.

### Settled by the same resolution

- **Centered window.** A trailing window imposes a causal reading that suits
  neither births nor historical events. A predictive study must define its own
  past-only representation rather than quietly reusing this one. Supported via
  `centered=False`, not the default.
- **Retrograde is not flagged.** A chronological trajectory already expresses
  reversal, stationarity, repeated cells and retracing. `TemporalKameaPath.reversals`
  reads it off the path. A separate feature would duplicate information unless
  1D shows the geometry loses it.
- **Scope is explicit.** R1 is seven independent planet-native temporal Kamea
  paths. R2 is complete R0 for all ten bodies **plus** R1 geometry for the
  classical seven. `build_trajectory` raises on Uranus/Neptune/Pluto rather
  than skipping them.

---

## The sampling experiment

Representation-only: no events, no outcomes, no cohort. Deliberately *not*
routed through `write_temporal_result` — that gate exists so an event result
cannot be published without control-quality evidence, and this study has no
controls because it has no events. Faking a control family to satisfy the gate
would weaken the gate.

```bash
.venv/Scripts/python.exe scripts/run_kamea_trajectory_sampling.py
```

48 reference instants drawn randomly across 1970–2025 (randomly, not on a
grid: a regular grid could beat against a body's period and flatter a family).
`half_width=6`, so 13 samples per path.

### Result: no family is acceptable

| | fixed-time (6 h) | body-relative (1°) | bin-relative (½ bin) |
|---|---|---|---|
| bodies failing | 6 / 7 | 4 / 7 | 2 / 7 |
| failure mode | degeneracy + collisions | degeneracy + collisions | collisions only |

Per body, projected-path stability and discrimination:

```text
                fixed-time              body-relative           bin-relative
body      window  1min  cells dist   window  cells dist    window  cells dist
saturn      3.0d  1.000  1.00 0.188  358.2d   1.52 0.667  7164.2d  6.88 0.854
jupiter     3.0d  1.000  1.02 0.333  144.4d   1.75 0.854  1624.6d  6.83 0.938
mars        3.0d  1.000  1.06 0.479   22.9d   1.90 0.938   164.9d  7.23 0.958
sun         3.0d  1.000  1.35 0.833   12.2d   2.21 1.000    60.9d  6.88 0.854
venus       3.0d  0.999  1.44 0.896    7.5d   2.31 0.979    27.5d  5.15 1.000
mercury     3.0d  1.000  1.62 0.979    2.9d   1.60 0.958     8.3d  2.79 1.000
moon        3.0d  0.999  9.90 0.979    0.9d   3.71 1.000     2.0d  7.02 1.000
```

`cells` = mean distinct cells visited; `dist` = fraction of the 48 instants
producing a distinct path.

### What the experiment establishes

**1. Path stability is satisfied, comfortably.** One-minute projected-path
similarity is ≥ 0.998 for every body in every family. The invariant that
replaced pointwise continuity is not merely falsifiable — it passes. Decision 1
was the right move.

**2. Discrimination is the binding constraint, and it was not in the invariant
list.** Every failure is degeneracy (the path never leaves its starting cell)
or collision (distinct instants producing identical paths). Neither of the five
original invariants would have caught this.

**3. The degeneracy is structural, not a tuning failure.** A body only leaves
its cell after crossing one bin, and the tradition pairs the slowest body with
the coarsest square:

| body | bin width | mean motion | time to cross one cell |
|---|---|---|---|
| moon | 4.44° | 13.176°/d | **0.34 d** |
| mercury | 5.62° | 4.092°/d | 1.37 d |
| venus | 7.35° | 1.602°/d | 4.59 d |
| sun | 10.00° | 0.986°/d | 10.15 d |
| mars | 14.40° | 0.524°/d | 27.48 d |
| jupiter | 22.50° | 0.083°/d | 270.76 d |
| saturn | 40.00° | 0.034°/d | **1194.03 d (3.27 yr)** |

Saturn's square is 3×3 *because* Saturn is slow, so its bins are widest exactly
where motion is slowest. The two effects compound rather than cancel. **No
window short enough to describe an instant gives Saturn a moving path**, and no
choice of sampling parameter changes that.

`bin_relative` was added *after* the two preregistered families failed — on the
diagnosis, not on any outcome, since no outcome data exists in this study. It
removes degeneracy everywhere (cells 2.79–7.23) and confirms the tension is
real by paying its full price: Saturn's window becomes 7,164 days. A 19.6-year
"instant" is not an instant.

---

## Decision: accept static slow bodies — 1C is frozen

The constraint is structural, so it is recorded as a property of the
representation rather than tuned away:

> **A temporally local, traditional, planet-native Kamea path cannot
> simultaneously provide high discrimination for slow bodies.** Rescuing both
> would require changing "local", "traditional", or "planet-native".

### Canonical R1

```text
event instant t
    ↓  shared interval [t − W, t + W]     ← same W for all seven bodies
    ↓  chronological samples
    ↓  planet-native quantization
    ↓  traditional Kamea paths
    ↓  reduction
core geometry
```

R1 represents local, chronologically ordered motion through traditional
planet-native Kamea cells. **At a fixed temporal scale, slow bodies may
produce stationary or highly degenerate paths. That is an explicit feature of
R1's temporal resolution, not an implementation failure.**

Preserved by this choice: contemporaneous meaning, one shared window,
traditional square sizes, the existing projection/reduction pipeline, and
independence from event outcomes.

`canonical_spec(scale)` builds it. A spec is canonical only if it uses the
fixed-time family, a named scale, and a centered window.

### Rejected as canonical, retained as contrasts

**R1b — body-relative windows.** Solves cell occupancy by changing what the
object *means*: a Moon path describing two days beside a Saturn path
describing twenty years is not an observation of the same temporal
neighbourhood. Legitimate as a characterization contrast; never the primary
event representation.

**R1c — refined quantizer.** The coarse quantization is not accidental.
Refining it so Saturn moves more often introduces a non-traditional square
resolution while keeping traditional labels. That needs its own symbolic and
mathematical justification, and it may not be adopted to repair an
unfavourable measurement.

### Degeneracy is reported, never hidden

A one-cell Saturn path is represented honestly as stationary rather than
dropped or expanded. `TemporalKameaPath.diagnostics()` reports, per body:

```text
distinct_cells          transition_count       occupancy_fraction
longest_stationary_run  reversal_count         path_distance
reduced_path_length     core_shape             stationary
```

### What R1 now claims

Not an equally discriminative encoding of every body at every scale. Rather:
*how much locally observable Kamea-cell traversal each classical body exhibits
around an instant at a fixed temporal resolution.* At that scale the Moon is
highly dynamic, Mercury and Venus usually move, Saturn and Jupiter are often
static — and **the variation across bodies is part of the representation.**
Physically coherent, statistically uneven.

### Multiscale, without adaptive windows

Four separately hashed representations, each with one interpretable temporal
scale and one window shared by all seven bodies:

```text
R1-W3D      R1-W30D      R1-W180D      R1-W1Y
```

Cleaner than per-body adaptive windows, because each keeps contemporaneity.
None may be selected using event results; 1D characterizes how discrimination,
stability and era dependence change with scale.

### R0 becomes essential, not a comparator

R1 discards within-cell phase by construction; R0 preserves it. So:

```text
R2 = complete R0 (ten bodies) + R1 path and core-geometry features (seven)
```

And the question 2B must ask is **not** whether R1 beats R0, but whether R1
adds structure *after conditioning on* R0. A standalone R1 result could merely
reflect coarse longitude bins or era occupancy.

---

## Deliverables

- [x] Measured locality constraints, pinned by test
- [x] Correction of the candidate set against those measurements
- [x] Invariant 2 replaced with path stability, measured at four levels
- [x] Ordering resolved: chronological, from each body's own trajectory
- [x] Centered window, retrograde-by-geometry, explicit R1/R2 scope
- [x] Reference implementation with determinism, quantization and stability
      tests — `tests/test_temporal_kamea.py`, `tests/test_kamea_locality.py`
- [x] Representation-only comparison of three sampling families
- [x] `TrajectorySpec.spec_hash()`, so a path names the representation that
      produced it
- [x] Slow-body degeneracy resolved: accepted and reported, not tuned away
- [x] Canonical family and four canonical scales frozen
- [x] `body_relative` / `bin_relative` demoted to diagnostic contrasts
- [x] Per-body degeneracy diagnostics required in the output
- [ ] `spec_hash` folded into the temporal schema hash
- [ ] R1-space control-quality diagnostics (before 2B)

**Status: closed.** The mathematical object exists, is implemented, is frozen,
and its principal limitation is characterized rather than hidden. No event or
birth outcome entered any part of the decision.

The central finding stands on its own:

> The traditional Kamea system imposes body-dependent temporal resolution.
> Stability is achievable; equal discrimination is not.

That is not a reason to redesign the representation. It is exactly the kind of
structural characteristic 1C existed to uncover.

Next: **Temporal 1D — Kamea information-loss and scale audit**, which measures
the consequences rather than searching for another sampling rule.
