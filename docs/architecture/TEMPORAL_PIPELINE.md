# Atlas Temporal Pipeline

## Overview

Atlas Temporal Intelligence is a deterministic compiler pipeline responsible for enriching the Canonical Structural Signature (CSS).

Temporal Intelligence is **not** an independent subsystem. Every temporal computation is performed through the Compiler Engine and becomes part of the canonical structural representation.

```text
Profile
    ↓
Compiler Engine
    ↓
Temporal Pass
    ↓
Canonical Structural Signature (CSS)
```

---

# Purpose

The purpose of the Temporal domain is to transform birth and timing information into deterministic structural data that can be consumed by every other Atlas subsystem.

Temporal Intelligence should never perform interpretation.

Its sole responsibility is to compute reproducible structural measurements.

---

# Design Principles

Temporal Intelligence must always remain:

- Deterministic
- Reproducible
- Testable
- Compiler-driven
- Stateless
- Modular
- Gracefully degrading
- Independent of LLM reasoning

Every temporal stage should enrich CSS rather than creating a parallel representation.

---

# Current Pipeline

```text
Birth Seed
    ↓
Swiss Ephemeris
    ↓
Sidereal Conversion
    ↓
Nakshatra Analysis
    ↓
CSS
```

Current implementation order inside the compiler:

```text
Profile Payload
        ↓
build_birth_seed()
        ↓
build_ephemeris()
        ↓
convert_ephemeris_to_sidereal()
        ↓
build_nakshatra_chart()
        ↓
css.temporal.natal.ephemeris
```

---

# Current CSS Structure

```text
css.temporal

├── natal
│   ├── birth
│   ├── planetary_matrix
│   └── ephemeris
│       ├── planets
│       ├── sidereal
│       └── nakshatra
│
├── transits
├── dasha
└── calibration
```

---

# Stage 1 — Birth Seed

### Source

- profile.intake.json
- Saved profile payload
- Compiler payload

### Responsibilities

Extract:

- Name
- Birth date
- Birth time
- Birth place
- Birth location
- Latitude
- Longitude
- Time zone
- Source metadata

### Rules

- Never throw because of missing birth data.
- Missing values should gracefully degrade.
- Preserve provenance information.

---

# Stage 2 — Swiss Ephemeris

### Module

```
src/atlas/temporal/ephemeris.py
```

### Responsibilities

- Convert birth information into Julian Day.
- Compute tropical planetary positions.
- Compute planetary speed.
- Detect retrograde motion.
- Produce deterministic planetary metadata.

### Produces

```text
EphemerisResult
```

Stored under:

```text
css.temporal.natal.ephemeris
```

### Status

```text
ephemeris_status

computed
failed
```

---

# Stage 3 — Sidereal Conversion

### Module

```
src/atlas/temporal/sidereal.py
```

### Responsibilities

Convert tropical planetary positions into sidereal positions using a deterministic ayanamsa.

### Produces

- Sidereal longitude
- Sidereal sign
- Degree in sign
- Ayanamsa
- Zodiac metadata

Stored under

```text
css.temporal.natal.ephemeris.sidereal
```

### Status

```text
sidereal_status

computed
failed
```

---

# Stage 4 — Nakshatra Analysis

### Module

```
src/atlas/temporal/nakshatra.py
```

### Responsibilities

Compute:

- Nakshatra
- Pada
- Nakshatra metadata
- Summary statistics

Stored under

```text
css.temporal.natal.ephemeris.nakshatra
```

### Status

```text
nakshatra_status

computed
failed
skipped
```

---

# Planned Pipeline

The remaining compiler stages should be integrated in dependency order.

```text
Birth Seed
        ↓
Swiss Ephemeris
        ↓
Sidereal Conversion
        ↓
Nakshatra Analysis
        ↓
House System
        ↓
Aspect Engine
        ↓
Planetary Dignity
        ↓
Varga Charts
        ↓
Navamsa
        ↓
Vimshottari Dasha
        ↓
Yoga Evaluation
        ↓
Transit Engine
        ↓
Calibration
        ↓
CSS
```

---

# Planned Modules

```text
src/atlas/temporal/houses.py
src/atlas/temporal/aspects.py
src/atlas/temporal/dignity.py
src/atlas/temporal/vargas.py
src/atlas/temporal/navamsa.py
src/atlas/temporal/vimshottari_dasha.py
src/atlas/temporal/yoga_engine.py
src/atlas/temporal/transits.py
```

---

# Integration Order

Future work should proceed in this order:

1. Houses
2. Aspects
3. Planetary Dignity
4. Vargas
5. Navamsa
6. Vimshottari Dasha
7. Yoga Engine
8. Transits
9. Calibration

Each stage should enrich existing CSS structures rather than introducing new top-level representations.

---

# Compiler Rules

Every Temporal stage must:

- Consume deterministic input.
- Produce deterministic output.
- Never mutate previous compiler passes.
- Never bypass the Compiler Engine.
- Never duplicate CSS structures.
- Preserve backwards compatibility.
- Expose explicit status fields.
- Gracefully degrade on failure.
- Be independently testable.
- Maintain reproducible outputs.

---

# Current Compiler Flow

```text
compile_profile()

        │
        ▼

Compiler Engine

        │
        ▼

IdentityPass

        │
        ▼

CipherPass

        │
        ▼

KameaPass

        │
        ▼

TemporalPass

        │
        ├── Birth Seed
        ├── Swiss Ephemeris
        ├── Sidereal
        └── Nakshatra

        ▼

Canonical Structural Signature
```

---

# Current Milestone

## Compiler Framework V2

Completed

- Compiler Engine
- Pass Registry
- Dependency Ordering
- Compiler Pass Classes
- Compilation Report
- Runtime CSS Loader
- CSS Exporter
- Compiler Metrics

Verified:

- 507 automated tests passing
- Stable compiler API
- Stable CSS runtime
- Stable pass registry

---

## Temporal Intelligence V2

Completed

- Birth Seed
- Swiss Ephemeris
- Sidereal Conversion
- Nakshatra Analysis

Current deterministic pipeline:

```text
Birth
    ↓
Ephemeris
    ↓
Sidereal
    ↓
Nakshatra
```

---

# Next Milestone

The next deterministic compiler enrichment will be:

```text
Birth
    ↓
Ephemeris
    ↓
Sidereal
    ↓
Nakshatra
    ↓
Houses
```

Once Houses are integrated, the pipeline will continue through:

```text
Aspects
↓
Dignity
↓
Vargas
↓
Navamsa
↓
Vimshottari Dasha
↓
Yoga Engine
↓
Transits
```

---

# Long-Term Vision

Atlas is a compiler-driven Structural Intelligence platform.

Temporal Intelligence is one deterministic compiler domain among several.

Future domains include:

- Identity Intelligence
- Cipher Intelligence
- Kamea Intelligence
- Temporal Intelligence
- Research Intelligence
- Validation Intelligence
- Population Intelligence
- Topology Intelligence
- Forecasting

Each domain contributes to a single canonical representation:

```text
Canonical Structural Signature (CSS)
```

Every future capability should answer one architectural question:

> **"How does this enrich the Canonical Structural Signature?"**

No subsystem should create an alternative representation when it can instead become another deterministic compiler pass.