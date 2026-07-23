# Validation Cohort Policy

Rules for which profiles may enter which experiment, and what every result
must report about its cohorts. The purpose is to stop data-completeness from
becoming a hidden confounder.

---

## The fact that drives everything

**Identity vectors are derived from the name alone. Birth data does not enter
them.**

Verified in `tests/test_identity_vectors_do_not_depend_on_birth_data`: the
same name with full birth data, with wildly different birth data, and with no
birth data at all produces byte-identical vectors.

Three consequences, and they are not optional:

1. **Birth-permutation experiments cannot use identity vectors as their
   outcome measure.** Shuffling birth dates and comparing identity-vector
   similarity measures exactly zero, by construction. It is not a weak
   control — it is a no-op, and reporting it as a null result would be
   misleading.
2. **Unknown-birth profiles are fully valid subjects** for any
   identity-vector experiment. There is no imputation and no degradation.
3. **Birth data reaches only the temporal/CSS layer.** Any experiment about
   birth data must measure something from that layer, and must state so.

If `test_identity_vectors_do_not_depend_on_birth_data` ever fails, this
document is wrong and must be rewritten before any affected experiment runs.

---

## Birth-data status

Every ACF records its status under `identity.birth_data_resolution`, decided
by one resolver (`atlas.birth.resolve_birth_data`) rather than by each caller
guessing:

| Status | Meaning |
|---|---|
| `known` | date, time, and place all present |
| `partial` | at least one present, at least one missing |
| `unknown` | none present |

Placeholders in the corpus — `""`, `"Unknown"`, `"N/A"`, `"none"`, `"-"`,
`"?"` — count as missing, never as data.

Current corpus: **2,122 compiled profiles, of which 205 (9.7%) are
unknown-birth.** That group is not randomly distributed — it skews toward
figures with poor biographical records — so it cannot be treated as a random
subsample.

---

## Eligibility by experiment type

| Experiment | Eligible cohort | Notes |
|---|---|---|
| Name variants / name permutation | any status | The outcome is name-derived; birth completeness is irrelevant. |
| Population similarity, nearest-neighbour | any status | Report completeness breakdown alongside results. |
| Random-pair baseline | any status | Must mirror the composition of whatever it is a baseline for. |
| Birth-data experiments | `known` only | And must measure a temporal/CSS outcome, not identity vectors. |
| Partial-birth studies | `partial` only | Separate cohort; never merged into `known`. |
| Relationship / family / collaborator | any status | Match or stratify controls on completeness. |

---

## Control matching

A control group must match its positive group on anything that could produce
the effect by itself:

- **birth-data status** — always, when the outcome could depend on it
- **entity type** — never compare a person against a civilization
- **name length and token count** — name-derived features scale with the
  input, so a long-name positive group against a short-name control measures
  name length
- **era** — where the corpus is era-skewed

A result that beats a naive random control but not a matched control has not
demonstrated structure. Report both.

---

## Required reporting

Every experiment result records:

```text
complete birth profiles      (status = known)
partial birth profiles       (status = partial)
unknown birth profiles       (status = unknown)
imputed-feature count        (0 for identity-vector experiments)
entity-type breakdown
positive cohort size
control cohort size
```

Plus the runtime provenance that ties the result to exact data:

```text
feature_schema_hash
source_manifest_hash
artifact schema version
compiler version
normalization mode
random seed
```

---

## Determinism guarantees these rest on

Verified in `tests/test_birth_resolution_determinism.py`:

- the same profile compiles to identical vectors on any date
- unknown-birth profiles are as deterministic as known-birth ones
- wall-clock time appears in exactly one field, `metadata.created_utc`, which
  is provenance and never feeds a vector
- `build_transit_chart` refuses to default to today
- transits compiled into CSS use a fixed reference epoch
  (`transit-fixed-reference-epoch-v1`) and are labelled
  `placeholder_fixed_epoch` — they are geometry, not current transits, and
  must never be interpreted as evidence about the present

---

## Why the birth policy is not in the feature-schema hash

Because birth data provably does not affect identity vectors, hashing
`BIRTH_RESOLUTION_VERSION` into the feature schema would invalidate all 2,122
artifacts on every policy tweak, for a dependency that does not exist —
asserting a false relationship in the one place the system trusts to be
truthful about relationships.

The guard is the test named above. If birth data ever starts feeding vectors,
that test fails, and the policy version must then be added to
`atlas.compiled.feature_schema` so affected artifacts rebuild.
