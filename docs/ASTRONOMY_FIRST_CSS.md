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

The seven classical planets provide historically grounded symbolic Kamea
structures. Uranus, Neptune, and Pluto participate as measured astronomical
bodies in the planetary and multilayer graphs but do not receive fabricated
Kamea structures.

The canonical Kamea set is Saturn, Jupiter, Mars, Sun, Venus, Mercury, and
Moon. Uranus, Neptune, and Pluto are explicitly marked
`symbolic_projection.available = false` with reason
`no_historical_classical_kamea`.

## Graph of graphs

Every measured astronomical body is a master-graph node. Classical nodes use
the `astronomical_kamea_node` type and nest normalized Kamea graphs by
reference. Uranus, Neptune, and Pluto use the `astronomical_only_node` type.
All master-graph edges carry measured angular separation, aspect and normalized
orb strength where applicable, and applying/separating status where available.

Astronomy never mutates, rewires, prunes, diffuses, or otherwise alters a Kamea
graph in the canonical pipeline. Uranus/rewiring, Neptune/diffusion, and
Pluto/pruning-or-persistence associations exist only as disabled research
hypotheses outside canonical CSS measurement.

Similarity outputs are separated into `astronomical_similarity`,
`classical_kamea_similarity`, and `combined_multilayer_similarity`. The absence
of outer-planet Kamea structures carries no validity or similarity penalty.

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
