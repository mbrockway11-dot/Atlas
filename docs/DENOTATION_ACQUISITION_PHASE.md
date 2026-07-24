# Representation 1E — Acquisition Phase

**Status:** architecture frozen · **Next change:** caused by evidence entering
the system, not by more abstraction

The admission methodology has been tested against three materially different
systems, and each produced a **different** decomposition — strong evidence the
governance architecture discovers system structure rather than imposing a
template:

```text
numerology  computation + sourced interpretation                    2 layers
gematria    orthography + transliteration + values + equivalence
            + denotation                                            6 layers
vedic       astronomical frame + chart derivations + traditional
            rules + denotation                                      8 layers
```

No further architectural work is required to explain the current result. The
next meaningful change should be **evidence entering the system**.

---

## Frozen truth

```text
Kamea      denotation available          (direct measurement)

Numerology computation available
           denotation unavailable         (acquisition-blocked)

Gematria   Hebrew identity available      (Unicode standard)
           value method unavailable
           evaluation unavailable
           equivalence unavailable
           denotation unavailable

Vedic      some calculations reproducible in isolation
           coordinate authority unavailable   (ayanamsa unlicensed)
           downstream interpretation unavailable
```

And therefore:

```text
concordance_ready == False
```

1E-A cannot run: concordance needs two denoting systems and has one (Kamea).
This is a statement about the state of the evidence, not about implementation
progress.

---

## Data-level laundering rules, complete

Each system now enforces provenance at the point a result is serialized, not
only at import:

- **Gematria** — a numeric total carries both the orthography standard hash
  and the value method hash, or it is not serialized.
- **Vedic** — a sidereal quantity (longitude, nakshatra, sign, divisional,
  dasha) carries the ayanamsa choice hash, ephemeris input hash and provider
  version, or it is not serialized. The ayanamsa offset is computed and
  swisseph-verified; **selecting** a scheme is a school claim, and no scheme
  is admitted.

These are the feed-forward invariant applied to data. Combined with the
import-level lattice test and the interpretation quarantine, an unprovenanced
meaning cannot enter a 1E result by any route the tests cover.

---

## The three live evidence fronts

```text
1E-N-SOURCE          verified numerology passages + construct equivalence
1E-G-VALUE-SOURCE    one verified Hebrew value method
1E-V-SOURCE          ayanamsa, house, dasha, dignity/yoga, denotation
```

Vedic acquisition is subdivided, and **SOURCE-A is upstream** — it must admit
before the others can produce admitted output:

```text
1E-V-SOURCE-A   ayanamsa and house-system authority   ← blocks B and C
1E-V-SOURCE-B   nakshatra, divisional, and dasha rules
1E-V-SOURCE-C   dignity, yoga, and denotational interpretation
```

---

## Recommended acquisition priority

**Gematria's value method first.** It has the narrowest evidence requirement
and the shortest path to a genuinely licensed new capability:

```text
verified source copy → one value table → licensed Hebrew numeric evaluation
```

That still creates no denotation, but it would be the **first non-Kamea
symbolic system to move from licensed identity into licensed traditional
computation** — the first evidence-driven capability gain in the whole
denotation system.

- **Numerology** needs enough passages to establish construct equivalence and
  denotation — the widest requirement.
- **Vedic** needs several interdependent authorities, gated behind SOURCE-A.
- **Gematria** needs one tightly bounded value source.

---

## Standing rule

No further code change should manufacture evidence. The architecture is
complete through classification and provenance enforcement for all three
interpretive systems; what remains is acquisition. The next commit that adds a
denotation should be one that ingests a verified source, not one that adds an
abstraction.
