# Atlas Architecture Rules

## Prime Directive

Atlas must not add a new analysis engine until the existing codebase has been searched for equivalent functionality.

New code should extend, wrap, or consolidate existing systems before creating new standalone modules.

---

## Canonical Ownership

### `atlas.identity`

Owns:

- identity construction
- intake normalization
- profile metadata
- canonical identity objects

Does not own:

- statistics
- dashboards
- population validation
- report language

---

### `atlas.temporal`

Owns:

- birth data handling
- natal calculations
- sidereal calculations
- houses
- nakshatras
- dashas
- transits
- temporal overlays

Does not own:

- profile clustering
- graph topology
- population statistics

---

### `atlas.research`

Owns:

- research sessions
- matrix generation
- profile-level feature extraction
- validation reports
- research exports

Does not own:

- dashboard rendering
- duplicate graph algorithms
- duplicate clustering algorithms

---

### `atlas.calibration`

Owns canonical implementations for:

- similarity matrices
- nearest neighbors
- z-scores
- population statistics
- clustering
- confidence calibration

This should become the preferred home for reusable statistical algorithms.

---

### `atlas.graph`

Owns:

- graph structures
- topology primitives
- node/edge utilities
- centrality
- connected components
- graph exports

Single-profile topology and population topology should eventually share this layer.

---

### `atlas.explanation`

Owns:

- user-facing interpretation language
- readable summaries
- explanatory text
- evidence-to-language translation

Does not own:

- raw calculations
- dashboard rendering
- population algorithms

---

### `atlas.intelligence`

Owns orchestration only.

It may call:

- identity
- temporal
- research
- calibration
- graph
- explanation

It must not duplicate:

- similarity calculations
- clustering
- z-score logic
- graph algorithms
- feature generation

The future `atlas.intelligence.engine` should be a conductor, not a calculator.

---

## Dashboard Rules

Dashboard pages should be thin.

Allowed:

- layout
- controls
- tables
- charts
- download buttons
- calls to backend functions

Not allowed:

- major calculations
- duplicate algorithms
- hidden business logic
- custom one-off statistical implementations

If dashboard logic grows complex, move it into `src/atlas`.

---

## Duplication Rules

Before adding a new module, search for existing equivalents.

Check especially for:

- similarity
- nearest neighbors
- clustering
- PCA
- z-scores
- graph building
- centrality
- confidence
- report generation
- explanations

If overlap exists, choose one:

1. reuse existing implementation
2. wrap existing implementation
3. migrate shared logic into canonical module
4. deprecate older implementation

Do not maintain two independent implementations unless there is a documented reason.

---

## Deprecation Rules

Do not delete active modules immediately.

Preferred process:

1. mark older implementation as deprecated
2. migrate callers
3. add tests for the replacement
4. remove only after the new path is stable

Every deprecation should state:

- replacement module
- reason
- migration path

---

## Testing Rules

Every new backend module needs tests.

Minimum expectations:

- deterministic test data
- no network dependency
- no dashboard dependency
- edge case coverage
- import test

Dashboard pages do not need exhaustive tests, but their backend functions do.

---

## Dependency Direction

Preferred dependency direction:

```text
dashboard
    ↓
atlas.intelligence
    ↓
atlas.research
    ↓
atlas.calibration / atlas.graph / atlas.temporal / atlas.identity
    ↓
atlas.core