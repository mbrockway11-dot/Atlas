# Identity Runtime 3.0 — Unicode Name Encoding

**Status:** open · **Type:** architectural · **Blocks:** the identity branch
· **Does not block:** temporal validation

---

## The defect

`atlas.ciphers.english_ordinal_sequence` builds its sequence with

```python
[ENGLISH_ORDINAL[c] for c in normalized if c in ENGLISH_ORDINAL]
```

Every character outside the A–Z map is silently discarded. There is no
warning, no status field, and no failure — the encoder returns a vector that
is structurally valid and semantically empty.

Atlas is therefore a model of **Latin orthography**, not of names.

### Demonstrated consequences

```text
Kurt Gödel      vs  Kurt Gdel          cosine 1.000   (ö deleted, not folded)
Лев Толстой     vs  Пётр Чайковский    cosine 1.000   (all characters dropped)
毛澤東           vs  孔子                cosine 1.000   (all characters dropped)
```

Two entirely unrelated non-Latin names are **indistinguishable**, because both
encode to the same degenerate sequence.

### Current corpus exposure

| Measure | Count | Share |
|---|---|---|
| Profiles losing ≥1 character | 195 / 2,122 | 9.2% |
| Profiles losing >50% of characters | 0 | 0% |
| Profiles encoding to nothing | 0 | 0% |

The present corpus is nearly all Latin script, so this is a **latent
boundary rather than active corruption**. It becomes active the moment a
non-Latin name enters the corpus.

### Downstream effects already measured

- The H1 confirmatory study was **contradicted** (AUC 0.248, d = −0.98)
  because accent-stripping is a character *insertion* from the encoder's
  view, not a substitution — and a null matched on raw string length cannot
  see that.
- Character loss is a secondary contributor to the unexplained extreme
  neighbours (77% of those pairs lose ≥1 character).

---

## The rule this milestone must establish

> Silent deletion is the only behaviour that must disappear.

Every input must either be **encoded correctly** or **fail loudly**. A vector
that looks valid for an unsupported script is the worst possible outcome,
because nothing downstream can detect it.

---

## Goals

1. **Normalization policy** — a decided, versioned choice between NFC and
   NFKC, applied before any cipher sees the string.
2. **Script detection** — identify the writing system(s) present in a name
   and record them on the profile.
3. **Transliteration policy** — whether, when, and by which standard a
   non-Latin name is romanized; transliteration must be recorded as a
   transformation, never presented as the original.
4. **Native-script support** — extend the cipher maps, or explicitly decline
   to.
5. **Explicit unsupported-script handling** — a profile whose script is
   unsupported must carry that status and must not yield a silently
   degenerate vector.
6. **Versioned alphabet policy** — the effective alphabet becomes part of the
   feature-schema hash, so changing it invalidates the artifacts it affects.

---

## Acceptance criteria

- [ ] No input path silently discards characters
- [ ] Coverage is measured and recorded per profile (`encoded_characters` /
      `total_characters`)
- [ ] Unsupported scripts produce an explicit status, not a degenerate vector
- [ ] Two distinct non-Latin names never produce identical vectors
- [ ] The alphabet policy version participates in the feature-schema hash
- [ ] Corpus recompiles cleanly with per-profile coverage reported
- [ ] The model card's scope section is rewritten against the new behaviour

---

## Sequencing note

This is deliberately **not** being fixed before temporal validation.

The Unicode issue is architectural; the temporal branch's open questions are
methodological. They are independent, and reopening the encoder now would
invalidate the Identity 2A evidence base — which is worth preserving intact,
since its value lies precisely in having been produced under a fixed
encoder.

```text
Identity branch     frozen at 2A
Temporal branch     begins independently
Unicode redesign    future milestone
```

Any re-run of the identity experiments after this milestone lands should be
treated as a **new evidence base**, not a continuation of 2A, because the
feature-schema hash will have changed and the vectors will not be comparable.
