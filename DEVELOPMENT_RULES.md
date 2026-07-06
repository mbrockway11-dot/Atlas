# DEVELOPMENT_RULES.md

# Atlas Development Rules

**Version:** 2.0  
**Status:** Locked  
**Authority:** Atlas Architecture

---

# Purpose

This document defines the engineering rules governing Atlas.

These rules exist to preserve a deterministic, maintainable, and scalable architecture as Atlas grows.

Every contributor should read this document before writing code.

---

# Core Philosophy

Atlas is not a collection of scripts.

Atlas is a deterministic structural intelligence platform.

Every new feature should make the platform:

- simpler
- more deterministic
- easier to reason about
- easier to validate
- easier to extend

Never the opposite.

---

# The Golden Rule

> **Compile once. Consume everywhere.**

This single sentence governs the entire architecture.

---

# Rule 1 — One Compiler

There is exactly **one** compiler.

```python
compile_canonical_profile(profile_key)
```

Location

```text
src/atlas/compiler/canonical_profile_compiler.py
```

Everything begins here.

Nothing bypasses it.

---

# Rule 2 — One Canonical Artifact

The only authoritative profile artifact is

```text
profile.payload.json
```

Everything consumes this payload.

Nothing supersedes it.

---

# Rule 3 — Never Build Another Compiler

Forbidden

```python
build_profile_payload_v2()

compile_profile()

compile_person()

compile_graph()

compile_temporal()

compile_everything()
```

If intelligence belongs in the canonical payload, extend the canonical compiler.

Never create parallel compilation paths.

---

# Rule 4 — Services Consume

Services read compiled intelligence.

They do not create intelligence.

Correct

```text
profile.payload.json

↓

Profile Report Service
```

Incorrect

```text
Profile Report Service

↓

Compile Natal
```

---

# Rule 5 — Dashboard Renders

Dashboard pages display information.

They never compute it.

Correct

```text
payload

↓

render()
```

Incorrect

```text
payload

↓

calculate topology

↓

render()
```

---

# Rule 6 — Research Is Read-Only

Research modules never mutate profiles.

Allowed

```text
profile.payload.json

↓

hypothesis
```

Forbidden

```text
profile.payload.json

↓

rewrite topology
```

---

# Rule 7 — Validation Never Fixes

Validation identifies problems.

Validation never repairs data.

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

Modify Payload
```

---

# Rule 8 — Never Read Legacy Artifacts

New code must never depend on

```text
profile.acf.json
identity_stack.json
profile_summary.json
profile_interpretation.json
```

Legacy artifacts may exist only for export or backward compatibility.

---

# Rule 9 — No Duplicate Intelligence

If a value already exists in the payload, reuse it.

Never calculate it again.

Example

Wrong

```python
calculate_topology()
```

Right

```python
payload["topology"]
```

---

# Rule 10 — Missing Is Better Than Fake

Never invent data.

Correct

```json
{
  "status":"missing"
}
```

Incorrect

```json
{
  "topology":"unknown"
}
```

---

# Rule 11 — Every Layer Has One Owner

Identity

↓

Compiler

Temporal

↓

Compiler

Topology

↓

Compiler

Resonance

↓

Compiler

Fingerprint

↓

Compiler

Classification

↓

Compiler

No shared ownership.

---

# Rule 12 — Stable Schema

Never change the payload shape casually.

If schema changes

Update

```
CANONICAL_SCHEMA.md
```

first.

---

# Rule 13 — Explicit Failures

Every failure returns

```json
{
  "status":"missing",
  "reason":"",
  "warnings":[],
  "errors":[]
}
```

Never

```python
None
```

Never silent failure.

---

# Rule 14 — Small Services

A service should have one responsibility.

Examples

Good

```
profile_report_service
```

```
temporal_intelligence_service
```

```
graph_intelligence_service
```

Bad

```
super_service_everything.py
```

---

# Rule 15 — Pure Functions Preferred

Given identical input

↓

produce identical output

Avoid hidden state.

Avoid globals.

Avoid randomness.

---

# Rule 16 — No Circular Dependencies

Allowed

```
Compiler

↓

Services

↓

Dashboard
```

Forbidden

```
Dashboard

↓

Compiler
```

Forbidden

```
Service A

↓

Service B

↓

Service A
```

---

# Rule 17 — Dashboard Pages Stay Thin

Pages should contain

- layout
- widgets
- rendering

Pages should not contain

- business logic
- graph algorithms
- topology calculations
- temporal compilation

---

# Rule 18 — Business Logic Lives in Services

If logic exceeds a few lines

↓

move it into a service.

UI imports services.

Services never import UI.

---

# Rule 19 — Compiler Owns Intelligence

Only the compiler may generate

- graph
- topology
- resonance
- fingerprint
- classification

Every other module consumes these.

---

# Rule 20 — Every Layer Is Testable

Every compiler stage must have

- deterministic input
- deterministic output
- repeatable tests

No hidden dependencies.

---

# Rule 21 — Metrics Everywhere

Every significant compiler stage should expose metrics.

Example

```json
{
    "has_graph": true,
    "has_topology": true,
    "has_resonance": true
}
```

Metrics make debugging easy.

---

# Rule 22 — Services Never Guess

If data is missing

Return

```
missing
```

Do not infer.

Do not fabricate.

---

# Rule 23 — One Responsibility Per Module

Good

```
graph_service.py

topology_service.py

temporal_service.py
```

Bad

```
misc.py

utilities.py

helpers.py
```

Modules should be cohesive.

---

# Rule 24 — Prefer Composition

Compose

```
Compiler

↓

Services

↓

AI
```

Avoid inheritance-heavy designs.

---

# Rule 25 — Population Never Mutates Individuals

Population Intelligence

reads

many payloads

↓

produces

clusters

statistics

similarity

Never writes back into profiles.

---

# Rule 26 — AI Explains

Atlas AI performs

- synthesis
- reasoning
- explanation
- prioritization

Atlas AI never creates deterministic intelligence.

---

# Rule 27 — Documentation Is Part of the Code

Whenever architecture changes

Update

- ARCHITECTURE.md
- PIPELINE.md
- CANONICAL_SCHEMA.md
- DEVELOPMENT_RULES.md

Documentation is not optional.

---

# Rule 28 — New Layers Follow the Same Process

Every future layer must

1. be compiled
2. be documented
3. expose metrics
4. be rendered
5. be testable

Example

Behavior Layer

↓

Compiler

↓

Payload

↓

Dashboard

↓

Population

↓

Research

---

# Rule 29 — CI Requirements

No merge without

- passing tests
- successful compile
- schema integrity
- dashboard audit
- documentation update (if architecture changed)

---

# Rule 30 — Simplicity Wins

When choosing between two designs

Prefer the one that

- has fewer moving parts
- has fewer dependencies
- is easier to explain
- produces fewer artifacts
- has one obvious execution path

---

# Architectural Smells

If you encounter any of these, stop and refactor.

❌ Two compilers

❌ Two payload formats

❌ Services rebuilding intelligence

❌ Dashboard computing intelligence

❌ Circular imports

❌ Duplicate schema

❌ Hidden mutation

❌ Silent failures

❌ Legacy becoming authoritative

---

# Pull Request Checklist

Before merging, ask:

- Does this follow the canonical pipeline?
- Does it duplicate existing logic?
- Does it belong in the compiler?
- Does it belong in a service?
- Does it change the schema?
- Does documentation need updating?
- Does it pass all tests?
- Does it preserve determinism?

If any answer is "no" or "unclear", revise before merging.

---

# Final Principle

Atlas should become **simpler** as it grows.

Every commit should reduce architectural entropy, not increase it.

If a feature cannot be explained in terms of the canonical compiler and the canonical payload, it probably does not belong in Atlas.

> **Compile once. Consume everywhere. Document everything.**