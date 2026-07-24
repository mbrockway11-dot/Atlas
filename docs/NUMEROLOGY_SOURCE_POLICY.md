# Numerology Source Policy

**Status:** frozen protocol · **Governs:** every numerology dictionary version
· **Part of:** [Representation 1E](REPRESENTATION_1E_CROSS_SYSTEM_DENOTATION.md)

Numerology is the **first genuinely interpretive** system to enter 1E. Kamea
entered through direct structural measurement — its claims are computed from a
path's geometry by fixed rule, no source required. Numerology's claims will
rest on what a tradition *says a number means*, which is provenance, not
measurement.

So the rules by which a numerology source is allowed to speak are frozen
**before any meaning is written down**. Otherwise the first interpretive system
silently determines the ontology, and every later system's apparent agreement
is measured against numerology's unexamined choices. This protocol is the
template gematria and Vedic astrology will inherit.

The governing rule:

> Existing vocabulary may supply identifiers; it may not supply provenance.

The interpretive packages already in the tree (`archetypes`,
`structural_roles`, `symbolic_behavior`, the synthesis adapters) may suggest
*which* ontology term a mapping targets. They may never be the *evidence* for
it. An ontology term is licensed only when a numerology source independently
supports it.

---

## Three layers, kept apart

```text
NumerologyExpression      computation only — knows nothing of the ontology
NumerologyDictionaryEntry source-licensed denotation — knows nothing of a subject
DenotationClaim           one entry applied to one expression, by exact key
```

The expression layer does not import the ontology. The dictionary layer does
not import a subject. The claim assembler is the only place they meet, and it
may combine them only through an exact licensed key.

---

## Tradition boundary

Each dictionary version represents **exactly one** numerological tradition,
named explicitly. The following are never silently blended into one
authoritative mapping:

- Pythagorean name values
- Chaldean values
- master-number rules (11, 22, 33)
- compound-number meanings
- modern personality descriptions
- unrelated esoteric correspondences

Different traditions may become different dictionary versions. They do not
merge. A `tradition` identifier is part of every entry's licensing key.

---

## Computational boundary

Only quantities the code **actually computes** may receive dictionary entries.
If the implementation produces a number but not a named construct, the audit
may not invent the construct afterward. The frozen expression set is whatever
`NumerologyExpression` deterministically generates, and nothing else is
addressable.

A generic entry for "the number 4" does **not** automatically apply to every
quantity. A reduced value may denote different things as a life-path number, a
name total, an intermediate sum, or an incidental arithmetic result. An entry
is keyed to a specific quantity unless the sources explicitly support
quantity-independent interpretation, which is itself a source claim to be
cited.

---

## Reduction policy (part of the expression, not preprocessing)

Frozen per dictionary version and recorded in a `reduction_policy` identifier:

- treatment of 11, 22, 33 and any other unreduced ("master") values
- treatment of zero
- treatment of punctuation and whitespace
- transliteration rules
- handling of alternate names
- date normalization
- whether compound values remain available alongside reduced values

The `NumerologyExpression` carries its full `reduction_trace`, so two versions
with different reduction rules produce distinguishable expressions and cannot
be silently conflated.

---

## Source admissibility

Every mapping requires:

- an identifiable source
- a specific passage or table
- an attributable tradition
- enough context to distinguish direct meaning from later interpretation
- **no dependence** on the Kamea, Vedic, or behavioral result for the same
  subject

> A source saying "4 means stability" can license a constrained mapping. A
> synthesis layer saying "4 is stable because this subject's Kamea was
> stationary" cannot.

---

## Conflict policy

When admissible sources disagree, the disagreement is represented explicitly —
never reconciled informally. Permitted outcomes:

- **consensus** — sources agree; one mapping
- **source-specific** — each source keeps its own mapping
- **conflicting** — sources oppose; recorded as such, licenses no agreement
- **insufficient** — too little evidence to map
- **none** — no mapping

Silence is preferable to forced consensus. A conflicting or insufficient
verdict produces no `DenotationClaim`.

---

## Smallest defensible dictionary

The first version does not try to fill all four axes. It admits only mappings
the sources clearly support — likely `dynamic`, some `temporal_character`, a
limited set of `domain`. `behavioral_manifestation` stays **empty** unless a
source makes a specific, operationalizable claim.

A sparse dictionary is a strength: it gives the null controls room to
distinguish authentic agreement from vocabulary breadth. The first dictionary
should contain fewer entries than expected.

---

## Negative guarantees (tested)

Numerology may not inherit meaning from:

- Kamea body identity or shape labels
- Vedic graha names
- `archetypes`, `structural_roles`, `symbolic_behavior`
- any subject biography or historical outcome

Tests assert these at the architecture level: the expression layer cannot
import the ontology, and a claim cannot be constructed without citing a
dictionary entry whose provenance is a numerology source.

---

## Readiness for 1E-A

The numerology dictionary is ready only when all hold:

1. The computational expression is deterministic and versioned.
2. Tradition and reduction rules are frozen.
3. Every denotation has source provenance.
4. Unsupported quantities produce silence.
5. Conflicting sources remain explicit.
6. Authentic agreement exceeds all frozen controls.
7. The gap is not produced by vocabulary breadth.
8. No single mapping or compatibility edge dominates the result.
9. The result reproduces without opening synthesis or biography data.
10. Dictionary, ontology, compatibility-table and expression hashes all enter
    the artifact hash.

Items 1–5 and 10 are architectural — this commit. Items 6–9 are the pilot,
after a source-backed dictionary exists.

---

## Implementation order

1. **This commit:** schemas and gates only — no number meanings.
   `NumerologyExpression`, `NumerologyDictionaryEntry`, provenance schema,
   tradition and reduction identifiers, dictionary hash, claim-construction
   gate, conflict/silence behavior, cross-system-inheritance tests.
2. **Separate commit:** a very small source-backed dictionary.

The separation is deliberate: it keeps architectural change distinguishable
from interpretive addition in the history.
