# Query Planner

**Project:** Atlas  
**Architecture Version:** Phase II  
**Document:** Query Planner Specification  
**Status:** Canonical Service Specification

---

# Purpose

The Query Planner is the entry point into the Atlas Cognitive Stack.

Its responsibility is to transform natural language into a deterministic execution plan.

The Query Planner performs **planning only**.

It does not perform reasoning.

It does not execute intelligence services.

It determines **what should be executed**.

---

# Responsibilities

The Query Planner is responsible for:

- parsing user queries
- identifying research intent
- determining execution scope
- resolving profile references
- selecting required intelligence services
- generating deterministic execution plans

---

# Position Within Atlas

```text
User Query
      │
      ▼
Query Planner
      │
      ▼
Execution Plan
      │
      ▼
Atlas AI
      │
      ▼
Reasoning
```

The Query Planner is the bridge between user language and Atlas execution.

---

# Inputs

The Query Planner accepts:

- natural language queries
- profile identifiers
- optional execution hints
- optional service constraints

Example:

```text
Explain Nikola Tesla
```

Example:

```text
Compare Nikola Tesla and Thomas Edison
```

---

# Outputs

The Query Planner produces a deterministic execution plan.

Example:

```json
{
    "intent": "profile_analysis",
    "scope": "profile",
    "profiles": [
        "nikola_tesla"
    ],
    "services": [
        "profile_report",
        "graph_intelligence",
        "temporal",
        "evidence",
        "narrative"
    ]
}
```

The execution plan is consumed by Atlas AI.

---

# Responsibilities by Stage

## Intent Detection

Determine what type of research is being requested.

Examples:

- profile analysis
- relationship analysis
- comparison
- discovery
- population research

Intent detection determines the overall execution path.

---

## Scope Detection

Determine the scope of analysis.

Current scopes include:

- profile
- relationship
- population

Only one primary scope is selected.

---

## Profile Resolution

Identify every referenced profile.

The Query Planner must resolve aliases when possible.

If resolution fails, an appropriate warning is produced.

---

## Service Selection

Based on intent and scope, determine which services should execute.

Examples:

Profile analysis:

```text
Profile Report

Narrative

Evidence

Graph Intelligence

Temporal Intelligence
```

Relationship analysis:

```text
Relationship Report

Relationship Evidence

Relationship Graph Intelligence
```

---

# Determinism

The Query Planner is deterministic.

Identical queries should produce identical execution plans.

No randomness is permitted.

---

# Service Independence

The Query Planner performs no interpretation.

It does not inspect graph topology.

It does not inspect temporal data.

It does not generate conclusions.

Its only responsibility is planning.

---

# Validation

Execution plans should be validated before execution.

Validation checks include:

- valid intent
- valid scope
- profile existence
- supported services

Warnings should be produced when ambiguity exists.

---

# Confidence

The Query Planner produces planning confidence.

Planning confidence measures confidence in:

- intent detection
- profile resolution
- execution completeness

Planning confidence is not analytical confidence.

---

# Warning Model

Warnings include:

- ambiguous query
- unresolved profile
- unsupported request
- incomplete query

Warnings propagate to Atlas AI.

---

# Error Model

Errors include:

- invalid request
- no profiles resolved
- unsupported intent
- malformed execution plan

Errors terminate planning.

---

# Dependencies

The Query Planner depends upon:

- AtlasProfile Registry
- Service Registry

The Query Planner does **not** depend upon:

- Graph Intelligence
- Reasoning
- Hypothesis
- Discovery

---

# Consumers

Execution plans are consumed by:

- Atlas AI

No other service should consume raw user queries.

---

# Extension Policy

Future intents should be added through the intent registry.

Future scopes should be added through the scope registry.

Future services should register themselves rather than requiring Query Planner modification whenever possible.

---

# Engineering Guarantees

The Query Planner guarantees:

- deterministic planning
- explainable intent detection
- reproducible execution plans
- service independence
- standardized outputs

---

# Long-Term Vision

The Query Planner represents the cognitive front door of Atlas.

As Atlas evolves toward autonomous research, the Query Planner will expand from interpreting user questions to planning internally generated research tasks, allowing Atlas to schedule, prioritize, and execute investigations without direct user prompts while preserving deterministic planning behavior.