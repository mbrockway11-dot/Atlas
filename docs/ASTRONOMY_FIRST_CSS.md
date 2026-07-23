# Astronomy-First Canonical Structural Signature

Atlas Compiler 3.0 treats physical measurement as canonical and interpretation as downstream.

## Execution order

1. Identity and birth-data provenance
2. Physical astronomy
3. Planetary angular graph
4. Cipher transform
5. Unit-space Kamea graphs
6. Structural graph metrics
7. Nested planetary graph-of-graphs
8. Tropical, sidereal, and other interpretive transforms
9. Population fitting and interpretation

No interpretation is permitted to change an upstream measurement.

## Physical astronomy contract

`atlas.astronomy.build_physical_astronomy` records, for the Sun, Moon, Mercury,
Venus, Mars, Jupiter, Saturn, Uranus, Neptune, and Pluto:

- right ascension and declination;
- ecliptic longitude and latitude;
- geocentric distance;
- apparent longitude velocity and retrograde state;
- actual IAU constellation;
- tropical and Lahiri sidereal signs as metadata only.

The planetary graph contains all pairwise angular separations. Major aspects
are classifications of those measurements. Visibility and gravitational
metadata remain explicitly `not_computed` until Atlas has a selected observer,
horizon, mass, and reference-frame model.

## Normalized Kamea graph contract

All planetary Kamea coordinates use `x/(n-1), y/(n-1)` in `[0,1] × [0,1]`.
Geometry is stored once. Repeated visits increase node weight; repeated
transitions increase edge weight. The graph exports density, loops, hubs,
degree, clustering, paths, entropy, symmetry, axiality, center of mass,
revisit/persistence measures, motifs, and centrality summaries.

The Kamea graph is a deterministic name-derived transform, not a physical
astronomical measurement. Planet and stellar metadata do not modify its path.

## Graph of graphs

Every measured astronomical body is a master-graph node. Traditional
planetary Kamea graphs are nested by reference where available. Master-graph
edges are measured natal aspects. Outer planets remain valid astronomical
nodes even though the traditional seven-planet Kamea system has no native
square for them.

## Classification policy

Atlas does not manually assign Axial, Radial, Distributed, Clustered, or other
topology labels in the canonical measurement pass. The compiler emits a
population-ready feature vector and the status
`unclassified_pending_population_fit`. Classification requires a versioned
reference corpus and reproducible clustering model.

## Compatibility

The existing temporal/Jyotish, numerology, Gematria, narrative, and symbolic
systems remain available. They are downstream transforms and must identify
their coordinate system, assumptions, and evidence type. Existing ACF graph
artifacts remain readable during migration.

## Deferred work

- observer-dependent visibility calculations;
- a selected gravitational/reference-frame model;
- population-fitted morphology families;
- graph embeddings, kernels, and neural models;
- prospective behavioral validation.

These are intentionally marked pending instead of being approximated or
silently inferred.
