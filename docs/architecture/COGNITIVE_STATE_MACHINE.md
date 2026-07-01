# Atlas Cognitive State Machine

**Project:** Atlas  
**Architecture Version:** Phase II  
**Document:** Cognitive State Machine  
**Status:** Canonical Architecture Specification

---

# Purpose

The Atlas Cognitive State Machine defines the lifecycle of every investigation performed by Atlas.

While the Service Dependency Graph describes **which services depend upon one another**, the Cognitive State Machine describes **how knowledge progresses through those services**.

Every investigation should follow the same deterministic sequence of cognitive states.

The Cognitive State Machine ensures that reasoning remains reproducible, explainable, and scientifically disciplined.

---

# Philosophy

Atlas does not jump directly from a question to an answer.

Instead, every investigation progresses through a sequence of increasingly informed cognitive states.

Each state contributes information.

Each transition is deterministic.

Each transition produces a new research artifact.

---

# Complete State Machine

```text
USER QUERY
      │
      ▼
UNPLANNED
      │
      ▼
PLANNED
      │
      ▼
PROFILE READY
      │
      ▼
STRUCTURE READY
      │
      ▼
INTELLIGENCE READY
      │
      ▼
REASONING READY
      │
      ▼
HYPOTHESIS READY
      │
      ▼
UNDER FALSIFICATION
      │
      ▼
EXPERIMENT READY
      │
      ▼
DISCOVERY READY
      │
      ▼
MEMORIZED
```

Each state is deterministic.

No state may be skipped.

---

# State 0 — User Query

Input:

- Natural language
- API request
- Dashboard interaction
- Future autonomous task

Example

```text
Explain Nikola Tesla
```

Example

```text
Compare Nikola Tesla and Thomas Edison
```

No scientific interpretation occurs at this stage.

---

# State 1 — UNPLANNED

Description

The investigation exists only as a request.

No execution plan has been generated.

Responsible Service

```text
Query Planner
```

Transition Condition

A valid execution plan is produced.

---

# State 2 — PLANNED

Description

The investigation has an execution strategy.

Known information includes:

- intent
- scope
- profiles
- requested services
- execution hints

No intelligence has yet been executed.

Responsible Service

```text
Query Planner
```

Transition Condition

Atlas AI begins orchestration.

---

# State 3 — PROFILE READY

Description

AtlasProfile has been resolved.

Canonical identity has been loaded.

Structural construction is complete.

The investigation now possesses:

- identity
- canonical encoding
- planetary projection
- Kamea construction
- graph
- topology
- morphology
- resonance

Responsible System

```text
Canonical Structural Model
```

Transition Condition

Core Intelligence services begin execution.

---

# State 4 — STRUCTURE READY

Description

The Canonical Structural Model is available.

Structural Reality is fixed.

No interpretation has occurred.

Canonical Structure is now immutable.

Transition Condition

Intelligence services begin analysis.

---

# State 5 — INTELLIGENCE READY

Description

Atlas AI has completed orchestration.

Available information includes:

- observations
- evidence
- narrative
- graph intelligence
- temporal intelligence
- population intelligence
- validation domains
- confidence
- warnings
- metrics

Responsible Service

```text
Atlas AI
```

Transition Condition

Reasoning begins.

---

# State 6 — REASONING READY

Description

Scientific interpretation has completed.

The investigation now contains:

- conclusions
- limitations
- conflicts
- recommendations
- reasoning confidence

Responsible Service

```text
Reasoning Engine
```

Transition Condition

Hypothesis generation begins.

---

# State 7 — HYPOTHESIS READY

Description

Competing explanations have been generated.

Each hypothesis contains:

- supporting evidence
- counter evidence
- assumptions
- confidence
- falsification strategy

Responsible Service

```text
Hypothesis Engine
```

Transition Condition

Scientific challenge begins.

---

# State 8 — UNDER FALSIFICATION

Description

Every hypothesis is actively challenged.

The investigation now includes:

- contradiction analysis
- disconfirming signals
- repair actions
- falsification pressure
- recommended tests

Responsible Service

```text
Falsification Engine
```

Transition Condition

Research priorities are established.

---

# State 9 — EXPERIMENT READY

Description

The investigation now contains actionable research.

Available information includes:

- experiments
- research phases
- expected information gain
- implementation effort
- success criteria

Responsible Service

```text
Experiment Planner
```

Transition Condition

Population-level synthesis begins.

---

# State 10 — DISCOVERY READY

Description

The investigation contributes to scientific discovery.

The Discovery Engine identifies:

- recurring patterns
- research gaps
- open questions
- research priorities
- population trends

Responsible Service

```text
Discovery Engine
```

Transition Condition

Research is preserved.

---

# State 11 — MEMORIZED

Description

The investigation becomes part of Atlas Research Memory.

Stored information includes:

- reasoning
- hypotheses
- falsification
- experiments
- discoveries
- confidence
- warnings
- metadata
- lineage

Responsible Service

```text
Research Memory
```

The investigation is complete.

---

# State Transitions

Transitions must satisfy the following rules.

## Rule 1

Transitions are deterministic.

Identical inputs always produce identical state transitions.

---

## Rule 2

No state may be skipped.

Every investigation passes through every cognitive stage.

---

## Rule 3

Each state produces a persistent artifact.

Examples

```text
PLANNED

↓

Execution Plan
```

```text
INTELLIGENCE READY

↓

Atlas AI Payload
```

```text
REASONING READY

↓

Reasoning Model
```

```text
HYPOTHESIS READY

↓

Hypothesis Model
```

```text
UNDER FALSIFICATION

↓

Falsification Model
```

```text
EXPERIMENT READY

↓

Experiment Model
```

```text
DISCOVERY READY

↓

Discovery Model
```

```text
MEMORIZED

↓

Research Record
```

---

# State Invariants

Every cognitive state preserves the following invariants.

- Canonical Structure is immutable.
- Confidence propagates forward.
- Warnings propagate forward.
- Errors propagate forward.
- Previous artifacts remain available.
- No downstream state modifies upstream artifacts.

---

# State Ownership

Each state has one owner.

| State | Owner |
|--------|-------|
| UNPLANNED | Query Planner |
| PLANNED | Query Planner |
| PROFILE READY | Canonical Structural Model |
| STRUCTURE READY | AtlasProfile |
| INTELLIGENCE READY | Atlas AI |
| REASONING READY | Reasoning Engine |
| HYPOTHESIS READY | Hypothesis Engine |
| UNDER FALSIFICATION | Falsification Engine |
| EXPERIMENT READY | Experiment Planner |
| DISCOVERY READY | Discovery Engine |
| MEMORIZED | Research Memory |

Ownership is exclusive.

Only the owning subsystem may create that state.

---

# Recovery

If execution fails:

```text
Current State

↓

Failure

↓

Diagnostic

↓

Recovery

↓

Resume
```

Atlas should resume from the most recent valid cognitive state whenever possible.

Recomputation should be minimized.

---

# Autonomous Research

Future versions of Atlas may begin without a human query.

Example

```text
Discovery Engine

↓

Research Opportunity

↓

Generated Query

↓

UNPLANNED
```

The state machine remains unchanged.

Only the origin of the investigation changes.

---

# Relationship to the Scientific Method

The Cognitive State Machine operationalizes the scientific method.

It provides the execution lifecycle through which every scientific investigation progresses.

The Scientific Method defines *why* Atlas performs each stage.

The Cognitive State Machine defines *how* Atlas executes those stages.

---

# Engineering Guarantees

The Cognitive State Machine guarantees:

- deterministic progression
- reproducible execution
- immutable structural foundations
- explicit cognitive transitions
- explainable research lineage
- recoverable execution

Every Atlas investigation must conform to these guarantees.

---

# Long-Term Vision

The Cognitive State Machine is the execution backbone of Atlas.

As new intelligence services, validation domains, autonomous agents, and research capabilities are introduced, they should integrate by participating in the existing cognitive lifecycle rather than creating parallel reasoning paths.

By enforcing explicit cognitive states, Atlas ensures that every investigation—from a single profile analysis to large-scale autonomous scientific discovery—remains transparent, reproducible, and grounded in the same deterministic research process.

The Cognitive State Machine therefore serves as the operational framework through which the Atlas platform transforms questions into enduring scientific knowledge.