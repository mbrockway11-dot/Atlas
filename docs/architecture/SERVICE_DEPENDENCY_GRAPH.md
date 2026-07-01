# Atlas Service Dependency Graph

**Project:** Atlas  
**Architecture Version:** Phase II  
**Document:** Service Dependency Graph  
**Status:** Active Development

---

# Purpose

This document defines the dependency relationships between every major Atlas service.

Its purpose is to ensure that:

- service execution is deterministic
- dependency direction is explicit
- circular dependencies are prohibited
- every service has a single responsibility
- future services integrate consistently

This document is considered the authoritative dependency contract for Atlas.

---

# Design Principle

Atlas follows a layered architecture.

Services may depend only on services beneath them.

Higher layers orchestrate lower layers.

Lower layers never depend upon higher layers.

```text
Higher Layers
      │
      ▼
Lower Layers
```

No service may introduce a circular dependency.

---

# Complete Cognitive Stack

```text
Research Corpus
        │
        ▼
Canonical Structural Model
        │
        ▼
AtlasProfile
        │
        ▼
Core Intelligence Services
        │
        ▼
Atlas AI
        │
        ▼
Query Planner
        │
        ▼
Reasoning Engine
        │
        ▼
Hypothesis Engine
        │
        ▼
Falsification Engine
        │
        ▼
Experiment Planner
        │
        ▼
Discovery Engine
        │
        ▼
Research Memory
```

Each stage consumes the output of the previous stage.

No stage skips intermediate layers.

---

# Layer 0 — Research Corpus

Responsibilities

- Research sessions
- Profile intake
- Corpus artifacts
- Validation data
- Canonical evidence

Outputs

- Research assets
- Identity metadata
- Birth metadata
- Supporting evidence

Consumers

- Canonical Structural Model

---

# Layer 1 — Canonical Structural Model

Responsibilities

- Identity encoding
- Cipher transformations
- Kamea projection
- Graph construction
- Topology generation
- Morphology generation
- Resonance generation

Outputs

- Canonical graph
- Canonical topology
- Canonical morphology
- Canonical metrics

Consumers

- AtlasProfile

---

# Layer 2 — AtlasProfile

AtlasProfile is the canonical representation of every profile.

Responsibilities

- unify canonical structure
- expose shared interfaces
- provide immutable profile state
- serve as input for intelligence services

Consumers

- Graph Intelligence
- Temporal Intelligence
- Population Intelligence
- Narrative
- Evidence
- Profile Report

---

# Layer 3 — Core Intelligence Services

Core Intelligence services perform domain-specific analysis.

Current services include:

```text
Profile Report

Narrative

Evidence

Graph Intelligence

Temporal Intelligence

Population Intelligence

Vedic Behavior
```

Outputs

- observations
- metrics
- warnings
- confidence
- recommendations

Consumers

- Atlas AI

---

# Layer 4 — Atlas AI

Atlas AI is the orchestration layer.

Responsibilities

- execute requested services
- aggregate outputs
- aggregate warnings
- aggregate confidence
- normalize service responses

Inputs

- Profile Report
- Narrative
- Evidence
- Graph Intelligence
- Temporal Intelligence
- Population Intelligence
- Vedic Behavior

Outputs

Unified Atlas AI Payload

Consumers

- Query Planner
- Reasoning Engine

---

# Layer 5 — Query Planner

Responsibilities

- classify intent
- determine scope
- identify profiles
- determine required services
- build execution plan

Outputs

Execution Plan

Consumers

- Reasoning Engine

---

# Layer 6 — Reasoning Engine

Responsibilities

- interpret Atlas AI results
- synthesize evidence
- summarize observations
- identify limitations
- generate recommendations

Outputs

Reasoning Model

Consumers

- Hypothesis Engine

---

# Layer 7 — Hypothesis Engine

Responsibilities

- generate competing explanations
- compare evidence
- score hypotheses
- identify strongest explanation

Outputs

Hypothesis Model

Consumers

- Falsification Engine

---

# Layer 8 — Falsification Engine

Responsibilities

- search for contradictions
- identify disconfirming evidence
- design falsification tests
- recommend repairs

Outputs

Falsification Model

Consumers

- Experiment Planner

---

# Layer 9 — Experiment Planner

Responsibilities

- prioritize research
- estimate value
- estimate effort
- build research roadmap

Outputs

Experiment Plan

Consumers

- Discovery Engine

---

# Layer 10 — Discovery Engine

Responsibilities

- aggregate experiments
- detect recurring patterns
- identify research gaps
- prioritize discoveries

Outputs

Discovery Model

Consumers

- Research Memory

---

# Layer 11 — Research Memory

Responsibilities

- persist research sessions
- persist reasoning
- persist hypotheses
- persist experiments
- preserve discovery history

Outputs

Research Memory Records

Consumers

Future Atlas sessions

---

# Validation Domains

Validation domains evaluate the Canonical Structural Model.

They do not construct it.

Current validation domains

```text
Vedic Behavior
```

Future validation domains

```text
Planetary Transits

Historical Biography

Psychology

Population Statistics

Cardology

Numerology

Additional symbolic or empirical domains
```

Validation domains contribute observations.

They never overwrite canonical structure.

---

# Dependency Rules

Every Atlas service must satisfy the following rules.

## Rule 1

Services only depend downward.

---

## Rule 2

Canonical Structural Model is immutable.

---

## Rule 3

AtlasProfile is the only canonical profile interface.

---

## Rule 4

Atlas AI orchestrates services.

It does not replace them.

---

## Rule 5

Reasoning never modifies evidence.

---

## Rule 6

Hypotheses never become evidence.

---

## Rule 7

Falsification always attempts to disprove hypotheses.

---

## Rule 8

Experiments are generated from falsification.

Not from intuition.

---

## Rule 9

Discovery aggregates completed research.

---

## Rule 10

Research Memory stores outcomes.

It never recomputes them.

---

# Circular Dependency Policy

The following dependency direction is prohibited.

```text
Reasoning

↓

Hypothesis

↓

Reasoning
```

Likewise,

```text
Atlas AI

↓

Graph Intelligence

↓

Atlas AI
```

Every dependency graph must remain acyclic.

---

# Extension Policy

Future services must specify:

- dependencies
- inputs
- outputs
- confidence model
- warning model
- failure modes

before implementation.

No service may bypass AtlasProfile.

No service may bypass Atlas AI.

No service may modify the Canonical Structural Model after construction.

---

# Current Cognitive Stack

The current validated execution chain is:

```text
Research Corpus
        │
        ▼
Canonical Structural Model
        │
        ▼
AtlasProfile
        │
        ▼
Profile Intelligence
        │
        ▼
Atlas AI
        │
        ▼
Query Planner
        │
        ▼
Reasoning
        │
        ▼
Hypothesis
        │
        ▼
Falsification
        │
        ▼
Experiment Planner
        │
        ▼
Discovery
        │
        ▼
Research Memory
```

This dependency graph represents the current architecture of Atlas Phase II.

Future services must integrate into this graph without violating the dependency rules defined above.