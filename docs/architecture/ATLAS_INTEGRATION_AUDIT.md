# Atlas Integration Audit

**Version:** 1.0  
**Status:** Active Integration Plan  
**Purpose:** Align the existing dashboard and service layer with the current Atlas core architecture.

---

# Executive Summary

Atlas now has a mature backend architecture, but the dashboard was built across multiple earlier phases. The current priority is no longer adding isolated engines. The priority is integrating the engines already built into coherent dashboard workflows.

Recent backend capabilities include:

- Canonical Structural Signature compiler
- Temporal Intelligence compiler
- Temporal Runtime
- Timeline Engine
- Forecast Engine
- Semantic Graph
- Graph Metrics
- Graph Activation
- Graph Propagation
- Graph Resonance
- Structural Fingerprint
- Population Index
- Population Similarity
- Population Search
- Population Archive
- IVE package

The dashboard already contains many relevant pages, including profile observatory, graph explorer, temporal intelligence, population observatory, population topology, statistical intelligence, intelligence engine, and IVE panel. The issue is not absence of dashboard structure. The issue is that many pages predate the newer graph/runtime/fingerprint/population layers.

---

# Current Backend Architecture

```text
Profile Intake
      ¦
      ?
Compiler Engine
      ¦
      ?
Canonical Structural Signature
      ¦
      +-- Identity Layer
      +-- Cipher Layer
      +-- Kamea Layer
      +-- Temporal Layer
              ¦
              ?
      Temporal Runtime
              ¦
              ?
      Timeline / Forecast
              ¦
              ?
      Semantic Graph Bridge
              ¦
              ?
      AtlasGraph
              ¦
      +-------+----------------------------------+
      ?       ?        ?            ?            ?
   Metrics Activation Propagation Resonance Structural Fingerprint
                                                  ¦
                                                  ?
                                      Population Index/Search/Archive
                                                  ¦
                                                  ?
                                                  IVE
```

---

# Dashboard Inventory

Existing dashboard structure includes:

```text
dashboard/
    atlas_dashboard.py

    components/
        classification_panel.py
        functional_role_panel.py
        ive_panel.py

    components/observatory/
        calibration.py
        functional_role_v2.py
        graph_evolution_3d.py
        header.py
        topology_3d.py

    pages/
        atlas_ai.py
        compare_profiles.py
        developer_console.py
        evidence_explorer.py
        graph_explorer.py
        identity_stack_lab.py
        intelligence_engine.py
        morphology_lab.py
        narrative_intelligence.py
        population_intelligence.py
        population_observatory.py
        population_topology.py
        population_validation.py
        profile_builder.py
        profile_library.py
        profile_observatory.py
        profile_report.py
        profile_test_lab.py
        relationship_report.py
        research_corpus.py
        research_session.py
        role_calibration_lab.py
        statistical_intelligence.py
        temporal_intelligence.py
        validation_lab.py
```

The dashboard already has strong coverage areas. The next phase is wiring these pages to the new unified backend outputs instead of duplicating calculations.

---

# Integration Principle

No dashboard page should own core analysis logic.

Dashboard pages should:

1. Render controls.
2. Call service-layer functions.
3. Display returned payloads.
4. Provide export/download controls.

Core logic should live in:

```text
src/atlas/
    core/
    temporal/
    temporal_runtime/
    graph/
    fingerprint/
    population/
    ive/
    services/
```

---

# Primary Integration Targets

## 1. Profile Observatory

Current role:

- Main profile view
- Likely identity/temporal/profile summary surface

Target role:

The Profile Observatory should become the canonical single-profile intelligence page.

It should display:

```text
Profile
    Identity
    CSS Metadata
    Temporal Intelligence
    Runtime Activation
    Timeline / Forecast
    Semantic Graph
    Graph Metrics
    Graph Activation
    Graph Propagation
    Structural Fingerprint
    IVE Vector
    Population Nearest Neighbors
```

Recommended tabs:

```text
Overview
Temporal
Runtime
Graph
Activation
Propagation
Fingerprint
IVE
Population
Raw JSON
```

Required service payload:

```python
build_profile_observatory_payload(profile_key: str) -> dict
```

Payload should include:

```text
css
temporal_runtime
timeline
forecast
semantic_graph
graph_metrics
graph_activation
graph_propagation
structural_fingerprint
ive_vector
population_search_results
exports
```

---

## 2. Temporal Intelligence Page

Current role:

- Displays natal, houses, nakshatras, dignities, yogas, dashas, and transits.

Target role:

Temporal Intelligence should remain the focused temporal page, but it should include runtime and forecast outputs.

Add sections:

```text
Runtime Summary
Activation Score
Timeline Summary
Forecast Window
Peak Date
Temporal Graph Bridge Status
```

Do not add graph algorithms directly to this page. Instead, expose graph links or summary cards.

Recommended additions:

```text
runtime.activation_score
timeline.summary
forecast.summary
transits.summary
```

---

## 3. Graph Explorer

Current role:

- Graph/topology visualization surface.

Target role:

Graph Explorer should become the main surface for AtlasGraph.

It should support:

```text
Semantic Graph
Graph Metrics
Activation Field
Propagation Field
Resonance Comparison
Top Nodes
Hub Nodes
Isolated Nodes
Activation Center
Propagation Top Node
```

Recommended tabs:

```text
Graph
Metrics
Activation
Propagation
Resonance
Raw Graph JSON
```

This page should consume:

```python
build_temporal_graph()
compute_graph_metrics()
build_graph_activation()
propagate_activation()
compute_graph_resonance()
```

via a service wrapper, not directly.

---

## 4. IVE Panel / IVE Integration

Current role:

- Existing IVE component exists.

Target role:

IVE should become the high-dimensional profile representation layer that consumes existing graph/fingerprint outputs.

Integration question:

Which IVE features duplicate graph/fingerprint features?

Audit required:

```text
src/atlas/ive/feature_vector.py
src/atlas/ive/identity_vector.py
src/atlas/ive/composite.py
src/atlas/ive/similarity.py
```

Needed bridge:

```text
src/atlas/ive/graph_bridge.py
```

Possible API:

```python
build_ive_from_graph_intelligence(
    *,
    css: dict,
    graph: AtlasGraph,
    metrics: GraphMetrics,
    activation: GraphActivation,
    propagation: PropagationResult,
    fingerprint: StructuralFingerprint,
) -> IdentityVector
```

Goal:

IVE should not recompute graph metrics. It should consume graph intelligence outputs as features.

---

## 5. Population Observatory

Current role:

- Population-level page.

Target role:

Population Observatory should expose the new population stack.

It should display:

```text
Population Index
Archive Load/Save Status
Search Controls
Nearest Neighbors
Similarity Scores
Shared Features
Structural Hashes
Metadata Filters
```

Recommended tabs:

```text
Index
Search
Similarity
Archive
Raw JSON
```

Must consume:

```python
build_population_index()
find_similar_profiles()
search_population()
save_population_index()
load_population_index()
```

---

## 6. Population Intelligence

Current role:

- Likely older population analysis page.

Target role:

This should become higher-level population analytics after the archive/search layer is wired.

Future capabilities:

```text
Cluster Discovery
Archetypes
Outlier Detection
Structural Cohorts
Historical Analogs
Population Topology
```

Do not build clustering here until corpus/archive/search are wired.

---

## 7. Statistical Intelligence

Current role:

- Existing statistical page uses service-backed matrix/cluster/PCA style calculations.

Target role:

Statistical Intelligence should eventually operate on structural fingerprints and IVE vectors, not older matrix-only features.

Integration target:

```text
StructuralFingerprint.vector
IVE vector
PopulationIndex records
```

Needed migration:

```text
Old profile matrix
        ?
Structural fingerprint matrix
        ?
IVE matrix
        ?
PCA / clustering / cohorts
```

---

## 8. Relationship Report

Current role:

- Compares two profiles using reports, graph morphology, topology contrast, and warnings.

Target role:

Relationship Report should use graph resonance and fingerprint similarity.

Add:

```text
Graph Resonance
Propagation Similarity
Structural Fingerprint Similarity
IVE Similarity
Shared Hubs
Shared Top Nodes
Unique Structures
```

This page should become the two-profile counterpart to Population Search.

---

# Service Layer Needs

The dashboard already appears to prefer service-backed pages. Continue that pattern.

Create or update service modules:

```text
src/atlas/services/profile_observatory_service.py
src/atlas/services/graph_intelligence_service.py
src/atlas/services/population_intelligence_service.py
src/atlas/services/ive_integration_service.py
```

Recommended service APIs:

```python
build_single_profile_intelligence_payload(profile_key: str) -> dict

build_graph_intelligence_payload(profile_key: str) -> dict

build_population_search_payload(
    *,
    query_profile_key: str,
    archive_path: str | None = None,
    minimum_similarity: float = 0.0,
    top_k: int = 25,
    exclude_self: bool = True,
) -> dict

build_ive_integration_payload(profile_key: str) -> dict
```

---

# Duplicate / Redundant Areas To Audit

## Potential redundancy

```text
IVE similarity
Graph resonance
Population similarity
Relationship report similarity
Statistical matrix similarity
```

These should not remain independent scoring systems forever.

Recommended hierarchy:

```text
Raw graph comparison
        ?
Graph Resonance
        ?
Structural Fingerprint Similarity
        ?
IVE Similarity
        ?
Population Search
```

Each layer should document what it adds.

---

# Recommended Integration Order

## Phase 1 — Inventory

Inspect these files:

```text
dashboard/pages/profile_observatory.py
dashboard/pages/graph_explorer.py
dashboard/pages/temporal_intelligence.py
dashboard/pages/population_observatory.py
dashboard/pages/population_intelligence.py
dashboard/components/ive_panel.py
src/atlas/services/
src/atlas/ive/
```

Goal:

Find existing service boundaries and avoid direct dashboard logic.

---

## Phase 2 — Profile Observatory Payload

Build one master payload:

```python
build_single_profile_intelligence_payload(profile_key)
```

This should become the reusable integration payload for several pages.

---

## Phase 3 — Graph Explorer Integration

Wire graph metrics, activation, propagation, and resonance into Graph Explorer.

---

## Phase 4 — IVE Bridge

Map graph/fingerprint outputs into IVE.

Do not duplicate features.

---

## Phase 5 — Population Observatory Integration

Wire population index/search/archive to the dashboard.

---

## Phase 6 — Statistical/Clustering Migration

Move statistical intelligence toward structural fingerprint vectors and IVE vectors.

---

# Current Completion Estimate

## Backend Core

```text
Compiler                       complete
Temporal Intelligence           complete
Runtime                         complete
Graph Intelligence              complete
Structural Fingerprint          complete
Population Index/Search/Archive complete
```

## Dashboard

```text
Dashboard pages                 present
Dashboard integration            incomplete
Service unification              partial
New graph/fingerprint outputs    not fully surfaced
IVE integration                   incomplete
```

The dashboard is now the main gap.

---

# Immediate Next Action

Do not add more engines.

Next concrete task:

```text
Build Single Profile Intelligence Service
```

File:

```text
src/atlas/services/single_profile_intelligence_service.py
```

Purpose:

Produce one complete payload for a profile using all major engines.

This service should be the integration backbone for:

```text
Profile Observatory
Graph Explorer
Temporal Intelligence
IVE Panel
Population Search
```

Planned API:

```python
build_single_profile_intelligence_payload(profile_key: str) -> dict
```

Payload:

```text
profile_key
css
temporal_runtime
timeline
forecast
semantic_graph
graph_metrics
graph_activation
graph_propagation
structural_fingerprint
ive
population
exports
warnings
errors
```

Once this exists, the dashboard can migrate page-by-page without rebuilding logic.

---

# Final Objective

Atlas should not become a collection of separate dashboard pages.

Atlas should become a unified intelligence workbench where every page is a different lens on the same canonical pipeline:

```text
Profile
    ?
CSS
    ?
Runtime
    ?
Graph
    ?
Fingerprint
    ?
IVE
    ?
Population
    ?
Interpretation
```

That is the integration target.
