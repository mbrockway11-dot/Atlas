# Atlas Warning & Error Model

**Project:** Atlas  
**Architecture Version:** Phase II  
**Document:** Warning & Error Model  
**Status:** Canonical Engineering Specification

---

# Purpose

The Warning & Error Model defines how Atlas represents uncertainty, execution issues, missing information, and failures.

Its objectives are:

- deterministic behavior
- explainable execution
- consistent diagnostics
- confidence propagation
- reproducibility
- graceful degradation

Every Atlas service must implement this model.

---

# Philosophy

Atlas distinguishes between three categories:

```text
Success

↓

Warning

↓

Error
```

These categories are not interchangeable.

Warnings communicate uncertainty.

Errors communicate execution failure.

---

# Definitions

## Success

A service successfully completed its responsibilities.

A successful service may still contain warnings.

Example:

```text
Graph Intelligence

Success

2 warnings

0 errors
```

---

## Warning

A warning indicates that execution completed but some limitation exists.

Warnings do **not** invalidate results.

Warnings reduce confidence.

Warnings propagate downstream.

---

## Error

An error indicates the requested computation could not be completed.

Errors terminate the affected computation.

Errors propagate downstream.

Errors never silently disappear.

---

# Execution States

Every service must terminate in one of the following states.

| State | Meaning |
|---------|----------|
| Success | Completed successfully |
| Success With Warnings | Completed with limitations |
| Failed | Execution terminated |

---

# Canonical Payload

Every service should expose:

```json
{
    "success": true,
    "warnings": [],
    "errors": [],
    "metrics": {}
}
```

Warnings and errors should always exist as arrays.

Empty arrays indicate no issues.

---

# Warning Object

Warnings should follow a consistent schema.

```json
{
    "code": "TEMPORAL_MISSING_DASHA",
    "severity": "warning",
    "message": "Moon nakshatra could not be resolved.",
    "component": "temporal_intelligence"
}
```

---

# Error Object

Errors should follow the same structure.

```json
{
    "code": "PROFILE_NOT_FOUND",
    "severity": "error",
    "message": "Profile does not exist.",
    "component": "profile_loader"
}
```

---

# Severity Levels

Atlas defines four severity levels.

```text
Info

Warning

Error

Critical
```

---

## Info

Informational only.

Does not affect confidence.

---

## Warning

Execution continues.

Confidence decreases.

---

## Error

Execution cannot continue for the affected service.

Confidence cannot increase.

---

## Critical

System integrity is compromised.

Execution should terminate.

---

# Warning Categories

Warnings should be categorized.

Current categories include:

```text
Missing Artifact

Incomplete Data

Validation Limitation

Temporal Limitation

Graph Limitation

Population Limitation

Research Limitation

Configuration
```

Future categories should extend this list.

---

# Error Categories

Errors should be categorized.

Examples include:

```text
Missing Profile

Invalid Schema

Corrupt Artifact

Missing Dependency

Execution Failure

Unexpected Exception

Configuration Failure
```

---

# Propagation Rules

Warnings propagate downstream.

Example:

```text
Temporal Intelligence

↓

Atlas AI

↓

Reasoning

↓

Hypothesis

↓

Experiment
```

Every downstream service should be aware of upstream warnings.

---

Errors also propagate.

Example:

```text
Profile Report

↓

Atlas AI

↓

Reasoning

↓

Hypothesis
```

If the Profile Report fails, downstream services should report the failure rather than fabricate results.

---

# Confidence Interaction

Warnings reduce confidence.

Errors prevent confidence calculation.

Confidence should explain:

```text
Score

↓

Penalties

↓

Warnings

↓

Errors
```

---

# Canonical Structure

Warnings and errors never modify:

- canonical graph
- topology
- morphology
- resonance
- identity

The Canonical Structural Model remains deterministic.

Warnings describe interpretation.

They do not describe structure.

---

# Atlas AI Responsibilities

Atlas AI must aggregate:

- warnings
- errors
- successful services
- failed services

Atlas AI should expose unified diagnostics.

---

# Reasoning Responsibilities

Reasoning must acknowledge uncertainty.

Reasoning should never ignore warnings.

Example:

```text
Primary limitations

- Missing research session

- Moon nakshatra unresolved

- Graph confidence limited
```

---

# Hypothesis Responsibilities

Hypothesis generation should consider warnings.

Warnings reduce confidence in hypotheses.

Warnings should also generate possible explanations for uncertainty.

---

# Falsification Responsibilities

Warnings should become candidate falsification targets.

Example:

```text
Missing temporal layer

↓

Suggested repair

↓

Resolve Moon nakshatra

↓

Repeat experiment
```

---

# Experiment Responsibilities

Warnings frequently generate experiments.

Examples:

```text
Missing graph metrics

↓

Generate graph metrics
```

```text
Missing biography

↓

Acquire additional evidence
```

---

# Discovery Responsibilities

Discovery should identify recurring warnings.

Examples:

```text
Moon nakshatra unresolved

appears in

481 profiles
```

↓

Research Priority

---

# Research Memory

Research Memory stores:

- warnings
- errors
- confidence
- repair actions

Future sessions should learn from recurring issues.

---

# User Experience

Warnings should be visible.

Errors should be understandable.

Atlas should never expose raw stack traces to end users.

Instead:

```text
Unable to resolve Moon nakshatra.

Temporal interpretation is limited.
```

rather than

```text
KeyError line 281
```

---

# Logging

Warnings should be logged.

Errors should be logged.

Critical failures should be logged with sufficient context for reproduction.

---

# Determinism

Warnings must be deterministic.

The same input should produce the same warnings.

Errors should also be reproducible.

---

# Engineering Guarantees

The Warning & Error Model guarantees:

- standardized diagnostics
- deterministic warning propagation
- deterministic error propagation
- confidence integration
- explainable failures
- graceful degradation

Every Atlas service must implement these guarantees.

---

# Long-Term Vision

Warnings and errors are not merely diagnostics.

They are research signals.

Recurring warnings identify weaknesses in the research corpus.

Recurring errors identify weaknesses in the platform.

By systematically tracking, propagating, and learning from warnings and errors, Atlas continuously improves both its engineering quality and its scientific methodology.