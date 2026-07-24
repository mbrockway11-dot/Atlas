# Temporal 1C — Planetary→Kamea Specification

**Status:** open · **Type:** design milestone, not validation · **Blocks:**
Temporal 1D · **Does not block:** Temporal 2 (earthquakes on R0)

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

## Candidate mappings

Recorded with their known trade-offs. **Not yet chosen.**

### A. Degree quantization

```text
longitude → integer 0-359 → Kamea lookup
```

Simple and obviously deterministic. Brutally discontinuous: adjacent degrees
land in unrelated cells, so invariant 2 fails unless every degree boundary is
declared. Reversibility is excellent (±0.5°).

### B. Cell interpolation

```text
longitude → continuous grid coordinate → weighted neighbouring cells
```

Smooth, so invariant 2 holds naturally. Reversibility good. Cost: the result
is no longer a *path* through discrete cells, which is what the existing Kamea
machinery consumes — so it either needs new downstream machinery or a
documented discretization step that reintroduces boundaries.

### C. Modular mapping

```text
longitude → mod N → magic-square index
```

Mathematically elegant. Likely destroys locality: longitudes 10° apart may map
to adjacent cells while longitudes 1° apart map to opposite corners. That
fails invariant 2 badly and makes invariant 4 nearly useless.

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

## Deliverables

- [ ] A written specification naming one mapping and justifying it against
      all five invariants
- [ ] A decision on the modern bodies (Uranus/Neptune/Pluto)
- [ ] A decision on differing per-planet square sizes
- [ ] Declared boundary locations, if the mapping is discontinuous
- [ ] A versioned `KAMEA_MAPPING_VERSION` participating in the temporal
      schema hash
- [ ] Reference implementation with determinism and reversibility tests

Only then does Temporal 1D (the representation audit) become runnable.
