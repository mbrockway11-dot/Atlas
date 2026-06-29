# Atlas Duplicate and Overlap Scan

Static scan of duplicate function names and concept overlap categories. Review before adding new engines.

## High-risk overlap categories


### similarity

- `dashboard\pages\compare_profiles.py`
- `dashboard\pages\population_intelligence.py`
- `dashboard\pages\population_validation.py`
- `src\atlas\ablation\metrics.py`
- `src\atlas\calibration\models.py`
- `src\atlas\calibration\nearest_neighbor.py`
- `src\atlas\calibration\population_graph.py`
- `src\atlas\calibration\population_statistics.py`
- `src\atlas\calibration\similarity_calibration.py`
- `src\atlas\calibration\similarity_engine.py`
- `src\atlas\calibration\similarity_matrix.py`
- `src\atlas\calibration\structural_clustering.py`
- `src\atlas\corpus\duplicates.py`
- `src\atlas\corpus\similarity.py`
- `src\atlas\features\clustering.py`
- `src\atlas\graph\identity_morphology.py`
- `src\atlas\identity\builder.py`
- `src\atlas\identity\similarity.py`
- `src\atlas\ive\relationship_matrix.py`
- `src\atlas\ive\similarity.py`
- `src\atlas\measurement\dynamics.py`
- `src\atlas\research\population_topology.py`
- `src\atlas\research\similarity.py`
- `src\atlas\research\validation.py`
- `src\atlas\resonance\similarity.py`
- `src\atlas\temporal\aspects.py`
- `src\atlas\temporal\transits.py`
- `src\atlas\topology\structural_similarity.py`
- `src\atlas\topology\topology_signature.py`
- `tests\test_corpus_similarity.py`
- `tests\test_ive_similarity.py`
- `tests\test_nearest_neighbor.py`
- `tests\test_planet_matrix.py`
- `tests\test_population_topology.py`
- `tests\test_population_validation.py`
- `tests\test_research_similarity.py`
- `tests\test_resonance.py`
- `tests\test_similarity_engine.py`
- `tests\test_similarity_matrix.py`
- `tests\test_structural_similarity.py`
- `tests\test_temporal_aspects.py`
- `tests\test_temporal_transits.py`

### clustering

- `dashboard\pages\population_intelligence.py`
- `dashboard\pages\statistical_intelligence.py`
- `src\atlas\calibration\structural_clustering.py`
- `src\atlas\features\cluster_interpretation.py`
- `src\atlas\features\clustering.py`
- `src\atlas\measurement\organization.py`
- `src\atlas\research\statistical.py`
- `src\atlas\resonance\clustering.py`
- `tests\test_cluster_interpretation.py`
- `tests\test_clustering.py`
- `tests\test_resonance.py`
- `tests\test_statistical_intelligence.py`
- `tests\test_structural_clustering.py`

### graph_topology

- `dashboard\components\__init__.py`
- `dashboard\components\classification_panel.py`
- `dashboard\components\functional_role_panel.py`
- `dashboard\components\ive_panel.py`
- `dashboard\components\observatory\__init__.py`
- `dashboard\components\observatory\calibration.py`
- `dashboard\components\observatory\functional_role_v2.py`
- `dashboard\components\observatory\graph_evolution_3d.py`
- `dashboard\components\observatory\header.py`
- `dashboard\components\observatory\topology_3d.py`
- `dashboard\pages\identity_stack_lab.py`
- `dashboard\pages\morphology_lab.py`
- `dashboard\pages\population_topology.py`
- `dashboard\pages\statistical_intelligence.py`
- `dashboard\utils\graphs.py`
- `src\atlas\calibration\edge_normalization.py`
- `src\atlas\calibration\population_graph.py`
- `src\atlas\calibration\population_statistics.py`
- `src\atlas\calibration\similarity_engine.py`
- `src\atlas\calibration\structural_clustering.py`
- `src\atlas\classification\functional_role.py`
- `src\atlas\classification\functional_role_v2.py`
- `src\atlas\classification\meanings.py`
- `src\atlas\essence\builder.py`
- `src\atlas\export\csv.py`
- `src\atlas\export\json.py`
- `src\atlas\export\svg.py`
- `src\atlas\features\metrics.py`
- `src\atlas\features\scoring.py`
- `src\atlas\fingerprint\builder.py`
- `src\atlas\fusion\translation.py`
- `src\atlas\graph\__init__.py`
- `src\atlas\graph\analysis.py`
- `src\atlas\graph\attractor.py`
- `src\atlas\graph\canonical.py`
- `src\atlas\graph\coherence.py`
- `src\atlas\graph\identity_graph.py`
- `src\atlas\graph\identity_morphology.py`
- `src\atlas\graph\identity_resonance.py`
- `src\atlas\graph\identity_stack.py`
- `src\atlas\graph\identity_topology.py`
- `src\atlas\graph\motifs.py`
- `src\atlas\graph\reduction.py`
- `src\atlas\graph\stack_audit.py`
- `src\atlas\graph\structural_genome.py`
- `src\atlas\graph\structural_truth.py`
- `src\atlas\identity\__init__.py`
- `src\atlas\identity\builder.py`
- `src\atlas\identity\layer.py`
- `src\atlas\identity\persistence.py`
- `src\atlas\intelligence\interpreter.py`
- `src\atlas\invariant\features.py`
- `src\atlas\kamea\visit_history.py`
- `src\atlas\motifs\detector.py`
- `src\atlas\motifs\identity.py`
- `src\atlas\overlay\composite_overlay.py`
- `src\atlas\research\attractor_metrics.py`
- `src\atlas\research\coherence_metrics.py`
- `src\atlas\research\graph_metrics.py`
- `src\atlas\research\population_topology.py`
- `src\atlas\research\reduction_metrics.py`
- `src\atlas\research\statistical.py`
- `src\atlas\resonance\alignment.py`
- `src\atlas\resonance\clustering.py`
- `src\atlas\resonance\field.py`
- `src\atlas\resonance\similarity.py`
- `src\atlas\resonance\vector.py`
- `src\atlas\signatures\__init__.py`
- `src\atlas\signatures\fingerprint.py`
- `src\atlas\signatures\graph_entropy.py`
- `src\atlas\signatures\motif_detection.py`
- `src\atlas\signatures\topology_signature.py`
- `src\atlas\topology\__init__.py`
- `src\atlas\topology\branch_pruning.py`
- `src\atlas\topology\differential.py`
- `src\atlas\topology\graph.py`
- `src\atlas\topology\graph_builder.py`
- `src\atlas\topology\node_weights.py`
- `src\atlas\topology\overlay.py`
- `src\atlas\topology\structural_similarity.py`
- ... 51 more

### statistics

- `dashboard\pages\population_validation.py`
- `dashboard\pages\profile_test_lab.py`
- `dashboard\pages\validation_lab.py`
- `src\atlas\calibration\baseline_library.py`
- `src\atlas\calibration\models.py`
- `src\atlas\calibration\population_statistics.py`
- `src\atlas\calibration\zscore_engine.py`
- `src\atlas\fusion\translation.py`
- `src\atlas\ive\identity_vector.py`
- `src\atlas\ive\normalizer.py`
- `src\atlas\research\baselines.py`
- `src\atlas\research\feature_correlation.py`
- `src\atlas\research\feature_variance.py`
- `src\atlas\research\population.py`
- `src\atlas\research\validation.py`
- `src\atlas\research\zscores.py`
- `tests\test_baselines.py`
- `tests\test_feature_correlation.py`
- `tests\test_feature_variance.py`
- `tests\test_ive_normalizer.py`
- `tests\test_population.py`
- `tests\test_population_statistics.py`
- `tests\test_zscore_engine.py`
- `tests\test_zscores.py`

### confidence

- `dashboard\components\functional_role_panel.py`
- `src\atlas\calibration\confidence_engine.py`
- `src\atlas\calibration\models.py`
- `src\atlas\calibration\population_statistics.py`
- `src\atlas\classification\functional_role.py`
- `src\atlas\classification\functional_role_v2.py`
- `src\atlas\classification\role_diagnostics.py`
- `src\atlas\fusion\translation.py`
- `src\atlas\graph\structural_truth.py`
- `src\atlas\intelligence\confidence.py`
- `src\atlas\intelligence\evidence.py`
- `tests\test_planet_matrix.py`

### reports

- `dashboard\components\functional_role_panel.py`
- `dashboard\components\ive_panel.py`
- `dashboard\components\observatory\graph_evolution_3d.py`
- `dashboard\pages\compare_profiles.py`
- `dashboard\pages\identity_stack_lab.py`
- `dashboard\pages\morphology_lab.py`
- `dashboard\pages\population_intelligence.py`
- `dashboard\pages\population_observatory.py`
- `dashboard\pages\population_topology.py`
- `dashboard\pages\population_validation.py`
- `dashboard\pages\profile_observatory.py`
- `dashboard\pages\profile_test_lab.py`
- `dashboard\pages\research_session.py`
- `dashboard\pages\temporal_intelligence.py`
- `src\atlas\ablation\reports.py`
- `src\atlas\acf\builder.py`
- `src\atlas\calibration\models.py`
- `src\atlas\calibration\nearest_neighbor.py`
- `src\atlas\calibration\population_graph.py`
- `src\atlas\calibration\similarity_matrix.py`
- `src\atlas\calibration\structural_clustering.py`
- `src\atlas\calibration\zscore_engine.py`
- `src\atlas\classification\functional_role_v2.py`
- `src\atlas\classification\role_calibration.py`
- `src\atlas\classification\role_diagnostics.py`
- `src\atlas\coherence\summary.py`
- `src\atlas\comparison\compare.py`
- `src\atlas\comparison\interpretation.py`
- `src\atlas\features\cluster_interpretation.py`
- `src\atlas\fusion\translation.py`
- `src\atlas\graph\canonical.py`
- `src\atlas\graph\coherence.py`
- `src\atlas\graph\identity_graph.py`
- `src\atlas\graph\identity_morphology.py`
- `src\atlas\graph\identity_resonance.py`
- `src\atlas\graph\identity_stack.py`
- `src\atlas\graph\identity_topology.py`
- `src\atlas\graph\motifs.py`
- `src\atlas\graph\reduction.py`
- `src\atlas\graph\stack_audit.py`
- `src\atlas\graph\structural_genome.py`
- `src\atlas\graph\structural_truth.py`
- `src\atlas\identity\builder.py`
- `src\atlas\identity\persistence.py`
- `src\atlas\identity\summary.py`
- `src\atlas\importance\ablation_importance.py`
- `src\atlas\intelligence\interpreter.py`
- `src\atlas\intelligence\report.py`
- `src\atlas\interpretation\__init__.py`
- `src\atlas\interpretation\identity.py`
- `src\atlas\interpretation\profile.py`
- `src\atlas\interpretation\rules.py`
- `src\atlas\invariant\pipeline.py`
- `src\atlas\kamea\validation.py`
- `src\atlas\library\profile_library.py`
- `src\atlas\motifs\identity.py`
- `src\atlas\ontology\identity.py`
- `src\atlas\overlay\composite_overlay.py`
- `src\atlas\profiles\__init__.py`
- `src\atlas\profiles\summary.py`
- `src\atlas\provenance.py`
- `src\atlas\reports\__init__.py`
- `src\atlas\reports\markdown.py`
- `src\atlas\research\coherence_metrics.py`
- `src\atlas\research\motion.py`
- `src\atlas\research\population_topology.py`
- `src\atlas\research\statistical.py`
- `src\atlas\research\validation.py`
- `src\atlas\resonance\field.py`
- `tests\test_cluster_interpretation.py`
- `tests\test_coherence_summary.py`
- `tests\test_identity_graph_coherence.py`
- `tests\test_identity_interpretation.py`
- `tests\test_intelligence_interpreter.py`
- `tests\test_intelligence_report.py`
- `tests\test_interpretation.py`
- `tests\test_invariant_pipeline.py`
- `tests\test_kamea_validation.py`
- `tests\test_population_validation.py`
- `tests\test_profile_summary.py`
- ... 8 more

### features

- `dashboard\components\functional_role_panel.py`
- `dashboard\components\ive_panel.py`
- `dashboard\pages\compare_profiles.py`
- `dashboard\pages\population_intelligence.py`
- `dashboard\pages\population_topology.py`
- `dashboard\pages\population_validation.py`
- `dashboard\pages\profile_observatory.py`
- `dashboard\pages\profile_test_lab.py`
- `dashboard\pages\role_calibration_lab.py`
- `dashboard\pages\statistical_intelligence.py`
- `dashboard\pages\validation_lab.py`
- `src\atlas\ablation\experiments.py`
- `src\atlas\ablation\metrics.py`
- `src\atlas\acf\builder.py`
- `src\atlas\calibration\models.py`
- `src\atlas\calibration\nearest_neighbor.py`
- `src\atlas\calibration\population_statistics.py`
- `src\atlas\calibration\similarity_engine.py`
- `src\atlas\calibration\similarity_matrix.py`
- `src\atlas\calibration\zscore_engine.py`
- `src\atlas\classification\functional_role_v2.py`
- `src\atlas\classification\role_calibration.py`
- `src\atlas\classification\role_diagnostics.py`
- `src\atlas\comparison\compare.py`
- `src\atlas\comparison\features.py`
- `src\atlas\comparison\planet_matrix.py`
- `src\atlas\corpus\diagnostics.py`
- `src\atlas\corpus\similarity.py`
- `src\atlas\diagnostics\audit.py`
- `src\atlas\explanation\identity.py`
- `src\atlas\explanation\measurements.py`
- `src\atlas\explanation\planets.py`
- `src\atlas\features\__init__.py`
- `src\atlas\features\cluster_interpretation.py`
- `src\atlas\features\clustering.py`
- `src\atlas\features\metrics.py`
- `src\atlas\features\scoring.py`
- `src\atlas\fusion\translation.py`
- `src\atlas\graph\analysis.py`
- `src\atlas\graph\canonical.py`
- `src\atlas\identity\persistence.py`
- `src\atlas\identity\similarity.py`
- `src\atlas\importance\__init__.py`
- `src\atlas\importance\ablation_importance.py`
- `src\atlas\interpretation\identity.py`
- `src\atlas\invariant\features.py`
- `src\atlas\ive\__init__.py`
- `src\atlas\ive\composite.py`
- `src\atlas\ive\feature_vector.py`
- `src\atlas\ive\identity_vector.py`
- `src\atlas\ive\normalizer.py`
- `src\atlas\ive\relationship_matrix.py`
- `src\atlas\ive\schema.py`
- `src\atlas\ive\similarity.py`
- `src\atlas\measurement\__init__.py`
- `src\atlas\reports\markdown.py`
- `src\atlas\research\attractor_metrics.py`
- `src\atlas\research\baselines.py`
- `src\atlas\research\coherence_metrics.py`
- `src\atlas\research\distributions.py`
- `src\atlas\research\export_matrix.py`
- `src\atlas\research\feature_correlation.py`
- `src\atlas\research\feature_importance.py`
- `src\atlas\research\feature_variance.py`
- `src\atlas\research\graph_metrics.py`
- `src\atlas\research\matrix.py`
- `src\atlas\research\motion.py`
- `src\atlas\research\planetary_vectors.py`
- `src\atlas\research\population.py`
- `src\atlas\research\population_topology.py`
- `src\atlas\research\reduction_metrics.py`
- `src\atlas\research\similarity.py`
- `src\atlas\research\statistical.py`
- `src\atlas\research\validation.py`
- `src\atlas\research\vectors.py`
- `src\atlas\resonance\similarity.py`
- `src\atlas\resonance\vector.py`
- `src\atlas\topology\structural_similarity.py`
- `tests\test_attractor_metrics_expansion.py`
- `tests\test_cluster_interpretation.py`
- ... 36 more

## Duplicate public function names


### `average`

- `src\atlas\classification\functional_role_v2.py`
- `src\atlas\fusion\translation.py`
- `src\atlas\ive\identity_vector.py`
- `src\atlas\ive\relationship_matrix.py`
- `src\atlas\ive\similarity.py`
- `src\atlas\measurement\structural_roles.py`

### `birth_data_to_dict`

- `src\atlas\birth\birth_data.py`
- `src\atlas\temporal\models.py`

### `build_identity_graph_summary`

- `src\atlas\graph\identity_graph.py`
- `src\atlas\identity\builder.py`

### `build_population_statistics`

- `src\atlas\calibration\population_statistics.py`
- `src\atlas\research\population.py`

### `build_topology_signature`

- `src\atlas\signatures\fingerprint.py`
- `src\atlas\topology\topology_signature.py`

### `build_undirected_adjacency`

- `src\atlas\graph\analysis.py`
- `src\atlas\graph\motifs.py`
- `src\atlas\research\graph_metrics.py`

### `clamp`

- `src\atlas\classification\functional_role_v2.py`
- `src\atlas\diagnostics\audit.py`
- `src\atlas\graph\coherence.py`
- `src\atlas\graph\identity_morphology.py`
- `src\atlas\graph\identity_resonance.py`
- `src\atlas\graph\structural_genome.py`
- `src\atlas\graph\structural_truth.py`
- `src\atlas\identity\builder.py`
- `src\atlas\ive\feature_vector.py`
- `src\atlas\ive\identity_vector.py`
- `src\atlas\ive\normalizer.py`
- `src\atlas\ive\relationship_matrix.py`
- `src\atlas\ive\similarity.py`
- `src\atlas\measurement\coverage.py`
- `src\atlas\measurement\organization.py`
- `src\atlas\measurement\structural_roles.py`
- `src\atlas\ontology\archetypes.py`
- `src\atlas\research\coherence_metrics.py`

### `classify_coherence`

- `src\atlas\graph\coherence.py`
- `src\atlas\research\coherence_metrics.py`

### `compute_degrees`

- `src\atlas\calibration\population_graph.py`
- `src\atlas\research\population_topology.py`

### `compute_distributions`

- `src\atlas\calibration\population_statistics.py`
- `src\atlas\calibration\population_statistics.py`

### `compute_profile_zscores`

- `src\atlas\calibration\zscore_engine.py`
- `src\atlas\research\zscores.py`

### `connected_components`

- `src\atlas\calibration\structural_clustering.py`
- `src\atlas\features\metrics.py`
- `src\atlas\graph\analysis.py`
- `src\atlas\research\population_topology.py`

### `cosine_similarity`

- `src\atlas\corpus\similarity.py`
- `src\atlas\ive\relationship_matrix.py`
- `src\atlas\research\similarity.py`

### `count_region`

- `src\atlas\graph\coherence.py`
- `src\atlas\resonance\field.py`

### `dict_to_dataframe`

- `dashboard\pages\identity_stack_lab.py`
- `dashboard\pages\morphology_lab.py`
- `dashboard\utils\dataframe.py`

### `euclidean_distance`

- `src\atlas\corpus\similarity.py`
- `src\atlas\features\clustering.py`
- `src\atlas\ive\relationship_matrix.py`

### `feature_variance`

- `src\atlas\ive\identity_vector.py`
- `src\atlas\research\validation.py`

### `find_articulation_points`

- `src\atlas\graph\analysis.py`
- `src\atlas\research\graph_metrics.py`

### `find_bridges`

- `src\atlas\graph\analysis.py`
- `src\atlas\research\graph_metrics.py`

### `format_float`

- `dashboard\components\classification_panel.py`
- `dashboard\components\functional_role_panel.py`
- `dashboard\components\ive_panel.py`
- `dashboard\components\observatory\functional_role_v2.py`
- `dashboard\pages\compare_profiles.py`
- `dashboard\pages\identity_stack_lab.py`
- `dashboard\pages\morphology_lab.py`
- `dashboard\pages\profile_observatory.py`
- `dashboard\pages\profile_test_lab.py`
- `dashboard\pages\role_calibration_lab.py`

### `format_percent`

- `dashboard\components\functional_role_panel.py`
- `dashboard\components\observatory\functional_role_v2.py`
- `dashboard\pages\role_calibration_lab.py`

### `format_table_value`

- `dashboard\components\ive_panel.py`
- `dashboard\pages\identity_stack_lab.py`
- `dashboard\pages\morphology_lab.py`

### `graph_density`

- `src\atlas\calibration\population_graph.py`
- `src\atlas\calibration\population_statistics.py`
- `src\atlas\research\attractor_metrics.py`

### `int_or_self`

- `src\atlas\research\coherence_metrics.py`
- `src\atlas\research\reduction_metrics.py`

### `is_numeric`

- `src\atlas\classification\role_calibration.py`
- `src\atlas\classification\role_diagnostics.py`
- `src\atlas\diagnostics\audit.py`

### `load_acf`

- `dashboard\pages\identity_stack_lab.py`
- `dashboard\pages\morphology_lab.py`

### `load_calibration_acfs`

- `dashboard\components\ive_panel.py`
- `dashboard\pages\compare_profiles.py`

### `load_matrix_rows`

- `dashboard\pages\profile_test_lab.py`
- `dashboard\pages\role_calibration_lab.py`

### `load_or_repair_acf`

- `dashboard\pages\compare_profiles.py`
- `dashboard\pages\profile_library.py`
- `dashboard\pages\profile_observatory.py`

### `load_profile_library_matrix`

- `dashboard\pages\population_topology.py`
- `dashboard\pages\population_validation.py`
- `dashboard\pages\statistical_intelligence.py`

### `load_profiles`

- `dashboard\pages\research_session.py`
- `dashboard\pages\temporal_intelligence.py`

### `max_key`

- `src\atlas\ive\identity_vector.py`
- `src\atlas\ive\similarity.py`

### `mean`

- `src\atlas\ablation\global_harness.py`
- `src\atlas\graph\identity_morphology.py`

### `min_key`

- `src\atlas\ive\identity_vector.py`
- `src\atlas\ive\similarity.py`

### `nakshatra_position_to_dict`

- `src\atlas\temporal\models.py`
- `src\atlas\temporal\nakshatra.py`

### `natal_chart_to_dict`

- `src\atlas\temporal\models.py`
- `src\atlas\temporal\natal_chart.py`

### `node_hover_text`

- `dashboard\components\observatory\graph_evolution_3d.py`
- `dashboard\pages\population_topology.py`

### `normalize_birth_time`

- `src\atlas\datasets\manager.py`
- `src\atlas\temporal\birth.py`

### `normalize_text`

- `src\atlas\ciphers.py`
- `src\atlas\datasets\manager.py`
- `src\atlas\temporal\birth.py`

### `normalized`

- `src\atlas\graph\coherence.py`
- `src\atlas\graph\structural_truth.py`

### `numeric_columns`

- `src\atlas\diagnostics\audit.py`
- `src\atlas\research\validation.py`

### `parse_birth_date`

- `src\atlas\temporal\ephemeris.py`
- `src\atlas\temporal\vimshottari_dasha.py`

### `percentile`

- `src\atlas\calibration\population_statistics.py`
- `src\atlas\research\distributions.py`

### `population_statistics_to_dict`

- `src\atlas\calibration\models.py`
- `src\atlas\calibration\population_statistics.py`

### `ratio`

- `src\atlas\graph\structural_genome.py`
- `src\atlas\graph\structural_truth.py`

### `render_cohorts`

- `dashboard\pages\population_validation.py`
- `dashboard\pages\statistical_intelligence.py`

### `render_correlation`

- `dashboard\pages\population_validation.py`
- `dashboard\pages\profile_test_lab.py`

### `render_exports`

- `dashboard\pages\population_topology.py`
- `dashboard\pages\population_validation.py`
- `dashboard\pages\research_session.py`
- `dashboard\pages\statistical_intelligence.py`
- `dashboard\pages\temporal_intelligence.py`

### `render_modifier_scores`

- `dashboard\components\functional_role_panel.py`
- `dashboard\components\observatory\functional_role_v2.py`

### `render_profile_consensus`

- `dashboard\components\observatory\functional_role_v2.py`
- `dashboard\pages\role_calibration_lab.py`

### `render_quality`

- `dashboard\components\ive_panel.py`
- `dashboard\pages\population_validation.py`

### `render_role_probabilities`

- `dashboard\components\functional_role_panel.py`
- `dashboard\components\observatory\functional_role_v2.py`

### `render_summary`

- `dashboard\components\functional_role_panel.py`
- `dashboard\pages\population_topology.py`
- `dashboard\pages\population_validation.py`
- `dashboard\pages\profile_test_lab.py`
- `dashboard\pages\temporal_intelligence.py`

### `render_variance`

- `dashboard\pages\population_validation.py`
- `dashboard\pages\profile_test_lab.py`

### `repeated_edges`

- `src\atlas\features\metrics.py`
- `src\atlas\topology\node_weights.py`

### `repeated_nodes`

- `src\atlas\features\metrics.py`
- `src\atlas\topology\node_weights.py`

### `safe_ratio`

- `src\atlas\calibration\population_statistics.py`
- `src\atlas\classification\role_calibration.py`
- `src\atlas\classification\role_diagnostics.py`
- `src\atlas\identity\builder.py`
- `src\atlas\measurement\coverage.py`
- `src\atlas\measurement\dynamics.py`
- `src\atlas\measurement\organization.py`
- `src\atlas\measurement\stability.py`
- `src\atlas\measurement\structural_roles.py`
- `src\atlas\research\graph_metrics.py`

### `sample_matrix`

- `tests\test_population_topology.py`
- `tests\test_population_validation.py`
- `tests\test_statistical_intelligence.py`

### `slugify`

- `dashboard\pages\population_intelligence.py`
- `dashboard\pages\population_observatory.py`
- `dashboard\pages\research_session.py`

### `test_build_chart`

- `tests\test_temporal_aspects.py`
- `tests\test_temporal_nakshatra.py`

### `test_chart_to_dict`

- `tests\test_temporal_aspects.py`
- `tests\test_temporal_nakshatra.py`

### `test_connected_components`

- `tests\test_metrics.py`
- `tests\test_structural_clustering.py`

### `unique_edges`

- `src\atlas\features\metrics.py`
- `src\atlas\topology\overlay.py`

### `unique_nodes`

- `src\atlas\features\metrics.py`
- `src\atlas\topology\overlay.py`

### `write_json`

- `dashboard\utils\io.py`
- `src\atlas\export\json.py`