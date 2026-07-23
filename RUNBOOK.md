# Atlas Compiled Runtime — Runbook

Operating guide for the compiled layer: what to run, in what order, and how to
tell whether the runtime can be trusted.

> **Interpreter:** every command below must run under the project virtualenv.
> A bare `python` lacks native dependencies (`swisseph`) and will fail with
> import errors that look like broken code but are not.
>
> ```powershell
> .venv\Scripts\python.exe -m pytest -q
> ```
>
> On Windows PowerShell use `.venv\Scripts\python.exe`; the examples below
> write `python` for brevity.

---

## The two representations

```text
ACF   output/library/profiles/<key>/profile.acf.json
      Authoritative research representation. ~2,122 profiles, ~5.4 GB.

AIR   output/compiled/
      Authoritative runtime representation. ~42.5 MB. Derived, disposable,
      gitignored — always rebuildable from ACF.
```

Runtime reads AIR. It never walks the ACF corpus.

---

## Rebuild order

Each stage consumes the previous one's output. Running them out of order
produces artifacts tied to a corpus revision that no longer exists, which
the health check reports as stale.

```text
1. compile profiles          ACF        -> identity_vectors/*.json
2. validate artifacts        artifacts  -> health verdict
3. build index               artifacts  -> index.json
4. build calibration stats   artifacts  -> calibration/*.json
5. run parity tests          everything -> correctness proof
6. benchmark                 everything -> performance proof
```

Full sequence from a clean tree:

```powershell
python scripts\compile_identity_vectors_batch.py
python scripts\validate_compiled_vectors.py --write-index
python scripts\build_calibration_statistics.py
python -m pytest tests\test_compiled_runtime_parity.py -q
python scripts\benchmark_compiled_runtime.py
python scripts\compiled_runtime_health.py
```

Steps 2 and 3 are one command: `--write-index` validates, then writes the
index from what it validated.

---

## Commands

### Compile one profile

```powershell
python scripts\compile_identity_vector.py nikola_tesla
python scripts\compile_identity_vector.py nikola_tesla --force
```

Prints `"rebuilt": true` on a real compile, `false` when the existing artifact
was reused. Reuse is the expected result for an unchanged profile.

### Compile the whole library

```powershell
python scripts\compile_identity_vectors_batch.py
python scripts\compile_identity_vectors_batch.py --force
python scripts\compile_identity_vectors_batch.py --limit 100
python scripts\compile_identity_vectors_batch.py --profile-key nikola_tesla
python scripts\compile_identity_vectors_batch.py --fail-fast
python scripts\compile_identity_vectors_batch.py --manifest-path output\compiled\manifest.json
```

Scans the library for profiles that actually have an ACF export. Registry
entries without one are skipped, not counted as failures. One broken profile
never aborts the run unless `--fail-fast` is given; every failure is recorded
in the manifest with its error type.

Writes `output/compiled/manifest.json`.

### Validate artifacts and build the index

```powershell
python scripts\validate_compiled_vectors.py
python scripts\validate_compiled_vectors.py --write-index
python scripts\validate_compiled_vectors.py --rebuild-stale --write-index
```

Classifies every artifact as `current`, `missing`, `stale`, `damaged`,
`old_schema`, or `orphaned` (source ACF gone). Read-only unless
`--rebuild-stale`. Exits non-zero when anything is not current.

### Build calibration statistics

```powershell
python scripts\build_calibration_statistics.py
python scripts\build_calibration_statistics.py --skip-vectors
```

Reads compiled artifacts — never ACFs — and writes:

```text
output/compiled/calibration/feature-statistics.json   ~20 MB, always needed
output/compiled/calibration/raw-vectors.json          ~41 MB, optional
```

`--skip-vectors` writes statistics only. The consolidated corpus is useful for
analysis but the runtime needs only the statistics.

### Check runtime health

```powershell
python scripts\compiled_runtime_health.py
python scripts\compiled_runtime_health.py --deep
python scripts\compiled_runtime_health.py --quiet
```

Reports manifest, artifacts, index, and statistics. The default check reads
headers only and is cheap enough to run often; `--deep` validates every
artifact against its source. Exits non-zero when anything is not OK.

### Benchmark

```powershell
python scripts\benchmark_compiled_runtime.py
python scripts\benchmark_compiled_runtime.py --include-legacy
```

`--include-legacy` samples the old full-ACF path and extrapolates it, rather
than paying the full cost.

---

## When to rebuild what

| Change | Rebuild |
|---|---|
| One ACF edited | that profile, then index + statistics |
| Many ACFs / new profiles | batch, then index + statistics |
| Feature set, planet or cipher order, `IVE_VERSION` | **everything** (`--force`) |
| Normalization algorithm (bump `NORMALIZATION_VERSION`) | **everything** (`--force`) |
| Compiler logic only | batch (`--force`), then index + statistics |

The feature-schema hash makes rows 3 and 4 self-detecting: artifacts built
against a different schema read as stale and rebuild on the next run. It only
works if you bump the version constant when behaviour changes.

---

## Reading the health output

| Status | Meaning | Action |
|---|---|---|
| `ok` | Component matches the current schema and corpus | none |
| `stale` | Built against an older schema or a different corpus revision | rebuild that stage |
| `missing` | Artifact absent | run the stage |
| `error` | Present but unreadable or damaged | rebuild with `--force` |

Overall status is the worst component. The most common real finding is
**statistics stale against the index** — profiles were compiled but statistics
were not rebuilt, so normalization calibrates against a population that no
longer matches the corpus.

---

## Invariants

Anything below being false is a bug, not a configuration problem.

```text
successful_count = rebuilt_count + reused_count
requested_count  = successful_count + failed_count

second consecutive batch run  -> reused_count == successful_count
unchanged source + unchanged compiler semantics -> identical content_hash
compiled comparison output == ACF comparison output   (bit-exact, all modes)
```

The second run of a batch compile is the real proof the persistent layer
works: it should reuse everything and finish in seconds.

---

## Provenance recorded in every artifact

```text
schema_version        artifact format          feature_schema_hash   meaning of a feature
compiler version      which compiler           content_hash          semantic content only
git commit + dirty    which source revision    source SHA-256        which ACF
python version        interpreter              platform              OS
atlas version         package                  command               how it was invoked
```

`content_hash` deliberately excludes timestamps, git state, platform, and
command, so two builds of the same source agree. `git_dirty` matters: a clean
commit hash does not describe uncommitted compiler changes.

---

## Troubleshooting

**Tests fail at collection with `ModuleNotFoundError: swisseph`**
Wrong interpreter. Use `.venv\Scripts\python.exe`.

**Comparison returns a service error instead of results**
The compiled artifact could not be resolved. Run the health check, then
`validate_compiled_vectors.py --rebuild-stale`. The runtime deliberately does
not fall back to reparsing the ACF corpus — a silent fallback would turn a
millisecond request into a minute-long one.

**Everything rebuilds when nothing changed**
Expected after a feature-schema or normalization-version change. If it repeats
on every run, the recorded hash never matches the current one — check that
`NORMALIZATION_VERSION`/`IVE_VERSION` are stable and not derived from
something volatile.

**`content hash mismatch` on load**
The artifact was modified after compilation. Rebuild it; do not hand-edit
anything under `output/`.

**Statistics stale immediately after building them**
The index was rebuilt after the statistics. Rebuild statistics last — they are
pinned to the corpus revision via the source-manifest hash.
