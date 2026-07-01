# Atlas Confidence Model

**Project:** Atlas  
**Architecture Version:** Phase II  
**Document:** Confidence Model  
**Status:** Canonical Engineering Specification

---

# Purpose

Confidence is Atlas' quantitative estimate of how strongly available evidence supports an interpretation.

Confidence is **never** a measure of truth.

Confidence is a measure of evidential support given the information currently available.

Every Atlas service must use this confidence model.

No service may invent its own confidence semantics.

---

# Design Goals

The Confidence Model guarantees:

- deterministic scoring
- explainable calculations
- reproducibility
- bounded values
- confidence propagation
- service interoperability

---

# Fundamental Principle

Atlas separates three concepts.

```text
Structure

↓

Evidence

↓

Confidence
```

Structure exists.

Evidence is collected.

Confidence evaluates evidence.

Confidence never changes canonical structure.

---

# Confidence Is Not Truth

Atlas never claims certainty.

Confidence answers:

> "How strongly does the available evidence support this interpretation?"

Confidence does **not** answer:

> "Is this objectively true?"

---

# Confidence Scale

Atlas confidence is represented as:

```text
score

0.0000 → 1.0000
```

Every confidence object also exposes:

```text
percent

0.00 → 100.00
```

and

```text
label
```

---

# Standard Confidence Object

Every service returns confidence using the same structure.

```json
{
    "score": 0.8427,
    "percent": 84.27,
    "label": "high"
}
```

No alternate confidence formats are permitted.

---

# Confidence Labels

Atlas defines four standard confidence ranges.

| Score | Label |
|--------|--------|
| 0.80 – 1.00 | High |
| 0.60 – 0.79 | Moderate |
| 0.40 – 0.59 | Limited |
| 0.00 – 0.39 | Low |

These ranges are global.

Individual services may not redefine them.

---

# Confidence Sources

Confidence may be derived from:

- evidence completeness
- graph quality
- topology quality
- temporal completeness
- service agreement
- validation agreement
- warning count
- error count
- missing artifacts

Every contributing factor must be explainable.

---

# Confidence Propagation

Confidence flows through the cognitive pipeline.

```text
Core Intelligence

↓

Atlas AI

↓

Reasoning

↓

Hypothesis

↓

Falsification

↓

Experiment

↓

Discovery
```

Each stage consumes previous confidence.

No stage ignores upstream uncertainty.

---

# Confidence Aggregation

When multiple services contribute to a conclusion:

```text
Service A

+

Service B

+

Service C

↓

Aggregate Confidence
```

Aggregation should preserve uncertainty.

Confidence should never increase without additional supporting evidence.

---

# Penalties

Confidence decreases when uncertainty increases.

Examples include:

- missing artifacts
- unresolved temporal calculations
- incomplete graph construction
- missing validation domains
- service warnings
- failed services

Penalties must be deterministic.

---

# Warning Penalties

Warnings reduce confidence.

Warnings do not terminate execution.

Examples:

- missing research session
- incomplete temporal layer
- unavailable graph metrics

Warnings propagate downstream.

---

# Error Penalties

Errors indicate execution failure.

Errors may prevent confidence calculation.

Errors always propagate.

---

# Confidence Components

Every confidence calculation should expose its contributing components whenever practical.

Example:

```json
{
    "overall": 0.82,
    "components": {
        "graph": 0.91,
        "temporal": 0.84,
        "evidence": 0.88,
        "validation": 0.74
    }
}
```

Confidence should always be explainable.

---

# Canonical Structure

The Canonical Structural Model does not possess confidence.

Canonical structure is deterministic.

Confidence applies only to interpretations.

Incorrect:

```text
Graph

↓

Confidence
```

Correct:

```text
Graph

↓

Graph Intelligence

↓

Confidence
```

---

# Validation Domains

Validation domains contribute confidence only to their own observations.

They never modify canonical confidence directly.

Example:

```text
Canonical Structure

↓

Vedic Validation

↓

Validation Confidence
```

This confidence contributes to reasoning.

It does not alter structural confidence.

---

# Reasoning Confidence

Reasoning confidence reflects confidence in synthesized conclusions.

It depends upon:

- Atlas AI confidence
- evidence quality
- warning propagation
- validation agreement
- reasoning completeness

---

# Hypothesis Confidence

Hypothesis confidence reflects support for a specific explanation.

It should consider:

- supporting evidence
- counter evidence
- reasoning confidence
- validation agreement

---

# Falsification Confidence

Falsification does not increase confidence.

It measures pressure against a hypothesis.

Successful falsification may reduce confidence.

Failed falsification may preserve confidence.

---

# Experiment Confidence

Experiment confidence estimates expected research value.

It is not equivalent to hypothesis confidence.

Examples:

- expected confidence gain
- expected falsification value
- expected information gain

---

# Discovery Confidence

Discovery confidence reflects confidence that an observed pattern represents a meaningful research opportunity.

Discovery confidence depends upon:

- repeated observations
- multiple profiles
- consistent evidence
- independent validation

---

# Confidence Monotonicity

Confidence should obey one fundamental rule.

```text
Additional evidence

↓

Equal or Higher confidence
```

```text
Additional uncertainty

↓

Equal or Lower confidence
```

Confidence should never increase because uncertainty increased.

---

# Explainability

Every confidence score should be reproducible.

Atlas should always be able to explain:

- why confidence is high
- why confidence is low
- what reduced confidence
- what could increase confidence

---

# Future Extensions

Future confidence models may incorporate:

- Bayesian updating
- probabilistic graphical models
- empirical calibration
- longitudinal validation
- population calibration
- confidence learning

Future extensions must preserve the canonical confidence object.

---

# Engineering Guarantees

The Atlas Confidence Model guarantees:

- deterministic calculations
- reproducibility
- explainability
- bounded scores
- standardized labels
- confidence propagation
- interoperability across services

Every Atlas subsystem must conform to these guarantees.

---

# Long-Term Vision

Confidence is the mechanism that allows Atlas to reason under uncertainty while remaining scientifically disciplined.

Rather than presenting conclusions as certain, Atlas quantifies evidential support, propagates uncertainty through every reasoning stage, and continuously refines confidence as additional evidence becomes available.

Confidence is therefore not a measure of belief.

It is a measure of how well current evidence supports the present interpretation.