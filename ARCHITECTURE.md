# ARCHITECTURE.md

# Atlas System Architecture
Version 2.0

---

# Mission

Atlas is a deterministic structural intelligence platform.

Its purpose is to transform raw identity information into a complete,
reproducible structural representation that can be interpreted,
compared, researched, and visualized.

Atlas is designed as an operating system for structural intelligence,
not as a collection of independent services.

---

# Architectural Principles

Atlas follows five foundational principles.

## 1. Single Source of Truth

There is exactly one compilation pipeline.

```

profile.intake.json

↓

compile_canonical_profile()

↓

profile.payload.json

```

No service may rebuild intelligence that already exists.

---

## 2. Deterministic Before Interpretive

Every interpretation must originate from deterministic outputs.

The compiler produces facts.

The AI explains facts.

Never the opposite.

---

## 3. Immutable Intelligence

Compiled structural intelligence is treated as immutable.

Services consume compiled intelligence.

They do not regenerate it.

---

## 4. Layered Architecture

Each intelligence layer has exactly one responsibility.

```

Identity

↓

Temporal

↓

Graph

↓

Topology

↓

Resonance

↓

Fingerprint

↓

Classification

↓

Interpretation

```

No layer skips another.

---

## 5. Separation of Concerns

Atlas separates:

Compilation

Interpretation

Visualization

Research

Validation

Population Analysis

These remain independent.

---

# System Overview

```

profile.intake.json

↓

Canonical Compiler

↓

profile.payload.json

↓

+---------------------------+
| Atlas AI |
| Dashboard |
| Population Intelligence |
| Relationship Engine |
| Research |
| Validation |
+---------------------------+

```

Everything depends on the canonical payload.

Nothing depends on ACF.

---

# Major Components

## Intake

Purpose

Collect identity information.

Inputs

Name

Birth date

Birth time

Birth location

Optional metadata

Output

profile.intake.json

---

## Canonical Compiler

Primary entry point

```python
compile_canonical_profile()
```

Responsibilities

Validate intake

Build identity

Compile temporal intelligence

Compile natal chart

Compile ephemeris

Build graph

Generate topology

Generate resonance

Generate fingerprint

Produce classification

Assemble metrics

Write profile.payload.json

This compiler is the only supported compilation path.

---

## Identity Layer

Produces

Identity

Names

Canonical keys

Display information

Consumers

All downstream layers.

---

## Temporal Layer

Produces

Birth metadata

Natal chart

Ephemeris

Transit support

Consumers

Classification

Behavior

Temporal Intelligence

Population studies

---

## Graph Layer

Produces

Canonical identity graph

Structural graph

Graph metrics

Consumers

Topology

Fingerprint

Research

---

## Topology Layer

Produces

Topology class

Dominant axis

Flow pattern

Organization pattern

Persistence

Consumers

Classification

Population clustering

Similarity search

---

## Resonance Layer

Produces

Activation

Propagation

Damping

Channeling

Consumers

Behavior

Prediction

Population Intelligence

---

## Fingerprint Layer

Produces

Deterministic structural fingerprint.

Consumers

Population matching

Similarity

Uniqueness

Research

---

## Classification Layer

Consumes

Identity

Temporal

Topology

Resonance

Fingerprint

Produces

Structural role

Civilization function

Confidence

Interpretation inputs

---

## Atlas AI

Purpose

Executive synthesis.

Consumes

Compiled profile payload.

Produces

Narrative

Evidence

Reports

Research guidance

Atlas AI never performs structural compilation.

---

## Dashboard

Purpose

Visualization.

Consumes

Canonical payload.

Never computes intelligence.

---

## Population Intelligence

Purpose

Cross-profile analysis.

Examples

Similarity

Clusters

Distance

Distribution

Archetypes

Population Intelligence never mutates profiles.

---

## Research

Purpose

Evidence-driven experimentation.

Research layers are read-only.

---

## Validation

Purpose

Evaluate deterministic correctness.

Validation never changes compiled data.

---

# Data Flow

```

profile.intake.json

↓

compile_canonical_profile()

↓

profile.payload.json

↓

Atlas AI

↓

Dashboard

↓

Population Intelligence

↓

Research

```

No alternate compilation path exists.

---

# Canonical Payload

Every compiled profile contains:

Identity

Temporal

Graph

Topology

Resonance

Fingerprint

Classification

Metrics

Optional exports

These sections are documented separately.

---

# Legacy Components

Legacy compatibility exists only where required.

Examples

ACF export

Legacy adapters

Migration helpers

These exist to support older tooling.

They are not authoritative.

---

# Dependency Direction

Allowed

```

Compiler

↓

Services

↓

Atlas AI

↓

Dashboard

```

Not allowed

```

Dashboard

↓

Compiler

```

Not allowed

```

Service A

↓

Rebuild Graph

```

---

# Service Philosophy

Every service follows the same pattern.

Input

Canonical payload

↓

Analysis

↓

Return

No service regenerates intelligence.

---

# Dashboard Philosophy

The dashboard renders.

It does not calculate.

It does not classify.

It does not compile.

---

# Population Philosophy

Population Intelligence compares compiled profiles.

It never compiles them.

---

# Future Expansion

New layers should integrate into the compiler.

Example

```

Compiler

↓

Behavior Layer

↓

Decision Layer

↓

Forecast Layer

```

Every new layer becomes part of the canonical payload.

---

# Summary

Atlas is built around one architectural rule:

**Compile once. Consume everywhere.**

Every subsystem exists to uphold that rule.
