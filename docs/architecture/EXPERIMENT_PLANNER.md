# Experiment Planner

**Project:** Atlas  
**Architecture Version:** Phase II  
**Document:** Experiment Planner Specification  
**Status:** Canonical Service Specification

---

# Purpose

The Experiment Planner transforms falsification results into actionable scientific investigations.

Rather than asking whether a hypothesis is correct, the Experiment Planner asks:

> "What experiment should Atlas perform next to reduce uncertainty?"

Its responsibility is to convert scientific uncertainty into structured research plans.

---

# Architectural Position

```text
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
```

The Experiment Planner begins after hypotheses have been critically evaluated.

---

# Responsibilities

The Experiment Planner is responsible for:

- prioritizing experiments
- estimating research value
- estimating implementation effort
- maximizing expected information gain
- reducing uncertainty
- organizing research phases
- scheduling future investigation

The Experiment Planner does not perform experiments.

It designs them.

---

# Inputs

The Experiment Planner consumes one deterministic object.

```text
Falsification Model
```

The model contains:

- priority cases
- falsification pressure
- contradictory evidence
- repair actions
- suggested tests
- confidence
- validation observations

---

# Outputs

The Experiment Planner produces a deterministic experiment model.

Example

```text
Experiment Model

Recommended Experiments

Research Phases

Expected Gain

Estimated Effort

Priority Score

Execution Order

Success Criteria
```

This model becomes the input to the Discovery Engine.

---

# Scientific Philosophy

Atlas assumes that every experiment should reduce uncertainty.

Experiments are not designed to prove hypotheses.

They are designed to increase understanding.

Every experiment should produce measurable information.

---

# Experiment Design

Every experiment should contain:

- title
- objective
- scientific motivation
- expected information gain
- estimated effort
- confidence impact
- execution steps
- success criteria

Experiments should be reproducible.

---

# Expected Information Gain

Every experiment estimates its potential value.

Examples:

- reduce uncertainty
- validate graph topology
- improve temporal completeness
- increase population evidence
- improve validation agreement

Information gain should always be explicit.

---

# Estimated Effort

Atlas estimates implementation effort.

Examples:

- low
- moderate
- high

Effort considers:

- engineering work
- research effort
- computational cost
- data acquisition

---

# Priority Score

Experiments are ranked by priority.

Priority considers:

- falsification pressure
- expected information gain
- implementation effort
- confidence improvement

Higher priority experiments should execute first.

---

# Research Phases

Experiments may be grouped into phases.

Example:

```text
Phase 1

Repair Missing Evidence

↓

Phase 2

Expand Validation

↓

Phase 3

Population Validation
```

Phases organize long-term research.

---

# Success Criteria

Every experiment must define success.

Examples:

- confidence increases
- uncertainty decreases
- contradiction resolved
- additional evidence acquired
- hypothesis rejected
- hypothesis strengthened

Success should be measurable.

---

# Validation Domains

Validation domains frequently generate experiments.

Examples:

```text
Vedic disagreement

↓

Acquire additional birth data
```

```text
Historical disagreement

↓

Collect additional biography
```

Validation domains therefore become research generators.

---

# Determinism

The Experiment Planner is deterministic.

Identical falsification models always produce identical experiment plans.

No stochastic planning is permitted.

---

# Dependencies

The Experiment Planner depends upon:

- Falsification Engine
- Confidence Model
- Warning & Error Model

It does not depend upon:

- Discovery Engine
- Research Memory

---

# Relationship to the Scientific Method

The Experiment Planner corresponds to experimental design.

```text
Observation

↓

Reasoning

↓

Hypothesis

↓

Falsification

↓

Experiment Design
```

Execution occurs outside the planner.

---

# Engineering Guarantees

The Experiment Planner guarantees:

- deterministic planning
- explainable priorities
- reproducible experiments
- measurable objectives
- standardized experiment models

Every experiment can be independently reviewed.

---

# Long-Term Vision

The Experiment Planner transforms Atlas from an analytical platform into an active research platform.

As Atlas evolves, the Experiment Planner will optimize scientific progress by continuously selecting the investigations most likely to reduce uncertainty, improve structural understanding, and strengthen or reject competing hypotheses.

Rather than accumulating information indiscriminately, Atlas will pursue research according to expected knowledge gain, ensuring that every investigation contributes meaningfully to the evolution of the Canonical Structural Model.