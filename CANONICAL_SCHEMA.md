# CANONICAL_SCHEMA.md

# Atlas Canonical Profile Schema

**Version:** 2.0  
**Status:** Locked  
**Authority:** Canonical Compiler  
**Canonical Artifact:** `profile.payload.json`

---

# Purpose

This document defines the official schema for the Atlas canonical profile payload.

Every service, dashboard page, research module, relationship engine, population analysis tool, and future API must treat this schema as the authoritative profile contract.

The canonical payload is produced by:

```python
compile_canonical_profile(profile_key)
```

and written to:

```text
output/library/<profile_key>/profile.payload.json
```

---

# Schema Principle

Atlas follows one schema rule:

> **Every deterministic layer must exist in the canonical payload, even when incomplete.**

A missing layer should never be represented as `null`.

Correct:

```json
{
  "status": "missing",
  "reason": "Graph layer unavailable.",
  "warnings": [],
  "errors": []
}
```

Incorrect:

```json
null
```

No silent failure.  
No missing top-level keys.  
No dashboard guessing.

---

# Top-Level Schema

```text
profile.payload.json
│
├── success
├── version
├── profile_key
├── profile_dir
├── payload_path
│
├── identity
├── birth
├── death
├── lifecycle
│
├── cipher
├── kamea
│
├── temporal
│   ├── birth
│   ├── natal
│   ├── ephemeris
│   ├── sidereal
│   ├── summary
│   ├── warnings
│   └── errors
│
├── graph
│   ├── status
│   ├── identity_stack
│   ├── summary
│   ├── cig
│   ├── stg
│   ├── motifs
│   └── genome
│
├── topology
├── resonance
├── fingerprint
├── classification
├── narrative
├── evidence
├── metrics
└── diagnostics
```

---

# Required Top-Level Fields

Every canonical payload must include these fields:

```json
{
  "success": true,
  "version": "1.0",
  "profile_key": "example_profile",
  "profile_dir": "output/library/example_profile",
  "payload_path": "output/library/example_profile/profile.payload.json",
  "identity": {},
  "birth": {},
  "death": {},
  "lifecycle": {},
  "cipher": {},
  "kamea": {},
  "temporal": {},
  "graph": {},
  "topology": {},
  "resonance": {},
  "fingerprint": {},
  "classification": {},
  "narrative": {},
  "evidence": [],
  "metrics": {},
  "diagnostics": {}
}
```

---

# `success`

## Purpose

Indicates whether the canonical compiler completed enough work to produce a valid payload.

## Type

```json
true
```

## Notes

A payload may be successful even if some optional layers are marked as missing.

---

# `version`

## Purpose

Identifies the canonical payload schema version.

## Type

```json
"1.0"
```

## Producer

`canonical_profile_compiler`

## Consumers

All services.

---

# `profile_key`

## Purpose

Stable machine-readable profile identifier.

## Example

```json
"profile_key": "michael_elvis_brockway"
```

## Rules

- Lowercase
- Underscore separated
- Stable across runs
- Used as the directory key

---

# `profile_dir`

## Purpose

Filesystem location of the compiled profile.

## Example

```json
"profile_dir": "output/library/michael_elvis_brockway"
```

---

# `payload_path`

## Purpose

Filesystem path to the canonical artifact.

## Example

```json
"payload_path": "output/library/michael_elvis_brockway/profile.payload.json"
```

---

# `identity`

## Purpose

Canonical identity block.

## Produced By

Canonical compiler identity stage.

## Consumed By

- Graph layer
- Classification
- Atlas AI
- Dashboard
- Relationship Engine
- Population Intelligence
- Research Engine

## Schema

```json
"identity": {
  "profile_key": "michael_elvis_brockway",
  "name": "Michael Elvis Brockway",
  "display_name": "Michael Elvis Brockway",
  "full_name": "Michael Elvis Brockway"
}
```

## Required Fields

```text
profile_key
name
display_name
full_name
```

## Notes

`name` is the canonical display label used by downstream systems.

---

# `birth`

## Purpose

Canonical birth metadata.

## Produced By

Canonical compiler birth stage.

## Consumed By

- Temporal layer
- Natal compiler
- Ephemeris compiler
- Classification
- Dashboard
- Research Engine

## Schema

```json
"birth": {
  "date": "1993-08-16",
  "time": "17:30",
  "place": "Janesville, Wisconsin",
  "date_status": "provided",
  "time_status": "provided",
  "place_status": "provided"
}
```

## Required Fields

```text
date
time
place
date_status
time_status
place_status
```

## Date Format

Preferred:

```text
YYYY-MM-DD
```

## Time Format

Preferred:

```text
HH:MM
```

24-hour time is preferred internally.

---

# `death`

## Purpose

Lifecycle closure metadata.

## Schema

```json
"death": {
  "date": "",
  "place": "",
  "date_status": "open_or_missing",
  "place_status": "missing",
  "lifecycle_status": "open_lifecycle"
}
```

## Notes

Living profiles should keep death fields empty and lifecycle status open.

---

# `lifecycle`

## Purpose

Stores lifecycle-level metadata and major events.

## Schema

```json
"lifecycle": {
  "status": "compiled",
  "major_events": [],
  "notes": "Developer of Atlas"
}
```

## Consumed By

- Dashboard
- Narrative
- Research
- Relationship Engine

---

# `cipher`

## Purpose

Reserved for cipher-derived layers.

## Current Status

May be missing until cipher compiler is fully wired into the canonical compiler.

## Missing Contract

```json
"cipher": {
  "status": "missing",
  "layer": "cipher",
  "reason": "Cipher compiler not wired into canonical compiler yet.",
  "required_inputs": [],
  "warnings": [],
  "errors": []
}
```

---

# `kamea`

## Purpose

Reserved for Kamea-derived structural layers.

## Current Status

May be missing until Kamea compiler is fully wired into the canonical compiler.

## Missing Contract

```json
"kamea": {
  "status": "missing",
  "layer": "kamea",
  "reason": "Kamea compiler not wired into canonical compiler yet.",
  "required_inputs": [],
  "warnings": [],
  "errors": []
}
```

---

# `temporal`

## Purpose

Canonical temporal intelligence layer.

## Produced By

Canonical compiler temporal stage.

## Consumed By

- Temporal Intelligence
- Classification
- Vedic behavior service
- Atlas AI
- Profile Dossier
- Population Intelligence
- Research Engine

## Schema

```json
"temporal": {
  "status": "compiled",
  "birth": {},
  "natal": {
    "ephemeris": {},
    "sidereal": {}
  },
  "summary": {
    "planet_count": 9,
    "time_known": true,
    "ephemeris_path": "data/ephemeris"
  },
  "warnings": [],
  "errors": []
}
```

## Required Fields

```text
status
birth
natal
summary
warnings
errors
```

## Status Values

```text
compiled
missing
error
```

---

# `temporal.natal`

## Purpose

Stores natal-derived temporal outputs.

## Schema

```json
"natal": {
  "ephemeris": {},
  "sidereal": {}
}
```

## Required Fields

```text
ephemeris
sidereal
```

---

# `temporal.natal.ephemeris`

## Purpose

Stores planetary ephemeris calculations.

## Required For

- temporal intelligence
- Vedic behavior
- timing interpretation
- dasha support
- transit support

## Failure Contract

```json
"temporal": {
  "status": "missing",
  "reason": "Temporal compilation failed: Birth date is required.",
  "required_inputs": ["birth.date", "birth.time", "birth.place"],
  "warnings": [],
  "errors": ["Birth date is required."]
}
```

---

# `graph`

## Purpose

Canonical graph intelligence layer.

## Produced By

Canonical compiler graph stage.

## Consumed By

- Topology
- Resonance
- Fingerprint
- Graph Explorer
- Population Intelligence
- Research Engine
- Atlas AI

## Schema

```json
"graph": {
  "status": "compiled",
  "identity_stack": {},
  "summary": {},
  "cig": {},
  "stg": {},
  "motifs": {},
  "genome": {}
}
```

## Required Fields

```text
status
identity_stack
summary
cig
stg
motifs
genome
```

## Status Values

```text
compiled
missing
error
```

---

# `graph.identity_stack`

## Purpose

Complete compiled graph stack.

## Notes

This may include canonical identity graph, structural truth graph, motifs, topology support, resonance support, and genome information.

---

# `graph.cig`

## Purpose

Canonical Identity Graph.

## Consumers

- Graph Explorer
- Fingerprint
- Research
- Population Intelligence

---

# `graph.stg`

## Purpose

Structural Truth Graph.

## Consumers

- Fingerprint
- Research
- Validation
- Population Intelligence

---

# `graph.motifs`

## Purpose

Stores graph motif data.

## Consumers

- Topology
- Classification
- Population Intelligence

---

# `graph.genome`

## Purpose

Stores compact graph-derived structural genome.

## Consumers

- Topology
- Resonance
- Fingerprint

---

# `topology`

## Purpose

Canonical topology intelligence layer.

Topology describes how the profile organizes structurally.

## Produced By

Canonical compiler topology stage.

## Consumed By

- Classification
- Profile Dossier
- Population Intelligence
- Graph Explorer
- Research Engine
- Similarity Search

## Schema

```json
"topology": {
  "status": "compiled",
  "summary": {
    "version": "1.0",
    "definition": "Graph-native topology behavior profile derived from the Structural Genome.",
    "source": "StructuralGenome",
    "topology_class": "distributed_sparse",
    "dominant_axis": "hierarchy",
    "flow_pattern": "diffuse",
    "organization_pattern": "distributed",
    "stability_pattern": "low_persistence",
    "topology_vector": {
      "hierarchy": 0.0,
      "branching": 0.0,
      "cyclicity": 0.0,
      "bottleneck": 0.0,
      "persistence": 0.0,
      "motif_richness": 0.0
    }
  },
  "topology_class": "distributed_sparse",
  "dominant_topology_axis": "hierarchy",
  "dominant_motif": null,
  "motif_count": 0.0
}
```

## Required Fields

```text
status
summary
topology_class
dominant_topology_axis
dominant_motif
motif_count
```

## Status Values

```text
compiled
missing
error
```

---

# `topology.topology_class`

## Purpose

Primary topology classification.

## Example Values

```text
distributed_sparse
branching_tree
hub_dominant
cyclic
bottlenecked
persistent
```

---

# `topology.dominant_topology_axis`

## Purpose

Most prominent topology dimension.

## Example Values

```text
hierarchy
branching
cyclicity
bottleneck
persistence
motif_richness
```

---

# `resonance`

## Purpose

Canonical resonance behavior layer.

Resonance describes how activation moves through the profile's structure.

## Produced By

Canonical compiler resonance stage.

## Consumed By

- Atlas AI
- Profile Dossier
- Population Intelligence
- Comparison Engine
- Research Engine

## Schema

```json
"resonance": {
  "status": "compiled",
  "summary": {
    "version": "1.0",
    "definition": "Deterministic resonance behavior profile derived from IdentityTopology.",
    "source": "IdentityTopology",
    "topology_version": "1.0",
    "resonance_class": "low_resonance",
    "dominant_resonance_axis": "activation",
    "activation_pattern": "low_activation",
    "propagation_pattern": "diffuse_flow",
    "damping_pattern": "strongly_damped",
    "resonance_vector": {
      "activation": 0.0,
      "propagation": 0.0,
      "stability": 0.0,
      "recirculation": 0.0,
      "channeling": 0.0,
      "branching": 0.0
    }
  },
  "resonance_class": "low_resonance",
  "dominant_resonance_axis": "activation"
}
```

## Required Fields

```text
status
summary
resonance_class
dominant_resonance_axis
```

---

# `resonance.resonance_class`

## Purpose

Primary resonance classification.

## Example Values

```text
low_resonance
high_resonance
stable_resonance
diffuse_resonance
channeled_resonance
strongly_damped
```

---

# `fingerprint`

## Purpose

Compact structural signature of the profile.

## Produced By

Canonical compiler fingerprint stage.

## Consumed By

- Population Intelligence
- Similarity Search
- Comparison Engine
- Validation
- Research Engine

## Schema

```json
"fingerprint": {
  "status": "compiled",
  "summary": {
    "cig_nodes": 3,
    "cig_edges": 2,
    "stg_nodes": 0,
    "stg_edges": 0,
    "dominant_motif": null,
    "topology_class": "distributed_sparse",
    "resonance_class": "low_resonance"
  }
}
```

## Required Fields

```text
status
summary
```

---

# `classification`

## Purpose

Interprets compiled deterministic layers into a structural role.

## Produced By

Canonical compiler classification stage.

## Consumed By

- Atlas AI
- Profile Dossier
- Relationship Engine
- Population Intelligence
- Research Engine

## Schema

```json
"classification": {
  "structural_role": "Temporal-Interpreter",
  "civilization_function": "Timing Interpreter: reads structure through activation, sequence, and change over time.",
  "confidence": {
    "score": 0.75,
    "percent": 75.0,
    "label": "moderate"
  },
  "basis": {
    "dominant_motif": null,
    "topology_class": "distributed_sparse",
    "dominant_topology_axis": "hierarchy",
    "has_ephemeris": true
  }
}
```

## Required Fields

```text
structural_role
civilization_function
confidence
basis
```

---

# `classification.structural_role`

## Purpose

The primary role assigned to the profile.

## Example Values

```text
Temporal-Interpreter
Driver-Amplifier
Knowledge Pioneer
Integrator
Unclassified Structural Actor
```

---

# `classification.confidence`

## Purpose

Confidence record for classification.

## Schema

```json
"confidence": {
  "score": 0.75,
  "percent": 75.0,
  "label": "moderate"
}
```

---

# `narrative`

## Purpose

Reserved canonical narrative layer.

## Current Status

May be generated by Atlas AI services instead of the canonical compiler.

## Missing Contract

```json
"narrative": {
  "status": "missing",
  "layer": "narrative",
  "reason": "Narrative compiler not wired into canonical compiler yet.",
  "required_inputs": [],
  "warnings": [],
  "errors": []
}
```

---

# `evidence`

## Purpose

List of evidence records supporting interpretation.

## Schema

```json
"evidence": []
```

## Future Schema

```json
[
  {
    "claim": "Graph layer is available.",
    "source": "canonical_profile_compiler",
    "confidence": {
      "score": 1.0,
      "percent": 100,
      "label": "high"
    }
  }
]
```

---

# `metrics`

## Purpose

Fast health and completeness checks for the profile.

## Produced By

Canonical compiler metrics stage.

## Consumed By

- Atlas AI
- Dashboard
- Validation
- Population Intelligence
- Research Engine

## Schema

```json
"metrics": {
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

## Required Fields

```text
has_identity
has_birth_date
has_birth_time
has_birth_location
has_temporal
has_natal
has_ephemeris
has_graph
has_topology
has_resonance
has_fingerprint
has_classification
```

---

# `diagnostics`

## Purpose

Compiler diagnostics.

## Schema

```json
"diagnostics": {
  "warnings": [],
  "errors": [],
  "created_at": "2026-07-04T00:00:00+00:00",
  "compiler": "canonical_profile_compiler"
}
```

## Consumers

- Developer Console
- Validation
- Debugging
- CI checks

---

# Missing Layer Contract

Every optional or unavailable layer must use the missing layer contract.

```json
{
  "status": "missing",
  "layer": "layer_name",
  "reason": "Human-readable explanation.",
  "required_inputs": [],
  "warnings": [],
  "errors": []
}
```

---

# Error Layer Contract

If a layer fails unexpectedly:

```json
{
  "status": "error",
  "layer": "layer_name",
  "reason": "Unexpected compiler error.",
  "required_inputs": [],
  "warnings": [],
  "errors": ["Trace-safe error message."]
}
```

---

# Service Rules

Services must:

- Load or receive the canonical payload.
- Read from documented fields only.
- Return stable service payloads.
- Never rebuild canonical layers.
- Never mutate `profile.payload.json`.

Services must not:

- Read ACF directly.
- Compile topology.
- Compile resonance.
- Generate fingerprints.
- Infer missing canonical fields.
- Create alternate schema shapes.

---

# Dashboard Rules

Dashboard pages must:

- Render canonical payload data.
- Hide missing layers gracefully.
- Surface diagnostics clearly.
- Avoid computing intelligence.

Dashboard pages must not:

- Classify profiles.
- Build graphs.
- Compute topology.
- Run ephemeris calculations.
- Patch payloads.

---

# Research Rules

Research modules must:

- Treat payloads as read-only.
- Record derived findings separately.
- Cite source profile keys.
- Preserve reproducibility.

Research modules must not mutate canonical profile payloads.

---

# Population Rules

Population systems must consume many canonical payloads.

They may compute aggregate outputs such as:

- clusters
- nearest neighbors
- distributions
- histograms
- similarity matrices
- outlier detection

Population systems must not rewrite individual profile payloads.

---

# Compatibility Notes

Legacy artifacts may still exist:

```text
profile.acf.json
identity_stack.json
profile_summary.json
profile_interpretation.json
codex_report.md
```

These are not canonical.

The canonical artifact is:

```text
profile.payload.json
```

---

# Schema Extension Rules

To add a new top-level field:

1. Add it to `compile_canonical_profile()`.
2. Add a metrics flag if appropriate.
3. Document it in this file.
4. Update dashboard rendering.
5. Update service consumers.
6. Add tests.

No undocumented top-level schema additions.

---

# Canonical Contract

The canonical profile schema is the platform contract.

Every component must either:

1. Produce part of this schema inside the compiler, or
2. Consume this schema outside the compiler.

There is no third path.