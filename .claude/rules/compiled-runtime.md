---
paths:
  - "src/atlas/compiled/**/*.py"
  - "src/atlas/services/*.py"
  - "src/atlas/ive/**/*.py"
---

# Compiled runtime rules

## The invariant

Runtime reads compiled artifacts. It does not walk the ACF corpus. Any change
that reintroduces "load every ACF" per request defeats the whole layer — the
corpus is ~5.4 GB and a warm comparison currently costs about 5.6 ms.

When an artifact cannot be resolved, raise `CompiledRuntimeError`. Never fall
back to reparsing the corpus: a silent fallback turns a millisecond request
into a minute-long one with no visible failure.

## Freshness

Content hashing decides staleness, never mtime — mtimes change on copy, sync,
branch switch, and restore without the content changing. `compiled_artifact_is_current`
compares size first as a cheap reject, then SHA-256.

An artifact whose source ACF is gone is **orphaned**, not current. Do not
report it as current.

## Feature-schema and content hashing

Bump `NORMALIZATION_VERSION` whenever any mode's numerical behaviour changes,
even if no field moves — it feeds the feature-schema hash, which is what makes
an algorithmic change invalidate artifacts. Same for `IVE_VERSION` on builder
changes.

`content_hash` must cover semantic content only. Never add a timestamp, git
field, platform, or command to it: that would break the "same source, same
semantics -> same hash" property it exists to provide.

## Schema handling

- current schema → load
- known older schema → rebuild from source
- unknown/newer schema → reject, do not guess
- damaged → rebuild from source
- source missing → report failure

## Normalization parity

`normalize_feature_from_statistics` must stay numerically identical to
`atlas.ive.normalizer.normalize_feature_value` for the same population.
Not "close" — equal.

- `percentile` needs the exact sorted distribution (rank-based)
- `zscore` uses `pstdev`, not sample stdev
- both return exactly `0.5` when the group is missing or degenerate,
  matching the vector path's self-calibration fallback

Statistics are keyed by **cipher × planet**, then feature.

After any change here, run:

```bash
.venv/Scripts/python.exe -m pytest tests/test_compiled_runtime_parity.py -q
```

## Adding an artifact type

Frozen slotted dataclass, `to_dict`/`from_dict`, explicit schema-version
string, `from_dict` rejects unsupported versions and validates declared counts
against actual contents. Persist atomically with sorted keys and a trailing
newline. Tie derived artifacts to their corpus with a source-manifest hash.
