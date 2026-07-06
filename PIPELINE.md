# PIPELINE.md

# Atlas Canonical Compilation Pipeline

**Version:** 2.0  
**Status:** Locked  
**Authority:** Canonical Architecture

---

# Purpose

This document defines the **only supported execution pipeline** for Atlas.

Every profile, every dashboard, every AI service, every research module, and every population analysis begins from the exact same deterministic pipeline.

There are no alternate compilation paths.

---

# Guiding Principle

> **Compile once. Consume everywhere.**

The compiler produces intelligence.

Everything else consumes it.

---

# High-Level Pipeline

```text
                profile.intake.json
                        │
                        ▼
         compile_canonical_profile()
                        │
        ┌───────────────┼────────────────┐
        │               │                │
        ▼               ▼                ▼
   Identity         Temporal         Lifecycle
        │               │
        ▼               ▼
     Natal         Ephemeris
        │               │
        └───────┬───────┘
                ▼
        Identity Graph
                │
                ▼
          Topology Engine
                │
                ▼
         Resonance Engine
                │
                ▼
       Structural Fingerprint
                │
                ▼
        Structural Classification
                │
                ▼
         profile.payload.json
                │
                ▼
     ┌───────────────────────────────┐
     │        Consumers              │
     ├───────────────────────────────┤
     │ Atlas AI                      │
     │ Dashboard                     │
     │ Relationship Engine           │
     │ Graph Explorer                │
     │ Population Intelligence       │
     │ Statistical Intelligence      │
     │ Research Engine               │
     │ Validation                    │
     └───────────────────────────────┘
```

---

# Stage 1 — Intake

## Input

```text
output/library/<profile_key>/profile.intake.json
```

The intake file contains only source facts.

Examples include:

- Name
- Birth date
- Birth time
- Birth location
- Optional metadata

The intake file **never** contains:

- topology
- resonance
- graph
- fingerprint
- classification

Those are derived.

---

# Stage 2 — Canonical Compiler

Entry Point

```python
compile_canonical_profile(profile_key)
```

Location

```text
src/atlas/compiler/canonical_profile_compiler.py
```

Responsibilities

- Validate intake
- Normalize identity
- Build temporal layer
- Generate natal chart
- Generate ephemeris
- Build identity graph
- Compute topology
- Compute resonance
- Compute fingerprint
- Produce classification
- Produce metrics
- Assemble canonical payload
- Write profile.payload.json

This is the only compiler permitted inside Atlas.

---

# Stage 3 — Identity Layer

Produces

```text
identity
```

Contains

- profile key
- display name
- canonical name
- identity metadata

Consumers

Every downstream layer.

---

# Stage 4 — Temporal Layer

Produces

```text
temporal
```

Contains

- birth metadata
- natal chart
- ephemeris
- temporal summary
- runtime status

Consumers

- classification
- temporal intelligence
- dashboard
- AI
- research

---

# Stage 5 — Graph Layer

Produces

```text
graph
```

Contains

- identity graph
- canonical graph
- structural graph
- graph metrics
- graph summary

Consumers

- topology
- resonance
- fingerprint

---

# Stage 6 — Topology Layer

Consumes

```text
graph
```

Produces

```text
topology
```

Contains

- topology class
- dominant axis
- flow pattern
- persistence
- organization pattern
- topology vector
- motif summary

Consumers

- population intelligence
- classification
- graph explorer
- research

---

# Stage 7 — Resonance Layer

Consumes

```text
topology
```

Produces

```text
resonance
```

Contains

- resonance class
- dominant axis
- propagation
- activation
- damping
- resonance vector

Consumers

- AI
- dashboard
- comparison
- population intelligence

---

# Stage 8 — Fingerprint Layer

Consumes

- graph
- topology
- resonance

Produces

```text
fingerprint
```

Contains

- graph statistics
- deterministic signature
- uniqueness metrics
- comparison metrics

Consumers

- similarity search
- clustering
- nearest neighbors
- validation

---

# Stage 9 — Classification

Consumes

- identity
- temporal
- topology
- resonance
- fingerprint

Produces

```text
classification
```

Contains

- structural role
- civilization function
- confidence
- supporting basis

Classification **never** recompiles intelligence.

It only interprets compiled layers.

---

# Stage 10 — Metrics

Produces

```text
metrics
```

Example

```json
{
    "has_identity": true,
    "has_birth_date": true,
    "has_birth_time": true,
    "has_birth_location": true,
    "has_temporal": true,
    "has_natal": true,
    "has_ephemeris": true,
    "has_graph": true,
    "has_topology": true,
    "has_resonance": true,
    "has_fingerprint": true,
    "has_classification": true
}
```

Purpose

Metrics provide deterministic health checking across the entire platform.

---

# Stage 11 — Canonical Payload

Produces

```text
profile.payload.json
```

Example structure

```text
identity
birth
lifecycle
temporal
graph
topology
resonance
fingerprint
classification
metrics
summary
```

This payload is immutable.

Every downstream service consumes this payload.

---

# Consumer Architecture

## Atlas AI

Consumes

```text
profile.payload.json
```

Produces

- executive summaries
- reasoning
- narratives
- evidence synthesis
- recommendations

---

## Dashboard

Consumes

```text
profile.payload.json
```

Responsibilities

Display intelligence.

Never calculate intelligence.

---

## Relationship Engine

Consumes

Two canonical payloads.

Produces

Relationship synthesis.

---

## Population Intelligence

Consumes

Thousands of canonical payloads.

Produces

- clustering
- similarity
- topology distributions
- resonance distributions
- civilization statistics

---

## Statistical Intelligence

Consumes

Population datasets.

Produces

Research statistics.

---

## Research Engine

Consumes

Canonical payloads.

Produces

- hypotheses
- falsification
- experiment plans
- validation studies

Research is strictly read-only.

---

# Failure Handling

Every pipeline stage must return a valid object.

Correct

```json
{
    "status": "missing",
    "reason": "Graph unavailable.",
    "warnings": [],
    "errors": []
}
```

Incorrect

```json
null
```

No layer may silently fail.

---

# Extension Procedure

Every future intelligence layer must follow this process.

1. Add layer to canonical compiler.

2. Add layer to profile payload.

3. Add metrics.

4. Document schema.

5. Render in dashboard.

6. Add population support.

7. Add research support.

No exceptions.

---

# Deprecated Architecture

The following are legacy compatibility mechanisms only.

- profile.acf.json
- Legacy graph builders
- Fallback payload generators
- Compatibility adapters

These exist solely to support older tooling.

They are **not** authoritative.

---

# Architecture Rules

Allowed

```text
Compiler
        │
        ▼
Payload
        │
        ▼
Services
        │
        ▼
Dashboard
```

Not Allowed

```text
Dashboard
        │
        ▼
Compiler
```

Not Allowed

```text
Service
        │
        ▼
Rebuild Graph
```

Not Allowed

```text
Atlas AI
        │
        ▼
Generate Classification
```

Classification must already exist.

---

# Canonical Principle

Every future feature should answer one question before implementation:

> **Does this extend the canonical compiler, or does it consume the canonical payload?**

If the answer is **neither**, the feature does not belong in Atlas.

---

# Pipeline Contract

The Atlas pipeline is permanently defined as:

```text
profile.intake.json
        │
        ▼
compile_canonical_profile()
        │
        ▼
profile.payload.json
        │
        ▼
Atlas AI
Dashboard
Relationship Engine
Population Intelligence
Research
Validation
```

This pipeline is the architectural backbone of Atlas.

All future development must preserve this contract.