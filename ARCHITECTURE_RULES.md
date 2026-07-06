# ARCHITECTURE_RULES.md

# Atlas Architecture Rules

**Version:** 2.0  
**Status:** LOCKED  
**Authority:** Atlas Core Architecture

---

# Purpose

This document defines the immutable architectural rules of Atlas.

Unlike coding standards or style guides, these rules govern **how the system itself is allowed to evolve**.

If an implementation violates one of these rules, the implementation—not the rule—must change.

Architecture always takes precedence over convenience.

---

# The Prime Directive

> **Compile once. Consume everywhere.**

Everything in Atlas is built around this principle.

The compiler creates structural intelligence.

Everything else consumes structural intelligence.

Nothing else creates it.

---

# Rule 1 — Single Source of Truth

Atlas has exactly one authoritative compiler.

```python
compile_canonical_profile(profile_key)
```

Location

```text
src/atlas/compiler/canonical_profile_compiler.py
```

Every profile must originate from this compiler.

There are no alternate compilation paths.

---

# Rule 2 — Single Canonical Artifact

Atlas has exactly one canonical profile artifact.

```text
profile.payload.json
```

This artifact represents the complete structural state of a profile.

Every subsystem consumes this artifact.

No subsystem supersedes it.

---

# Rule 3 — Layer Ownership

Every intelligence layer has exactly one owner.

| Layer | Owner |
|--------|-------|
| Identity | Canonical Compiler |
| Birth | Canonical Compiler |
| Lifecycle | Canonical Compiler |
| Temporal | Canonical Compiler |
| Natal | Canonical Compiler |
| Ephemeris | Canonical Compiler |
| Graph | Canonical Compiler |
| Topology | Canonical Compiler |
| Resonance | Canonical Compiler |
| Fingerprint | Canonical Compiler |
| Classification | Canonical Compiler |
| Metrics | Canonical Compiler |

No layer may have multiple authoritative producers.

---

# Rule 4 — Deterministic Before Interpretive

Atlas always follows this order.

```text
Facts

↓

Structure

↓

Classification

↓

Interpretation

↓

Presentation
```

Interpretation never creates facts.

Facts always precede interpretation.

---

# Rule 5 — Compiler Responsibilities

Only the compiler may generate:

- Identity
- Temporal Intelligence
- Natal Charts
- Ephemeris
- Graph
- Topology
- Resonance
- Fingerprint
- Classification
- Metrics

No other component may regenerate these layers.

---

# Rule 6 — Services Consume

Services exist to interpret compiled intelligence.

Services may:

- summarize
- compare
- explain
- validate
- synthesize
- analyze

Services may not:

- rebuild graph
- regenerate topology
- regenerate resonance
- regenerate fingerprints
- perform classification

---

# Rule 7 — UI Never Computes Intelligence

Dashboard pages have one responsibility.

Render information.

Dashboard pages may:

- display
- filter
- search
- visualize

Dashboard pages must not:

- classify
- compile
- generate graphs
- compute topology
- run ephemeris
- infer missing intelligence

---

# Rule 8 — Population Intelligence Is Read-Only

Population Intelligence consumes many compiled profiles.

It may produce:

- clusters
- nearest neighbors
- distributions
- statistics
- topology maps
- similarity matrices

It must never modify an individual profile.

---

# Rule 9 — Research Is Read-Only

Research layers exist to answer questions.

Research may produce:

- hypotheses
- experiments
- falsification
- confidence
- validation

Research must never alter canonical data.

---

# Rule 10 — Validation Reports

Validation detects issues.

Validation never repairs them.

Correct

```text
Validation

↓

Report
```

Incorrect

```text
Validation

↓

Rewrite Payload
```

---

# Rule 11 — Dependency Direction

The dependency graph is fixed.

```text
Compiler
      │
      ▼
Canonical Payload
      │
      ▼
Services
      │
      ▼
Atlas AI
      │
      ▼
Dashboard
```

Dependencies may only flow downward.

---

# Forbidden Dependency Graphs

Not allowed

```text
Dashboard
      │
      ▼
Compiler
```

Not allowed

```text
Research
      │
      ▼
Compiler
```

Not allowed

```text
Atlas AI
      │
      ▼
Compiler
```

---

# Rule 12 — Canonical Schema Is Sacred

The canonical schema is the platform contract.

Changing it requires:

- compiler update
- schema documentation update
- service update
- dashboard update
- validation update
- tests

Undocumented schema changes are prohibited.

---

# Rule 13 — Legacy Is Never Authoritative

Legacy artifacts may exist.

Examples

```text
profile.acf.json
identity_stack.json
profile_summary.json
profile_interpretation.json
codex_report.md
```

They exist only for:

- exports
- migration
- backward compatibility

They are never authoritative.

---

# Rule 14 — No Parallel Pipelines

Forbidden

```text
profile.intake

↓

compiler A
```

and

```text
profile.intake

↓

compiler B
```

There is only one pipeline.

---

# Rule 15 — No Duplicate Intelligence

If information already exists in the payload,

reuse it.

Do not regenerate it.

Wrong

```python
calculate_topology()
```

Correct

```python
payload["topology"]
```

---

# Rule 16 — Missing Is Explicit

Every missing layer returns

```json
{
  "status": "missing",
  "reason": "",
  "warnings": [],
  "errors": []
}
```

Never

```python
None
```

Never silently omit keys.

---

# Rule 17 — Stable Layer Interfaces

Every layer exposes a stable interface.

Example

```text
identity

temporal

graph

topology

resonance

fingerprint

classification

metrics
```

Consumers rely on these interfaces.

---

# Rule 18 — Extension Pattern

Every new intelligence layer follows:

```text
Compiler

↓

Payload

↓

Metrics

↓

Services

↓

Dashboard

↓

Population

↓

Research
```

No shortcuts.

---

# Rule 19 — Separation of Concerns

Atlas is divided into distinct architectural domains.

### Compilation

Produces intelligence.

---

### Services

Interpret intelligence.

---

### Atlas AI

Synthesizes services.

---

### Dashboard

Displays intelligence.

---

### Population Intelligence

Analyzes populations.

---

### Research

Generates scientific inquiry.

---

### Validation

Measures correctness.

These domains remain independent.

---

# Rule 20 — Determinism

Given identical input,

Atlas should produce identical output.

No randomness.

No hidden state.

No nondeterministic behavior.

---

# Rule 21 — Explainability

Every deterministic result should be traceable.

Every classification should expose its basis.

Every topology should expose its source.

Every resonance should expose its derivation.

Atlas should always answer:

> Why was this produced?

---

# Rule 22 — Evidence Over Assumption

When information is unavailable,

report uncertainty.

Never fabricate structure.

Never infer unsupported facts.

Evidence always outweighs speculation.

---

# Rule 23 — Architecture Before Optimization

Never sacrifice architectural integrity for short-term convenience.

A slightly slower deterministic system is preferable to a faster, inconsistent one.

---

# Rule 24 — Documentation Is Architecture

Architecture documentation is part of the system.

When architecture changes,

update:

- README.md
- ARCHITECTURE.md
- PIPELINE.md
- CANONICAL_SCHEMA.md
- ARCHITECTURE_RULES.md
- DEVELOPMENT_RULES.md

before merging.

---

# Rule 25 — Architectural Smells

If any of these appear,

stop development and refactor.

❌ Multiple compilers

❌ Multiple payload formats

❌ Duplicate topology generators

❌ Duplicate classification systems

❌ Dashboard calculations

❌ Services rebuilding intelligence

❌ Circular dependencies

❌ Hidden mutations

❌ Legacy artifacts becoming authoritative

❌ Schema drift

---

# Rule 26 — Review Checklist

Before approving any architectural change, ask:

- Does this preserve the canonical pipeline?
- Does it introduce another source of truth?
- Does it duplicate existing intelligence?
- Does it violate dependency direction?
- Does it require a schema update?
- Does it reduce architectural complexity?
- Does it improve determinism?
- Is it fully documented?

If any answer is **No**, redesign before merging.

---

# Rule 27 — Atlas Philosophy

Atlas is not a collection of features.

Atlas is an operating system for structural intelligence.

Every subsystem should strengthen the platform.

Every commit should reduce entropy.

Every layer should become easier to understand.

The architecture should become simpler—not more complicated—as Atlas grows.

---

# Constitutional Principle

The architecture of Atlas is governed by one enduring principle:

> **Compile once. Consume everywhere. Preserve determinism. Document the contract.**

Everything else is an implementation detail.