# Atlas Refactor Plan

## Prime directive

No new analysis module should be added until the existing codebase has been searched for equivalent functionality.

## Canonical ownership proposal

- `atlas.identity`: profile and identity construction only.
- `atlas.temporal`: birth, chart, transit, dasha, and time-dependent calculations.
- `atlas.research`: matrix/session construction, research exports, and validation reports.
- `atlas.calibration`: canonical home for similarity, nearest-neighbor, z-score, clustering, and population statistics.
- `atlas.graph`: canonical home for graph algorithms and single/population topology primitives.
- `atlas.explanation`: canonical home for user-facing interpretation language.
- `atlas.intelligence`: orchestration only; no duplicate algorithms.
## Immediate actions

1. Treat `src/atlas/intelligence/engine.py` as an orchestration layer only.
2. Compare `src/atlas/research/population_topology.py` against `src/atlas/calibration/population_graph.py` and migrate shared graph logic into `atlas.graph` or `atlas.calibration`.
3. Compare `src/atlas/research/statistical.py` against `src/atlas/calibration/population_statistics.py`, `structural_clustering.py`, and `similarity_matrix.py`.
4. Keep dashboard pages thin; dashboard should render, not own calculations.
5. Add deprecation notes before deleting anything.
## Review queues

See `DUPLICATE_SCAN.md` for overlap candidates and `MODULE_INVENTORY.md` for per-file recommendations.