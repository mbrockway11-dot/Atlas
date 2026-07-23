# Historical Event–Relationship Transit Validation Methodology

## Claim separation

- Astronomical calculations: Swiss Ephemeris longitudes and explicitly defined aspects.
- Historical facts: accepted only from citation-linked registry records.
- Statistical associations: matched rate differences, odds ratios, Fisher tests, permutations, BH-FDR, and locked holdout summaries.
- Symbolic interpretations: hypothesis rationale only; never evidence of causality.
- Unsupported hypotheses: reported as not retained or not estimable.

## Transit interpretation ontology

Symbolic meanings are composed from the versioned `atlas.transit-interpretation-ontology.v1`. Every component resolves to ontology and source references. The ontology uses Ptolemy's *Tetrabiblos* only as historical provenance and an explicit Atlas operational convention for machine-testable definitions. Symbolic content never contributes to p-values, effect sizes, evidence confidence, or causal status.

## Pilot design

The Apollo 11 crew pilot was selected for authoritative NASA documentation and bounded relationship intervals. Event windows are compared with same-person shifted non-event windows. Profile outcomes are clustered within one mission family, so this pilot is a pipeline validation—not a substantive validation of transit claims.

## Astronomical uncertainty

Unknown birth times are evaluated at 00:00, 12:00, and 23:59 UT. Noon is a computational center, not asserted as the birth time. Houses and angles are excluded. Moon contacts and contacts that change classification across the daily range are flagged.

## Falsification

The run includes deterministic placebo dates, shuffled birth assignments, shuffled relationship edges, a preregistered negative-control hypothesis, permutation tests, BH false-discovery-rate correction, and a profile-level discovery/holdout split. Shared-event differential-outcome and unconnected-pair relationship controls are not estimable in this three-person all-positive pilot.

## Decision rule

No result is retained without adequate sample size, corrected significance, and same-direction holdout performance. No causal claims are permitted.

## Known limitations

- Three-person single-mission pilot is not powered for general inference.
- All documented pilot outcomes are positive; shared-event differential outcomes are unavailable.
- All birth times are unknown; houses and angles are disabled and Moon contacts are uncertainty-flagged.
- Four mission milestones are correlated within one historical event family.
- No matched unconnected relationship controls meet the pilot evidence standard.
- No finding may be called validated from this pilot.

## Existing-system audit

- **usable:** profile library and canonical payload path services; Swiss Ephemeris tropical geocentric planetary calculations; population and graph service conventions; evidence/confidence payload conventions; Streamlit dashboard service boundary; profile readiness reports
- **partially_integrated:** existing transit engine is sign-contact oriented and lacks orb/exactness/duration controls; relationship intelligence compares static structure but does not store sourced time-bounded relationships; lifecycle service accepts events but corpus event coverage is sparse; unknown birth time is normalized but lower-level ephemeris defaults to noon; this pilot adds explicit uncertainty bounds
- **duplicated:** temporal/aspects.py and temporal/atlas_overlay.py expose overlapping aspect-chart implementations; temporal/ephemeris.py and temporal/geocoder.py contain overlapping ephemeris wrappers
- **missing_before_pilot:** normalized sourced event/participation/dynamic-relationship registries; event/control windows and falsification randomizations; orb-based applying/separating transit exposure matrix; Fisher exact tests, permutation tests, BH-FDR, and holdout reporting; historical transit validation dashboard
- **Separation:** No atlas.investment or trading execution module is imported or modified.
