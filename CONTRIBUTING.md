# CONTRIBUTING.md

# Contributing to Atlas

Thank you for contributing to Atlas.

Atlas is not simply a software project—it is a deterministic structural intelligence platform. Every contribution should strengthen the architecture, preserve reproducibility, and improve scientific transparency.

Before submitting code, please read:

- README.md
- ARCHITECTURE.md
- ARCHITECTURE_RULES.md
- DEVELOPMENT_RULES.md
- PIPELINE.md
- CANONICAL_SCHEMA.md
- METHODOLOGY.md

These documents define how Atlas is built and why.

---

# Core Philosophy

Atlas follows one architectural principle above all others:

> **Compile once. Consume everywhere.**

The canonical compiler produces structural intelligence.

Everything else consumes it.

If your contribution violates this principle, it should be redesigned before merging.

---

# Before You Begin

Every contributor should understand the Atlas architecture.

The platform is organized into six primary domains:

```text
Compiler
      ↓
Canonical Payload
      ↓
Services
      ↓
Atlas AI
      ↓
Dashboard
      ↓
Research & Population Intelligence
```

Each layer has a distinct responsibility.

---

# Repository Structure

```text
src/
│
├── atlas/
│   ├── compiler/
│   ├── services/
│   ├── graph/
│   ├── temporal/
│   ├── topology/
│   ├── resonance/
│   ├── fingerprint/
│   ├── reasoning/
│   ├── ai/
│   ├── cognition/
│   └── validation/
│
dashboard/
│
scripts/
│
tests/
│
docs/
```

---

# Development Workflow

A typical feature follows this lifecycle:

```text
Create feature branch
        ↓
Implement compiler or service
        ↓
Write tests
        ↓
Run validation
        ↓
Update documentation
        ↓
Open Pull Request
```

Never merge directly into the main branch.

---

# Branch Naming

Recommended conventions:

```text
feature/profile-dossier

feature/population-intelligence

feature/temporal-engine

feature/topology-viewer

fix/compiler-metrics

fix/profile-report

docs/methodology-update

refactor/service-cleanup

research/transit-engine
```

---

# Commit Message Guidelines

Use clear, descriptive commit messages.

Examples:

```text
Add canonical profile compiler

Implement topology compilation

Refactor graph service

Modernize profile dossier UI

Add temporal intelligence metrics

Fix resonance layer serialization

Update canonical schema documentation
```

Avoid generic messages such as:

```text
Fix stuff

Update

Changes

Misc
```

---

# Coding Standards

Atlas follows modern Python practices.

### Type Hints

Use type hints whenever possible.

```python
def compile_profile(profile_key: str) -> dict[str, Any]:
```

---

### Pure Functions

Prefer deterministic, side-effect-free functions.

Good

```python
def classify(profile):
    ...
```

Avoid hidden global state.

---

### Explicit Returns

Never return ambiguous values.

Preferred

```python
{
    "success": True,
    "warnings": [],
    "errors": []
}
```

Avoid

```python
None
```

---

### Defensive Programming

Compiler and service boundaries should fail gracefully.

Unexpected conditions should return structured diagnostics instead of crashing.

---

# Architectural Rules

Before writing code, determine where it belongs.

## Compiler

Produces deterministic intelligence.

Examples:

- identity
- temporal
- graph
- topology
- resonance
- fingerprint
- classification

---

## Services

Interpret compiled intelligence.

Examples:

- profile report
- graph intelligence
- temporal intelligence
- narrative
- evidence

---

## Atlas AI

Synthesizes multiple services into executive summaries.

Atlas AI never creates deterministic intelligence.

---

## Dashboard

Displays information.

The dashboard should never calculate intelligence.

---

## Research

Consumes canonical payloads to generate hypotheses and analyses.

Research must never modify canonical profiles.

---

# Canonical Payload

The canonical artifact is:

```text
profile.payload.json
```

Every new feature should consume this payload.

Do not introduce new competing profile formats.

---

# Legacy Compatibility

Legacy artifacts remain for migration and compatibility.

Examples:

```text
profile.acf.json

identity_stack.json

profile_summary.json

profile_interpretation.json
```

New features should not depend on them.

---

# Tests

Every contribution should include appropriate tests.

Run the complete suite before submitting:

```bash
pytest
```

A passing test suite is required.

---

# Validation

Run the dashboard audit:

```bash
python scripts/audit_dashboard_modernization.py
```

Expected result:

```text
needs_work: 0
```

If new dashboard pages are added, update the audit script accordingly.

---

# Compiler Verification

Verify the canonical compiler:

```python
from atlas.compiler.canonical_profile_compiler import compile_canonical_profile

compile_canonical_profile(
    "example_profile",
    force=True,
)
```

Expected outcomes:

- success == True
- graph compiled
- topology compiled
- resonance compiled
- fingerprint compiled
- classification compiled

---

# Documentation Requirements

If your contribution changes architecture, schema, or methodology, update the relevant documentation.

Potential documents include:

- README.md
- ARCHITECTURE.md
- PIPELINE.md
- CANONICAL_SCHEMA.md
- DEVELOPMENT_RULES.md
- ARCHITECTURE_RULES.md
- METHODOLOGY.md
- ROADMAP.md

Documentation is considered part of the codebase.

---

# Pull Request Checklist

Before opening a pull request, confirm:

- [ ] Code follows the canonical architecture.
- [ ] No duplicate logic has been introduced.
- [ ] No new compilation path has been created.
- [ ] Services consume rather than compute.
- [ ] Dashboard remains presentation-only.
- [ ] Tests pass.
- [ ] Dashboard audit passes.
- [ ] Documentation has been updated where necessary.

---

# Code Review Principles

Reviewers should evaluate:

- Architectural correctness
- Determinism
- Simplicity
- Maintainability
- Explainability
- Documentation
- Test coverage

Functionality alone is not sufficient for approval.

---

# Design Principles

Atlas favors:

- Explicit over implicit
- Deterministic over probabilistic
- Composition over duplication
- Simplicity over cleverness
- Evidence over assumption
- Stable interfaces over rapid churn

When faced with multiple implementation options, choose the one that:

- introduces fewer moving parts,
- minimizes dependencies,
- preserves the canonical pipeline,
- and is easiest to explain to another developer.

---

# Reporting Issues

When opening an issue, include:

- Atlas version
- Operating system
- Python version
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages or stack traces
- Relevant logs or screenshots

The more reproducible an issue is, the faster it can be resolved.

---

# Feature Requests

Feature requests should describe:

- the problem being solved,
- the proposed solution,
- how it fits within the canonical architecture,
- and why it should exist in Atlas.

Requests that introduce duplicate pipelines or violate architectural rules are unlikely to be accepted.

---

# Community Expectations

Contributors are expected to:

- be respectful,
- welcome constructive feedback,
- prioritize architectural integrity,
- and collaborate openly.

Technical disagreements should be resolved through evidence, documentation, and reproducible reasoning rather than preference.

---

# Final Note

Atlas is intended to be a long-lived platform.

Every contribution should leave the codebase:

- cleaner than it was found,
- easier to understand,
- better documented,
- and more deterministic.

If future contributors can understand your work without reverse engineering it, you've contributed well.

> **Build with clarity. Preserve determinism. Strengthen the platform.**