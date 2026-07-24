# Atlas

Structural identity analysis research framework. Python 3.14, `src/` layout,
package name `atlas`.

## Interpreter — read this first

**Use `.venv/Scripts/python.exe`. A bare `python` is the wrong interpreter.**

The system Python lacks `swisseph` (and other native deps), so `atlas.temporal`
fails to import and roughly 44 test modules die at collection. That is an
environment problem, not a code problem — do not start debugging imports.

```bash
.venv/Scripts/python.exe -m pytest -q          # full suite (~4 min)
.venv/Scripts/python.exe -m pytest tests/test_compiled_calibration.py -q
.venv/Scripts/python.exe scripts/<name>.py     # any script
```

`pytest` gets `src/` on the path from `pyproject.toml` (`pythonpath = ["src"]`).
A bare `python` does not — prefix `PYTHONPATH=src` if you must use one.

Baseline: **1,600 tests passing.** Any drop is a regression you introduced.

## Architecture: ACF is source, AIR is runtime

Two representations, and the distinction is load-bearing:

- **ACF** (`output/library/profiles/<key>/profile.acf.json`) — authoritative
  research representation. ~2,122 profiles, ~5.4 GB total.
- **Compiled identity vectors** (`output/compiled/`) — authoritative *runtime*
  representation. Same data, 42.5 MB (99.2% smaller).

Runtime code reads compiled artifacts. It must not walk the ACF corpus: doing
so reintroduces the multi-gigabyte parse per request that the compiled layer
exists to remove. `src/atlas/compiled/runtime.py` raises `CompiledRuntimeError`
rather than falling back to reparsing — keep it that way.

Artifact freshness is decided by **SHA-256 of the source**, never mtime — and
by the **feature-schema hash**: an artifact built against a different notion of
"feature" is stale even when its ACF is byte-identical.

Every artifact records full provenance (compiler version, git commit + dirty
state, Python, platform, command) plus a `content_hash` over semantic content
only, so two builds of the same source agree despite differing timestamps.

### The compiled layer

| Path | Role |
|---|---|
| `src/atlas/compiled/identity_vector_compiler.py` | one ACF → one artifact |
| `src/atlas/compiled/identity_vector_library_compiler.py` | batch over the library |
| `src/atlas/compiled/calibration.py` | consolidated corpus + feature statistics |
| `src/atlas/compiled/runtime.py` | what comparison services call |
| `src/atlas/compiled/index.py` | corpus index |
| `src/atlas/compiled/feature_schema.py` | what a "feature" means, hashed |
| `src/atlas/compiled/content_hash.py` | deterministic semantic hash |
| `src/atlas/compiled/health.py` | runtime health / drift detection |

```bash
.venv/Scripts/python.exe scripts/compile_identity_vectors_batch.py
.venv/Scripts/python.exe scripts/build_calibration_statistics.py
.venv/Scripts/python.exe scripts/validate_compiled_vectors.py --write-index
.venv/Scripts/python.exe scripts/benchmark_compiled_runtime.py
.venv/Scripts/python.exe scripts/compiled_runtime_health.py
```

Full rebuild order and troubleshooting: [RUNBOOK.md](RUNBOOK.md).

### Normalization

Normalization calibrates **within a comparable group: cipher × planet** (21
groups × 17 features). Statistics are not global — anything keyed only by
feature is wrong.

Modes: `raw` (the canonical default everywhere), `percentile`, `minmax`,
`zscore`. Raw is each profile's own bounded measurements — self-contained, no
population dependency. Population modes are opt-in and need calibration;
without it they collapse to 0.5. The default is locked by
`tests/test_normalization_default.py` — changing it alters every caller that
omits the argument.

`percentile` is rank-based, so `feature-statistics.json` stores the exact
sorted distribution alongside the moments. Dropping it for summary statistics
alone silently breaks percentile parity.

**Compiled and ACF paths must stay bit-exact.** `tests/test_compiled_runtime_parity.py`
asserts this across all four modes. If you touch normalization, that suite is
the one that matters.

## Conventions

- Two blank lines between top-level definitions; `from __future__ import annotations`.
- Frozen slotted dataclasses for artifacts, each with `to_dict` / `from_dict`.
  `from_dict` validates and rejects unknown schema versions.
- Persisted JSON: atomic write via `.tmp` + `replace`, `sort_keys=True`,
  `indent=2`, UTF-8, trailing newline.
- Schema versions are explicit strings (`atlas.compiled.identity-vectors.v3`).
  Bump the version rather than changing a schema's meaning in place.
- Batch operations record per-item failures and continue; one bad profile must
  never abort a run.

## Don't

- Don't hand-edit anything under `output/` — it is compiler output and stays
  gitignored. Regenerate it.
- Don't assume every profile yields 21 vectors. Record actual counts and flag
  the outliers.
- Don't use `build_identity_vector(calibration_acfs=...)` in new code; it is
  deprecated and warns. Pass `calibration_vectors=`.
- Don't certify control balance in a lossy representation. **A lossy
  representation can make a confounded dataset appear balanced** — Temporal 1D
  measured this: translation normalization masks Saturn's era signal by
  collapsing the classes that carry it, so a clean check downstream is
  compatible with a badly confounded cohort. Certify in the representation
  that carries the information, not the one the analysis consumes.
- Don't gate a denotational system on whether it *can produce* meanings.
  **A system is eligible only when the exact evidence state that licensed
  those meanings remains reproducible, synchronized and independently
  auditable.** Representation 1E enforces this: capability flags are derived
  from the corpus, and `concordance_eligible` requires the corpus, rules and
  dictionary hashes to agree — so a dictionary full of real entries goes
  ineligible the moment its evidence changes underneath it. Checking "is the
  dictionary non-empty" fails open for fixtures, stale artifacts and
  unprovenanced legacy output alike. Any new system entering 1E inherits this
  gate; it may not borrow an existing synthesis vocabulary to skip it.
