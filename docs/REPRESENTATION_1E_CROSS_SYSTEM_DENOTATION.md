# Representation 1E — Cross-System Denotational Audit

**Status:** open · **Type:** design + characterization, not hypothesis testing
· **Blocked by:** none — [1D](TEMPORAL_1D_KAMEA_AUDIT.md) closed at R1-G ·
**Blocks:** all historical-anchor validation

1A–1D asked whether each representation is *mechanically valid* and
*statistically safe*. None of that establishes whether numerology, gematria,
Kamea geometry, and Vedic astrology are even expressing the **same object**
when applied to one subject. 1E is the missing bridge.

```text
mechanical validity          <- 1A-1D, done for Kamea/temporal
      ↓
denotational concordance     <- 1E, this milestone
      ↓
behavioral correspondence    <- 1E-B
      ↓
historical-event validation  <- only after all of the above
```

The governing distinction:

> Mechanical agreement is not denotational agreement, and denotational
> agreement is not empirical validity.

---

## The question

Not "do the systems produce the same numbers or shapes" — they will not. But:

> When the systems purport to denote the same characteristic, event,
> relationship, or behavior, do their independently generated expressions
> agree at a shared semantic level?

```text
identity and birth inputs
      ↓
independent system expressions      <- frozen before any translation
      ↓
denotational normalization          <- via frozen dictionaries only
      ↓
cross-system agreement audit        <- with null and contradiction controls
      ↓
historical anchors                  <- last, and only as confirmation
```

---

## Independence through generation — the load-bearing constraint

No system may determine another system's labels. For one subject, each system
generates its expression **frozen** before any translation into a shared
vocabulary:

```text
Numerology  name/date quantities and derived characteristics
Gematria    orthographic values, reductions, correspondences
Kamea       raw paths, deduplicated paths, translation-normalized shapes
Vedic       grahas, rāśis, bhāvas, nakṣatras, aspects, dignities, daśā/transit
```

Only then are they translated into the common comparison vocabulary. The
failure this prevents is circular self-confirmation:

> interpreting a Kamea shape as "Saturnian restraint" **because Saturn's
> square produced it**, then declaring agreement with a Saturn-heavy chart.

The architecture enforces this structurally: a `SystemExpression` records the
system that produced it and is immutable, and the translation layer may read
only the frozen expression plus a frozen dictionary — never the other systems'
outputs, and never the subject's outcome.

This constraint has teeth against Kamea specifically, given 1D. R1 denotes
**structural** properties (repetition, concentration, cyclicity, stability vs
transition) and nothing symbolic by construction. The 1D result that the
square's only geometric operation is a *subtractive coarsening* means Kamea
may not be read as carrying planetary symbolism it does not encode — the
planet supplied the square, not a meaning.

---

## Four kinds of agreement, tested in order of interpretive load

### 1. Referential — are they even about the same object?

Natal identity vs current transit state; person-level characteristic vs
event-level condition; enduring tendency vs temporary activation. A natal
numerology expression may **not** be compared with an event transit unless the
enduring↔temporary relationship is explicitly defined first. Mismatched
reference is `not_comparable`, not `contradictory`.

### 2. Structural — analogous formal properties?

Repetition, symmetry, concentration, fragmentation, polarity, centrality,
cyclicity, stability vs transition. **The safest comparison**: least
interpretive symbolism, and the one Kamea can enter honestly. 1E starts here.

### 3. Symbolic — comparable symbolic domains?

Restraint, expansion, conflict, communication, attraction, dissolution,
initiation. These mappings come **only** from frozen source dictionaries, not
from interpretation after seeing a subject. A system with no frozen dictionary
for an axis contributes nothing on that axis — silence, not a guess.

### 4. Behavioral — a jointly implied observable tendency?

The strongest claim, tested **last**, in 1E-B. Requires a predefined
behavioral ontology and observable coding rules.

---

## Agreement is not identical polarity

Different systems may describe different roles in one configuration — strong
constraint, repeated effort, delayed materialization — that are denotationally
compatible without being identical. So agreement is a **relation**, not a
binary:

```text
equivalent       same denotation, same polarity
compatible       consistent, one refines or restates the other
complementary    different roles in the same configuration
contradictory    opposed denotation at a shared reference
unrelated        no shared semantic content
not_comparable   different reference class; comparison undefined
```

Reducing this to match/no-match would let a broad word like "change" or
"power" make nearly every system appear mutually confirming.

---

## The shared ontology — the most important artifact

Frozen and hashed before any real subject is examined. Four axes:

```text
domain              cognition · communication · affiliation · agency ·
                    conflict · material_organization · transformation ·
                    spirituality
dynamic             expansion · contraction · stabilization · disruption ·
                    repetition · reversal · concealment · emergence
temporal_character  enduring · developmental · periodic · acute · transitional
behavioral          initiation · persistence · avoidance · cooperation ·
                    dominance · adaptation · risk_taking
```

Each system maps into this **independently**, recording per mapping: source
basis, confidence, polarity, temporal scope, and whether the mapping is
`direct` or `interpretive`. The ontology is versioned and its hash
participates in every concordance artifact, exactly as the feature-schema and
representation hashes do elsewhere.

---

## Null and contradiction controls — agreement must not be inevitable

The audit must demonstrate that authentic pairings agree **more** than
controls do. Otherwise broad symbolic words guarantee apparent confirmation.

```text
mismatched name / birth-record pairings
shuffled system outputs
time-shifted charts
unrelated Kamea expressions
decoy semantic labels
blinded human coding where interpretive judgment remains
```

An authentic-vs-control agreement gap is the primary 1E-A result. No gap means
the concordance is an artifact of vocabulary breadth, and no symbolic claim
survives.

---

## Two stages

### 1E-A — expression concordance (no biography, no outcomes)

Do the systems' frozen expressions align internally, above controls? This is
purely about the representations.

### 1E-B — behavioral concordance

Do the systems' **preregistered shared implications** match independently
coded behavior? Requires the behavioral ontology and coding rules frozen
first.

Birth data is the ideal first cohort because it joins the layers naturally:
name → numerology/gematria; birth time+place → Vedic + R0 + Kamea R1; observed
life data → external criterion.

---

## Historical anchors are confirmation, never dictionary construction

A famous event is semantically rich, so it is trivial to reinterpret almost
any expression to fit it after the fact.

```text
PROHIBITED                          REQUIRED
historical event                    freeze each system
  ↓ notice its known meaning        freeze translation dictionaries
  ↓ reinterpret until they agree    freeze agreement rules
                                    generate expressions blind to outcome
                                      ↓ then reveal the anchor
```

---

## Order (this milestone)

1. ~~Finish the large-cohort R1 audit and classify~~ — **done, R1-G.**
2. Freeze the precise information Kamea supplies: quantized trajectory,
   repeated-visit structure, translation-normalized shape.
3. Define and freeze the shared denotational ontology.
4. Freeze independent mappings from numerology, gematria, Kamea, Vedic.
5. Run blinded cross-system concordance on birth records (1E-A).
6. Test authentic pairings against shuffled and mismatched controls.
7. Add independently coded behavioral observations (1E-B).
8. Only then apply the complete system to historical anchors.

---

## Deliverables

- [ ] Frozen, hashed shared ontology (four axes)
- [ ] Frozen Kamea denotational contribution, structural axis only
- [ ] Relation algebra (six relations) with an explicit comparability gate
- [ ] `SystemExpression` framework enforcing independence at generation
- [ ] Per-system mappings, each gated on a frozen source dictionary
- [ ] Null/contradiction control generators
- [ ] 1E-A concordance study with an authentic-vs-control agreement gap
- [ ] Behavioral ontology + coding rules (1E-B), frozen before use

Symbolic and behavioral mappings for numerology, gematria and Vedic each
require their own frozen source dictionaries. Those are preregistered work in
their own right; until a dictionary exists for a given system and axis, that
system contributes **silence** on that axis, never an interpreted guess.

---

## Entry gate for any system

Numerology established the discipline every later system inherits. See
[the source policy](NUMEROLOGY_SOURCE_POLICY.md) and
[the acquisition gate](NUMEROLOGY_SOURCE_ACQUISITION.md).

> **A denotational system is not eligible because it can produce meanings. It
> is eligible only when the exact evidence state that licensed those meanings
> remains reproducible, synchronized and independently auditable.**

Concretely, a system entering 1E must supply:

- a declared tradition boundary, with any historical claim stated or disowned
- layered bibliographic identity — work, manifestation, source copy, passage
- a construct-equivalence verdict per mapping; a shared phrase is not evidence
- semantic granularity, with only direct denotation eligible for 1E-A
- derived capability flags, hash-synchronized to the corpus that produced them
- quarantine of any pre-existing unprovenanced interpretation path

It may **not** bypass its own missing sources by reaching for a synthesis
vocabulary already in the tree.

### Current entry status

| system | state |
|---|---|
| Kamea | **admitted** — structural axis only, direct measurement, no source needed |
| numerology | architecture complete, **acquisition pending** (baseline `07af099`) |
| gematria | classified, repaired, identity admitted; value table **evaluated** (P1) |
| Vedic | classified; ayanāṃśa provenance **investigated** (P1) |

1E-A cannot run yet: concordance needs two eligible systems and has one.

---

## Milestone: Representation 1E complete

The architecture is complete. Declared against a fixed checklist:

- [x] Provenance architecture stable (tiers, feed-forward lattice, laundering)
- [x] Capability gates stable (derived, hash-synchronised, fail-closed)
- [x] Acquisition protocol stable (11 stages, each mapped to an enforcing gate)
- [x] At least one real source evaluated end-to-end — Gesenius §5k and CLDR
      against the six numeral requirements ([table](GEMATRIA_P1_NUMERAL_EVALUATION_TABLE.md))
- [x] The framework changed in response to evidence at least once — the P1
      integration test reclassified the gematria value table from primary-text
      method to normative computation, and re-scoped its acquisition target
- [x] Remaining work is primarily source acquisition, not framework design

**1E has stopped asking for itself.** Every open thread is now a source event:
read Chrisomalis/Gandz (gematria provenance), inspect the Academy of the Hebrew
Language rules (value-table authority), obtain the Calendar Reform Committee
report / Rāṣṭrīya Pañcāṅga ([Vedic ayanāṃśa authority](JYOTISHA_P1_AYANAMSA_PROVENANCE.md)),
acquire one Juno Jordan work (numerology). Future commits should read
"admitted source", "rejected source", "coverage evaluation", "historical
finding" — research outputs, not framework changes.

### First cross-domain result

The same question — *what establishes this construct?* — already gives
opposite-shaped answers: gematria's value mapping is **convention-shaped**
(anonymous, emergent, no authority identified), while the Lahiri ayanāṃśa is
**authored / standard-shaped** (a named individual and an official governmental
standard). The doctrine-vs-convention model discriminates across domains — a
working model on two data points, not yet a settled classification.
