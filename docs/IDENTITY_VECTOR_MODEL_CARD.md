# Atlas Identity Vector — Model Card

Status: **Identity Validation 2A closed.** Evidence below is from the
full-corpus baseline, perturbation and invariance suites, metric ablation,
the variant pilot, and the held-out H1 confirmatory study.

Corpus: 2,122 compiled profiles · 2,250,381 unordered pairs · schema
`atlas.compiled.identity-vectors.v3`.

---

## What the vector encodes

**Atlas identity vectors model Latin orthography, not names in general.**

The encoder's effective alphabet is `A B C ... Z`. Every other character is
deleted before encoding. That is an architectural property, not a tuning
parameter, and it bounds every claim below: what the model encodes is
structural properties of the **ASCII-letter skeleton of a name string**, and
nothing else.

Each profile is 3 ciphers × 7 planets × 17 graph features = 357 dimensions,
derived from the name's Kamea identity graph.

**Birth data does not enter identity vectors.** The same name with full birth
data, with wildly different birth data, and with none at all produces
byte-identical vectors (`tests/test_identity_vectors_do_not_depend_on_birth_data`).
Birth and date information reaches only the temporal/CSS layer.

---

## What is invariant

Measured, not assumed (`tests/test_birth_resolution_determinism.py`,
invariance suite):

| Transformation | Behaviour |
|---|---|
| Case (upper/lower) | **exactly invariant** |
| Leading/trailing/repeated whitespace | **exactly invariant** |
| Punctuation, hyphens, apostrophes | **exactly invariant** |
| Compilation date / wall-clock time | **exactly invariant** |
| Diacritics | *variant* — see the scope boundary below |
| Token order | weakly variant (~0.973) |

The encoder sees **A–Z only**. Everything else is discarded.

---

## ⚠️ Scope boundary: non-A–Z characters are silently dropped

`english_ordinal_sequence` keeps only characters present in its A–Z map. This
has consequences that must be understood before the model is applied to any
non-English corpus:

- `Kurt Gödel` and `Kurt Gdel` are **identical** (cosine 1.0). The `ö` is not
  folded to `o`; it is deleted.
- Two entirely different Cyrillic names score **1.0**. Two different Han
  names score **1.0**. All their characters are dropped, so the vectors are
  degenerate and mutually indistinguishable.
- Accent-stripping is therefore a character *insertion* from the encoder's
  view, not a substitution.

**Current corpus exposure is limited**: 195 of 2,122 names (9.2%) lose at
least one character; none loses more than half; none encodes to nothing. So
this is a latent boundary rather than present corruption — but it makes the
model **unsuitable for non-Latin scripts as written**.

---

## Known structural confounders

| Variable | Correlation with similarity |
|---|---|
| Absolute name-length difference | Pearson −0.55, Spearman −0.43, **partial −0.63** |
| Absolute token-count difference | Pearson −0.24 |

A structural regression explains **45%** of score variance. Matching on
length and token strata removes ~35%, leaving **65% of variance unexplained
by name shape**.

Score distribution is severely compressed: mean **0.959**, σ **0.014**, and
the 0.1st percentile is still 0.881. A raw score of 0.98 is only the **97th
percentile** — unremarkable.

---

## Supported uses

- Deterministic, reproducible structural fingerprinting of Latin-script names
- Population-relative comparison **when reported with a percentile**
- Corpus-scale exploratory analysis (all pairs computable in ~0.11 s)

## Unsupported uses

- **Same-person variant recognition.** Not demonstrated in any class.
- **Identity inference about people.** The vector describes a string.
- **Non-Latin-script names.** The model is an ASCII encoder. Applying it to
  such names produces vectors that look valid and are meaningless.
- **Any temporal, birth-date, or astrological claim.** Those inputs are
  absent from this model.
- **Presenting a raw score alone.** Always pair with global and matched
  percentiles.

---

## Metric behaviour

Frozen decisions:

```text
canonical / production metric : cosine
secondary diagnostic          : centered_cosine
```

All five tested geometries preserve the declared invariances. Ranked by
resolution (known-identical minus known-unrelated, in population SDs):

| Metric | Resolution | Length confounder |
|---|---|---|
| cosine (canonical) | 2.38 | −0.55 |
| centered_cosine | 3.69 | −0.35 |
| standardized_euclidean | 4.39 | −0.69 |

**Centered cosine was not adopted.** Its better geometric resolution did not
translate into variant discrimination in the pilot, and it reorders the
population substantially (Spearman 0.75; only 5/10 of the top 10 and 43% of
the top 1% shared). Metric search is closed to avoid turning selection into a
multiple-testing channel.

---

## Nearest-neighbour limitations

Nearest-neighbour output is **exploratory, not identity evidence**.

Of the 50 most extreme pairs, 24 remain extreme under centering; 13 remain
**unexplained** by morphology, letter overlap, or stratum position. Those 13
are dominated by very long names — mean 32.5 characters against a corpus mean
of 13.9 — consistent with feature saturation in long Kamea graphs, with
character-dropping a secondary contributor (77% lose ≥1 character).

Any user-facing neighbour result must carry: global percentile, matched
percentile, metric agreement, morphology summary, and explanation status
(`explained_surface_similarity`, `explained_feature_collision`,
`metric_sensitive`, `unexplained`). **An unexplained neighbour must not be
presented as a meaningful relationship.**

---

## Validation evidence

| Study | Result |
|---|---|
| All-pairs baseline (2,250,381 pairs) | 0 exact collisions; all scores distinct |
| Perturbation response | Monotonic for substitution/transposition/insertion/deletion; no positional weighting |
| Synthetic decomposition (n=300) | Real unrelated names score **no higher** than synthetic strings of matched morphology (\|d\| ≤ 0.38) |
| Variant pilot (152 pairs, 4 classes) | No class separates from its conditioned null, either metric |
| **H1 confirmatory (held out, n=117)** | **H1 contradicted.** Diacritic variants score *significantly lower* than matched controls (AUC 0.248, d = −0.98) |

### Headline conclusion

> Under transformation-conditioned controls, the identity-vector geometry
> does not distinguish genuine name variants from structurally comparable
> synthetic or unrelated variants. The A2 result is a significant effect in
> the direction *opposite* to the hypothesis, explained by the encoder
> deleting accented characters rather than folding them.

### Two methodological failures caught during validation

Both would have produced confident, wrong conclusions:

1. **Mismatched null.** Comparing length-changing variants against a
   length-preserving control produced an apparent d = −1.65. Matching the
   null on length as well moved it to −0.16. The effect was the control, not
   the model.
2. **Non-directional verdict.** The confirmatory runner initially reported
   `H1_supported` because an AUC interval excluded 0.5 — from *below*. A
   significant effect in the opposite direction is not support.

---

## Reproducing

```bash
.venv/Scripts/python.exe scripts/run_validation_experiment.py \
    configs/validation/identity_random_pair_baseline_v1.yaml
.venv/Scripts/python.exe scripts/audit_false_neighbors.py
.venv/Scripts/python.exe scripts/run_variant_pilot.py
.venv/Scripts/python.exe scripts/run_h1_confirmatory.py
```

Every artifact records the feature-schema hash, source-manifest hash,
compiler version, git commit and dirty state. Re-running an experiment with
the same config reproduces its outputs byte-for-byte.

---

## Status of open questions

- **Identity metric search: closed.** Do not reopen without a new theory or
  dataset.
- **H2 (nicknames) / H3 (token-reducing): scope findings.** Effects are
  ~0 against correct controls; larger samples would likely confirm weak
  effects rather than reveal strong ones.
- **H4 (aliases): needs source verification** and separation by structural
  overlap before its mean has a coherent interpretation.
- **Non-Latin script handling: open defect**, tracked as
  [Identity Runtime 3.0 — Unicode Name Encoding](IDENTITY_RUNTIME_3_UNICODE.md).
  The identity branch is frozen until that milestone is addressed; it is
  architectural, while the temporal branch's open questions are
  methodological, so the two proceed independently.
