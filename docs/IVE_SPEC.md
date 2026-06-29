# Identity Vector Engine Specification

IVE Version: 0.3.0

## Purpose

The Identity Vector is the canonical mathematical representation of an Atlas profile.

Graphs are measurement instruments.
Classifications are interpretations.
The Identity Vector is the stable measurement object between them.

## Pipeline

Identity input
→ 21 Kamea graph layers
→ raw feature vectors
→ normalized planet vectors
→ composite planet vectors
→ identity vector

## Canonical Objects

### PlanetFeatureVector

One raw bounded vector for one cipher × planet layer.

Required:
- version
- name
- cipher
- planet
- kamea
- grid_size
- features

### NormalizedPlanetVector

One calibrated vector for one cipher × planet layer.

Required:
- version
- name
- cipher
- planet
- kamea
- grid_size
- features
- raw_features
- normalization_mode
- calibration_size

### CompositePlanetVector

One planet vector combining all available ciphers.

Required:
- version
- name
- planet
- features
- source_ciphers
- source_count
- normalization_mode

### IdentityVector

One full identity representation.

Required:
- version
- name
- planets
- global_features
- quality
- diagnostics

## Required Planets

Canonical order:

1. Saturn
2. Jupiter
3. Mars
4. Sun
5. Venus
6. Mercury
7. Moon

## Required Features

- node_coverage
- edge_coverage
- density
- entropy
- axis_strength
- graph_coherence
- core_survival_score
- topology_stability
- attractor_stability
- bridge_ratio
- articulation_ratio
- loop_ratio
- hub_ratio
- leaf_ratio
- reduction_entropy
- node_survival_auc
- edge_survival_auc

## Invariants

All vector features must be bounded between 0.0 and 1.0.

An IdentityVector must contain seven composite planet vectors.

IdentityVector global features must also be bounded between 0.0 and 1.0 unless explicitly documented otherwise.

No classifier labels belong inside the IdentityVector.

The IdentityVector may contain diagnostics about the measurement quality, but not interpretive role labels.

## Separation Rule

Measurement layer:
- feature vectors
- normalized vectors
- composite planet vectors
- identity vectors
- relationship matrices

Interpretation layer:
- functional role
- subtype
- report language
- predictions
- compatibility
- comparison narratives

## Versioning

IVE 0.1.0: PlanetFeatureVector
IVE 0.2.0: NormalizedPlanetVector + CompositePlanetVector
IVE 0.3.0: IdentityVector
IVE 0.4.0: Planet Relationship Matrix
IVE 1.0.0: Stable public API