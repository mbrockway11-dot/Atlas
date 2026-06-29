# Atlas Module Inventory

Generated static inventory for integration/refactor planning. This is an architectural aid, not a runtime truth source.

## Summary

- **src_py**: 266
- **dashboard_py**: 34
- **test_py**: 139
- **total_py**: 439

## Modules by package


### `tests`

| File | Purpose | Public API | Categories | Recommendation |
|---|---|---|---|---|
| `dashboard\atlas_dashboard.py` | dashboard | debug, safe_render, main | — | keep |
| `dashboard\components\__init__.py` | dashboard | — | graph_topology | keep |
| `dashboard\components\classification_panel.py` | dashboard | render_classification_panel, render_legacy_functional_role, render_expression, render_structural_state, render_planetary_topology, format_float | graph_topology | keep |
| `dashboard\components\functional_role_panel.py` | dashboard | render_functional_role_panel, render_summary, render_role_probabilities, render_modifier_scores, render_consensus, render_evidence, format_float, format_percent | graph_topology, confidence, reports, features | keep: multi-responsibility candidate |
| `dashboard\components\ive_panel.py` | dashboard | render_ive_panel, load_calibration_acfs, render_global_summary, render_planet_vectors, render_relationship_matrix, render_quality, format_float, format_table_value | graph_topology, reports, features | keep: multi-responsibility candidate |
| `dashboard\components\observatory\__init__.py` | dashboard | — | graph_topology | keep |
| `dashboard\components\observatory\calibration.py` | dashboard | render_calibration_view, calibration_dataframe | graph_topology | keep |
| `dashboard\components\observatory\functional_role_v2.py` | dashboard | render_functional_role_v2, render_role_probabilities, render_modifier_scores, render_profile_consensus, render_layer_results, format_float, format_percent | graph_topology | keep |
| `dashboard\components\observatory\graph_evolution_3d.py` | dashboard | render_graph_evolution_3d, build_graph_figure, build_node_positions, resolve_z, node_color, node_hover_text, render_graph_summary | graph_topology, reports | keep |
| `dashboard\components\observatory\header.py` | dashboard | render_observatory_header | graph_topology | keep |
| `dashboard\components\observatory\topology_3d.py` | dashboard | render_3d_topology_view, build_figure | graph_topology | keep |
| `dashboard\pages\__init__.py` | dashboard | — | — | keep |
| `dashboard\pages\compare_profiles.py` | dashboard | render_compare_profiles_page, load_or_repair_acf, load_calibration_acfs, render_ive_comparison, build_planet_agreement_from_vectors, render_similarity_summary, render_score_interpretation, render_planet_similarity, ... | similarity, reports, features | keep: multi-responsibility candidate |
| `dashboard\pages\identity_stack_lab.py` | dashboard | render_identity_stack_lab_page, load_acf, render_stack_audit, suggest_fix, render_graph_visualizations, render_cig_graph, render_stg_graph, has_graph_data, ... | graph_topology, reports | keep |
| `dashboard\pages\morphology_lab.py` | dashboard | render_morphology_lab_page, load_acf, render_morphology_summary, render_edit_counts, render_mutation_scores, render_genome_mutation, render_topology_mutation, render_resonance_mutation, ... | graph_topology, reports | keep |
| `dashboard\pages\population_intelligence.py` | dashboard | render_population_intelligence_page, render_summary_cards, render_cluster_table, render_neighbor_explorer, render_downloads, collect_matrix_identities, format_strongest_pair, slugify | similarity, clustering, reports, features | keep: multi-responsibility candidate |
| `dashboard\pages\population_observatory.py` | dashboard | render_population_observatory_page, load_population_records, render_population_summary, render_population_table, render_population_intelligence, render_profile_detail, slugify | reports | keep |
| `dashboard\pages\population_topology.py` | dashboard | render_population_topology_page, load_profile_library_matrix, attach_cohorts, render_summary, render_graph, build_positions, np_cos, np_sin, ... | graph_topology, reports, features | keep: multi-responsibility candidate |
| `dashboard\pages\population_validation.py` | dashboard | render_population_validation_page, load_profile_library_matrix, render_summary, render_quality, render_variance, render_neighbors, render_outliers, render_correlation, ... | similarity, statistics, reports, features | keep: multi-responsibility candidate |
| `dashboard\pages\profile_builder.py` | dashboard | render_profile_builder_page, render_legacy_classification_debug | — | keep |
| `dashboard\pages\profile_library.py` | dashboard | render_profile_library_page, load_or_repair_acf, render_legacy_library_debug | — | keep |
| `dashboard\pages\profile_observatory.py` | dashboard | render_profile_observatory_page, safe_section, load_or_repair_acf, render_identity_fingerprint, render_emanation_summary, render_composite_overlay, render_resonance_field, render_layer_explorer, ... | reports, features | keep |
| `dashboard\pages\profile_test_lab.py` | dashboard | render_profile_test_lab_page, load_matrix_rows, remove_legacy_columns, clean_dataframe, numeric_dataframe, render_summary, render_matrix, render_diagnostics, ... | statistics, reports, features | keep: multi-responsibility candidate |
| `dashboard\pages\research_corpus.py` | dashboard | render_research_corpus_page | — | keep |
| `dashboard\pages\research_session.py` | dashboard | render_research_session_page, load_profiles, render_session_summary, render_report, render_exports, slugify | reports | keep |
| `dashboard\pages\role_calibration_lab.py` | dashboard | render_role_calibration_lab_page, load_matrix_rows, render_health, render_role_distribution, render_metric_separation, render_learned_weights, render_profile_consensus, render_raw, ... | features | keep |
| `dashboard\pages\statistical_intelligence.py` | dashboard | render_statistical_intelligence_page, load_profile_library_matrix, render_overview, render_principal_components, render_clusters, render_silhouette, render_cohorts, render_exports | clustering, graph_topology, features | keep: multi-responsibility candidate |
| `dashboard\pages\temporal_intelligence.py` | dashboard | render_temporal_intelligence_page, load_profiles, render_summary, render_planets, render_houses, render_nakshatras, render_dignities, render_aspects, ... | reports, temporal | keep |
| `dashboard\pages\validation_lab.py` | dashboard | render_validation_lab_page, build_rows_for_profiles, render_variance_tab, render_correlation_tab, render_importance_tab, render_matrix_tab | statistics, features | keep |
| `dashboard\utils\__init__.py` | dashboard | — | — | keep |
| `dashboard\utils\classification.py` | dashboard | load_or_build_acf_classification | — | keep |
| `dashboard\utils\dataframe.py` | dashboard | dict_to_dataframe | — | keep |
| `dashboard\utils\graphs.py` | dashboard | build_graph | graph_topology | keep |
| `dashboard\utils\io.py` | dashboard | write_json, read_json | — | keep |
| `src\atlas\__init__.py` | general support | — | — | keep |
| `src\atlas\ablation\__init__.py` | general support | — | — | keep |
| `src\atlas\ablation\experiments.py` | general support | AblationExperiment, build_planet_experiments, build_feature_family_experiments, all_default_experiments | features | keep |
| `src\atlas\ablation\global_harness.py` | general support | GlobalAblationResult, run_global_ablation_experiment, run_default_global_ablation, summarize_profile_results, mean, global_ablation_result_to_dict | — | keep |
| `src\atlas\ablation\harness.py` | general support | AblationResult, run_ablation_experiment, apply_ablation, columns_for_experiment, ablation_result_to_dict | — | keep |
| `src\atlas\ablation\metrics.py` | general support | compute_rank_shift, compute_similarity_delta | similarity, features | keep |
| `src\atlas\ablation\reports.py` | general support | summarize_ablation_results, render_ablation_report_text, summarize_global_ablation_results, render_global_ablation_report_text | reports | keep |
| `src\atlas\ablation\visualization.py` | export/rendering | — | — | keep |
| `src\atlas\acf\__init__.py` | identity/profile construction | — | — | keep |
| `src\atlas\acf\builder.py` | identity/profile construction | build_acf_profile, export_acf_profile, add_classification_meanings, build_planetary_matrix, build_cipher_matrix, build_interpretation_seed | reports, features | keep |
| `src\atlas\birth\__init__.py` | identity/profile construction | — | temporal | keep |
| `src\atlas\birth\birth_data.py` | identity/profile construction | BirthData, birth_data_to_dict | temporal | keep |
| `src\atlas\calibration\baseline_library.py` | calibration/statistical validation | — | statistics | keep |
| `src\atlas\calibration\confidence_engine.py` | calibration/statistical validation | — | confidence | keep |
| `src\atlas\calibration\edge_normalization.py` | calibration/statistical validation | — | graph_topology | keep |
| `src\atlas\calibration\health_score.py` | calibration/statistical validation | — | — | keep |
| `src\atlas\calibration\models.py` | calibration/statistical validation | ProfileMetrics, MetricDistribution, PopulationStatistics, ProfileZScores, ConfidenceReport, HealthScore, CalibratedSimilarity, profile_metrics_to_dict, metric_distribution_to_dict, population_statistics_to_dict, profile_zscores_to_dict, confidence_report_to_dict, health_score_to_dict, calibrated_similarity_to_dict | similarity, statistics, confidence, reports, features | keep: multi-responsibility candidate |
| `src\atlas\calibration\nearest_neighbor.py` | calibration/statistical validation | NeighborResult, find_nearest_neighbors, build_neighbor_record, build_neighbor_summary, find_all_nearest_neighbors, collect_identities, neighbor_result_to_dict, all_neighbors_to_dict | similarity, reports, features | keep: multi-responsibility candidate |
| `src\atlas\calibration\population_graph.py` | calibration/statistical validation | PopulationGraph, build_population_graph, collect_population_nodes, build_node_record, collect_population_edges, build_edge_record, build_edge_id, build_population_graph_summary, compute_degrees, ... | similarity, graph_topology, reports | keep: multi-responsibility candidate |
| `src\atlas\calibration\population_statistics.py` | calibration/statistical validation | build_population_statistics, load_population_metrics, compute_distributions, extract_profile_metrics, profile_metrics_to_numeric_dict, compute_distributions, build_distribution, percentile, ... | similarity, graph_topology, statistics, confidence, features | keep: multi-responsibility candidate |
| `src\atlas\calibration\rarity_engine.py` | calibration/statistical validation | — | — | keep |
| `src\atlas\calibration\similarity_calibration.py` | calibration/statistical validation | — | similarity | keep |
| `src\atlas\calibration\similarity_engine.py` | calibration/statistical validation | SimilarityResult, compare_profile_metrics, metric_similarity, mean_score, clamp01, similarity_result_to_dict | similarity, graph_topology, features | keep: multi-responsibility candidate |
| `src\atlas\calibration\similarity_matrix.py` | calibration/statistical validation | SimilarityMatrix, build_similarity_matrix, build_similarity_matrix_from_library, build_similarity_matrix_summary, similarity_matrix_to_dict, export_similarity_matrix_json, export_similarity_matrix_csv | similarity, reports, features | keep: multi-responsibility candidate |
| `src\atlas\calibration\structural_clustering.py` | calibration/statistical validation | StructuralCluster, StructuralClusteringResult, build_structural_clusters, build_adjacency, connected_components, build_cluster, build_clustering_summary, structural_cluster_to_dict, structural_clustering_result_to_dict, export_structural_clusters_json | similarity, clustering, graph_topology, reports | keep: multi-responsibility candidate |
| `src\atlas\calibration\zscore_engine.py` | calibration/statistical validation | ProfileZScoreReport, compute_profile_zscores, compute_zscore, build_zscore_summary, zscore_report_to_dict | statistics, reports, features | keep: multi-responsibility candidate |
| `src\atlas\ciphers.py` | general support | normalize_text, english_ordinal_sequence, hebrew_literal_sequence, hebrew_phonetic_sequence, run_all_ciphers | — | keep |
| `src\atlas\civilization\__init__.py` | general support | — | — | keep |
| `src\atlas\classification\__init__.py` | classification/roles | — | — | keep |
| `src\atlas\classification\expression.py` | classification/roles | TopologicalExpression, classify_topological_expression | — | keep |
| `src\atlas\classification\functional_role.py` | classification/roles | FunctionalRole, classify_functional_role, classify_confidence, functional_role_to_dict | graph_topology, confidence | keep |
| `src\atlas\classification\functional_role_v2.py` | classification/roles | classify_functional_role_v2, classify_profile_functional_role_v2, score_functional_roles, score_modifiers, normalize_scores, build_evidence_summary, average_score_dicts, empty_classification, ... | graph_topology, confidence, reports, features | keep: multi-responsibility candidate |
| `src\atlas\classification\meanings.py` | classification/roles | get_functional_role_meaning, get_expression_meaning, get_structural_state_meaning, get_planetary_topology_meaning | graph_topology | keep |
| `src\atlas\classification\profile_classifier.py` | classification/roles | AtlasClassification, classify_signature, classification_to_dict | — | keep |
| `src\atlas\classification\role_calibration.py` | calibration/statistical validation | calibrate_functional_roles_v2, build_metric_separation, build_learned_role_weights, normalize_weight_records, build_role_distribution, detect_role_drift, empty_calibration_report, is_numeric, ... | reports, features | keep |
| `src\atlas\classification\role_diagnostics.py` | classification/roles | audit_functional_roles_v2, group_rows_by_profile, role_distribution, modifier_distribution, confidence_summary, evidence_metric_distribution, role_metric_signal, profile_consensus, ... | confidence, reports, features | keep: multi-responsibility candidate |
| `src\atlas\classification\structural_state.py` | classification/roles | StructuralState, classify_structural_state | — | keep |
| `src\atlas\coherence\__init__.py` | general support | — | — | keep |
| `src\atlas\coherence\summary.py` | general support | — | reports | keep |
| `src\atlas\comparison\__init__.py` | general support | — | — | keep |
| `src\atlas\comparison\compare.py` | general support | IdentityComparison, compare_profiles, build_planet_difference_summary, infer_planet_from_feature, classify_difference, build_comparison_interpretation, identity_comparison_to_dict | reports, features | keep |
| `src\atlas\comparison\features.py` | general support | — | features | keep |
| `src\atlas\comparison\interpretation.py` | general support | — | reports | keep |
| `src\atlas\comparison\planet_matrix.py` | general support | PlanetAgreementRow, PlanetAgreementMatrix, compare_planet_agreement | features | keep |
| `src\atlas\comparison\planets.py` | general support | — | — | keep |
| `src\atlas\core\__init__.py` | general support | — | — | keep |
| `src\atlas\core\constants.py` | general support | — | — | keep |
| `src\atlas\core\normalization.py` | general support | normalize_name, compact_name | — | keep |
| `src\atlas\core\utilities.py` | general support | — | — | keep |
| `src\atlas\corpus\__init__.py` | corpus/library/storage | — | — | keep |
| `src\atlas\corpus\builder.py` | corpus/library/storage | build_research_corpus, load_profile_acfs, flatten_profile_record, add_translation_fusion_fields | — | keep |
| `src\atlas\corpus\diagnostics.py` | corpus/library/storage | CorpusFeatureDiagnostics, numeric_feature_columns, build_feature_diagnostics, find_highly_correlated_pairs, diagnostics_to_dict, build_feature_diagnostics_from_csv | features | keep |
| `src\atlas\corpus\duplicates.py` | corpus/library/storage | DuplicateDetectionResult, canonicalize_name, name_tokens, detect_duplicate_names, detect_possible_aliases, detect_duplicates_and_aliases, alias_similarity_score, alias_reason, duplicate_detection_result_to_dict | similarity | keep |
| `src\atlas\corpus\export.py` | corpus/library/storage | export_corpus_rows | — | keep |
| `src\atlas\corpus\loader.py` | corpus/library/storage | load_corpus_csv | — | keep |
| `src\atlas\corpus\schema.py` | corpus/library/storage | build_corpus_metadata | — | keep |
| `src\atlas\corpus\search.py` | corpus/library/storage | CorpusSearch | — | keep |
| `src\atlas\corpus\similarity.py` | corpus/library/storage | find_nearest_profiles, explain_profile_difference, numeric_similarity_columns, standardize_features, similarity_score, distance_score, euclidean_distance, manhattan_distance, ... | similarity, features | keep |
| `src\atlas\corpus\statistics.py` | corpus/library/storage | build_corpus_statistics | — | keep |
| `src\atlas\corpus\validation.py` | corpus/library/storage | CorpusValidationResult, validate_profile_acfs, validate_profile_library, validation_result_to_dict | — | keep |
| `src\atlas\database\__init__.py` | corpus/library/storage | — | — | keep |
| `src\atlas\database\index.py` | corpus/library/storage | load_database_index, save_database_index, upsert_entity, list_entities, find_entity | — | keep |
| `src\atlas\datasets\__init__.py` | corpus/library/storage | — | — | keep |
| `src\atlas\datasets\manager.py` | corpus/library/storage | load_dataset, load_txt_dataset, load_csv_dataset, build_record_from_csv_row, validate_record, build_result, missing_file_result, has_error, ... | temporal | keep |
| `src\atlas\datasets\models.py` | corpus/library/storage | IdentityRecord, DatasetIssue, DatasetLoadResult, identity_record_to_dict, dataset_issue_to_dict, dataset_load_result_to_dict | — | keep |
| `src\atlas\diagnostics\__init__.py` | general support | — | — | keep |
| `src\atlas\diagnostics\audit.py` | general support | audit_research_matrix, numeric_columns, audit_metric, empty_metric_audit, most_common_ratio, score_metric_quality, quality_grade, diagnostic_statement, ... | features | keep |
| `src\atlas\essence\__init__.py` | identity/profile construction | — | — | keep |
| `src\atlas\essence\builder.py` | identity/profile construction | build_essence_graph | graph_topology | keep |
| `src\atlas\essence\export_svg.py` | identity/profile construction | export_essence_svg_3d | — | keep |
| `src\atlas\essence\profile.py` | identity/profile construction | build_essence_profile | — | keep |
| `src\atlas\explanation\__init__.py` | explanation/report language | — | — | keep |
| `src\atlas\explanation\archetypes.py` | explanation/report language | explain_archetype, explain_archetype_score | — | keep |
| `src\atlas\explanation\identity.py` | identity/profile construction | explain_identity_vector, balance_phrase, complexity_phrase, stability_phrase | features | keep |
| `src\atlas\explanation\measurements.py` | explanation/report language | explain_metric, explain_metric_value, classify_value | features | keep |
| `src\atlas\explanation\planets.py` | explanation/report language | explain_planet, explain_planet_feature | features | keep |
| `src\atlas\explanation\relationships.py` | explanation/report language | explain_relationship | — | keep |
| `src\atlas\explanation\roles.py` | explanation/report language | explain_role, explain_role_value | — | keep |
| `src\atlas\export\__init__.py` | export/rendering | — | — | keep |
| `src\atlas\export\composite_svg.py` | export/rendering | CompositeImageCell, export_composite_svg, composite_svg_to_string | — | keep |
| `src\atlas\export\csv.py` | export/rendering | export_nodes_csv, export_edges_csv, export_scores_csv, export_signature_csv | graph_topology | keep |
| `src\atlas\export\json.py` | export/rendering | graph_to_dict, scores_to_dict, signature_to_dict, resonance_to_dict, differential_to_dict, write_json, export_graph_json, export_scores_json, ... | graph_topology | keep |
| `src\atlas\export\svg.py` | export/rendering | export_graph_svg, export_graph_svg_3d, graph_to_svg, graph_to_svg_3d | graph_topology | keep |
| `src\atlas\features\__init__.py` | general support | — | features | keep |
| `src\atlas\features\cluster_interpretation.py` | general support | load_cluster_report, interpret_cluster_report, interpret_cluster, build_cluster_label, build_cluster_summary_lines, parse_feature_name, feature_label, describe_feature, ... | clustering, reports, features | keep: multi-responsibility candidate |
| `src\atlas\features\clustering.py` | general support | ClusterResult, cluster_corpus, build_feature_matrix, initialize_centroids, assign_clusters, recompute_centroids, build_assignment_rows, build_cluster_rows, dominant_cluster_features, ... | similarity, clustering, features | keep: multi-responsibility candidate |
| `src\atlas\features\metrics.py` | general support | node_count, edge_count, unique_nodes, unique_edges, repeated_nodes, repeated_edges, edge_density, in_degree, ... | graph_topology, features | keep |
| `src\atlas\features\scoring.py` | general support | TopologyScores, score_graph | graph_topology, features | keep |
| `src\atlas\fingerprint\__init__.py` | identity/profile construction | — | — | keep |
| `src\atlas\fingerprint\builder.py` | identity/profile construction | IdentityFingerprint, FunctionEngine, build_identity_fingerprint, build_fingerprint_dict, classify_individual_fingerprint | graph_topology | keep |
| `src\atlas\fusion\__init__.py` | general support | — | — | keep |
| `src\atlas\fusion\translation.py` | general support | PlanetTranslationFusion, TranslationFusionReport, build_translation_fusion_report, group_analyses_by_planet, build_planet_translation_fusion, extract_numeric_analysis_features, variance_to_agreement, average, planet_translation_fusion_to_dict, translation_fusion_report_to_dict | graph_topology, statistics, confidence, reports, features | keep: multi-responsibility candidate |
| `src\atlas\graph\__init__.py` | graph/topology algorithms | — | graph_topology | keep |
| `src\atlas\graph\analysis.py` | graph/topology algorithms | analyze_identity_graph, copy_graph, build_undirected_adjacency, build_directed_adjacency, attach_degree_metrics, connected_components, attach_components, find_bridges, ... | graph_topology, features | keep |
| `src\atlas\graph\attractor.py` | graph/topology algorithms | extract_structural_attractor | graph_topology | keep |
| `src\atlas\graph\canonical.py` | graph/topology algorithms | CanonicalIdentityGraph, build_canonical_identity_graph, build_cig_summary, canonical_identity_graph_to_dict | graph_topology, reports, features | keep: multi-responsibility candidate |
| `src\atlas\graph\coherence.py` | graph/topology algorithms | compute_coherence_field, compute_node_coherence, compute_edge_coherence, build_coherence_summary, count_region, top_by_coherence, classify_coherence, normalized, ... | graph_topology, reports | keep |
| `src\atlas\graph\identity_graph.py` | identity/profile construction | build_identity_graph_v2, empty_identity_graph, apply_construction_pass, apply_node_visit, apply_edge_visit, finalize_identity_graph, most_common_coordinate, build_identity_graph_summary, ... | graph_topology, reports | keep |
| `src\atlas\graph\identity_morphology.py` | identity/profile construction | IdentityMorphology, compare_identity_morphology, compare_motif_mutation, compare_genome_mutation, compare_topology_mutation, compare_resonance_mutation, compute_structural_edit_distance, classify_morphology, identity_morphology_to_dict, ... | similarity, graph_topology, reports | keep: multi-responsibility candidate |
| `src\atlas\graph\identity_resonance.py` | identity/profile construction | IdentityResonance, build_identity_resonance, compute_activation, compute_propagation, classify_resonance, classify_activation_pattern, classify_propagation_pattern, classify_damping_pattern, identity_resonance_to_dict, ... | graph_topology, reports | keep |
| `src\atlas\graph\identity_stack.py` | identity/profile construction | IdentityGraphStack, build_identity_graph_stack, build_stack_summary, identity_graph_stack_to_dict | graph_topology, reports | keep |
| `src\atlas\graph\identity_topology.py` | identity/profile construction | IdentityTopology, build_identity_topology, classify_topology, classify_flow_pattern, classify_organization_pattern, classify_stability_pattern, identity_topology_to_dict | graph_topology, reports | keep |
| `src\atlas\graph\motifs.py` | graph/topology algorithms | StructuralMotifs, extract_structural_motifs, build_undirected_adjacency, count_chain_motifs, count_triangle_motifs, count_star_motifs, count_cycle_like_motifs, undirected_edge_count, count_components, ... | graph_topology, reports | keep |
| `src\atlas\graph\reduction.py` | graph/topology algorithms | reduce_identity_graph, find_removable_leaf_noise, is_removable_leaf_noise, remove_nodes, build_reduced_summary, graph_copy, copy_record | graph_topology, reports | keep |
| `src\atlas\graph\stack_audit.py` | graph/topology algorithms | StackAuditIssue, StackAudit, audit_identity_stack, audit_construction_passes, audit_graph_connectivity, audit_hub_ratio, audit_edge_weight_distribution, audit_reduction_strength, stack_audit_to_dict, count_severity, ... | graph_topology, reports | keep |
| `src\atlas\graph\structural_genome.py` | graph/topology algorithms | StructuralGenome, build_structural_genome, compute_hierarchy_score, compute_branching_score, compute_cyclicity_score, compute_bottleneck_score, compute_persistence_score, build_genome_sequence, build_genome_summary, ... | graph_topology, reports | keep |
| `src\atlas\graph\structural_truth.py` | graph/topology algorithms | StructuralTruthGraph, build_structural_truth_graph, compute_node_truth, compute_edge_truth, build_stg_summary, structural_truth_graph_to_dict, classify_truth, top_truth_records, mean_truth, ... | graph_topology, confidence, reports | keep: multi-responsibility candidate |
| `src\atlas\identity\__init__.py` | identity/profile construction | — | graph_topology | keep |
| `src\atlas\identity\builder.py` | identity/profile construction | build_identity_layers, build_identity_graph, build_layer_similarity_edges, build_identity_graph_summary, score_identity_layer, safe_ratio, safe_float, clamp | similarity, graph_topology, reports | keep: multi-responsibility candidate |
| `src\atlas\identity\layer.py` | identity/profile construction | IdentityLayer, identity_layer_to_dict | graph_topology | keep |
| `src\atlas\identity\persistence.py` | identity/profile construction | build_identity_persistence, collect_node_records, collect_edge_records, split_by_persistence, enrich_persistence_record, build_node_trajectory_metrics, build_persistence_summary | graph_topology, reports, features | keep: multi-responsibility candidate |
| `src\atlas\identity\similarity.py` | identity/profile construction | layer_subtype_vector, layer_feature_vector, compare_identity_layers | similarity, features | keep |
| `src\atlas\identity\summary.py` | identity/profile construction | — | reports | keep |
| `src\atlas\identity_bridge.py` | identity/profile construction | AtlasIdentity, build_atlas_identity, build_temporal_payload, load_json_file, atlas_identity_to_dict, export_atlas_identity | temporal | keep |
| `src\atlas\importance\__init__.py` | general support | — | features | keep |
| `src\atlas\importance\ablation_importance.py` | general support | AblationImportanceRow, load_global_ablation_report, build_importance_from_global_ablation, importance_rows_to_dicts, export_importance_report, render_importance_report_text | reports, features | keep |
| `src\atlas\intelligence\__init__.py` | explanation/report language | — | — | keep |
| `src\atlas\intelligence\analogs.py` | explanation/report language | — | — | keep |
| `src\atlas\intelligence\confidence.py` | explanation/report language | — | confidence | keep |
| `src\atlas\intelligence\engine.py` | explanation/report language | — | — | keep |
| `src\atlas\intelligence\evidence.py` | explanation/report language | — | confidence | keep |
| `src\atlas\intelligence\explanation.py` | explanation/report language | — | — | keep |
| `src\atlas\intelligence\interpreter.py` | explanation/report language | InterpretationSection, AtlasInterpretation, interpret_identity, interpret_identity_overview, interpret_temporal_overview, interpret_natal_signature, interpret_dasha_state, interpret_transit_state, interpret_research_flags, format_sign_degree, ... | graph_topology, reports, temporal | keep: multi-responsibility candidate |
| `src\atlas\intelligence\prototypes.py` | explanation/report language | — | — | keep |
| `src\atlas\intelligence\recommendations.py` | explanation/report language | — | — | keep |
| `src\atlas\intelligence\report.py` | explanation/report language | AtlasReport, build_atlas_report, render_report_summary, render_section, atlas_report_to_dict, export_atlas_report_markdown, export_atlas_report_json | reports | keep |
| `src\atlas\interpretation\__init__.py` | general support | — | reports | keep |
| `src\atlas\interpretation\identity.py` | identity/profile construction | IdentityInterpretation, interpret_identity_vector, identity_interpretation_to_dict, build_identity_summary_lines, build_global_interpretation, build_planet_interpretations, build_archetype_interpretations, strongest_numeric_feature | reports, features | keep |
| `src\atlas\interpretation\profile.py` | general support | ProfileInterpretation, interpret_profile_summary, profile_interpretation_to_dict | reports | keep |
| `src\atlas\interpretation\rules.py` | general support | interpret_driver, interpret_amplifier, interpret_regulator, interpret_pattern, interpret_motif, interpret_signature | reports | keep |
| `src\atlas\invariant\__init__.py` | general support | — | — | keep |
| `src\atlas\invariant\features.py` | general support | InvariantFeatures, extract_invariant_features, invariant_features_to_dict | graph_topology, features | keep |
| `src\atlas\invariant\pipeline.py` | general support | run_invariant_pipeline, normalize_input, build_sequence_summary, score_kamea, rank_kameas, build_planetary_weight_distribution, build_planetary_contrast_distribution, build_consensus_subtype, ... | reports | keep |
| `src\atlas\invariant\rotations.py` | general support | rotate_90, rotate_180, rotate_270, mirror_x, mirror_y, transform_path, all_invariant_orientations | — | keep |
| `src\atlas\invariant\subtype.py` | general support | InvariantSubtype, classify_invariant_subtype, score_invariant_subtypes, invariant_subtype_to_dict | — | keep |
| `src\atlas\ive\__init__.py` | general support | — | features | keep |
| `src\atlas\ive\composite.py` | general support | build_composite_planet_vector, build_composite_planet_vectors, composite_vectors_to_feature_table, ordered_planets | features | keep |
| `src\atlas\ive\diagnostics.py` | general support | — | — | keep |
| `src\atlas\ive\export.py` | export/rendering | — | — | keep |
| `src\atlas\ive\feature_vector.py` | general support | build_planet_feature_vector, build_layer_vector_features, clamp | features | keep |
| `src\atlas\ive\identity_vector.py` | identity/profile construction | build_identity_vector, build_raw_vectors_from_acf, build_identity_global_features, build_identity_quality, build_identity_diagnostics, ordered_planet_vectors, mean_feature, feature_variance, ... | statistics, features | keep |
| `src\atlas\ive\normalizer.py` | general support | normalize_planet_vector, normalize_planet_vectors, comparable_vectors, normalize_feature_value, percentile_rank, minmax_scale, zscore_to_unit, clamp | statistics, features | keep |
| `src\atlas\ive\relationship_matrix.py` | general support | PlanetRelationshipMatrix, build_planet_relationship_matrix, cosine_similarity, euclidean_distance, feature_agreement, build_relationship_diagnostics, relationship_matrix_to_dict, validate_relationship_matrix, average, ... | similarity, features | keep |
| `src\atlas\ive\schema.py` | general support | PlanetFeatureVector, NormalizedPlanetVector, CompositePlanetVector, IdentityVector, planet_feature_vector_to_dict, normalized_planet_vector_to_dict, composite_planet_vector_to_dict, identity_vector_to_dict, validate_feature_vector, validate_normalized_vector, validate_composite_vector, validate_identity_vector, ... | features | keep |
| `src\atlas\ive\similarity.py` | general support | IdentityVectorSimilarity, compare_identity_vectors, compare_relationships, global_feature_distance, cosine_similarity_from_lists, identity_similarity_to_dict, validate_identity_similarity, average, max_key, ... | similarity, features | keep |
| `src\atlas\kamea\__init__.py` | general support | — | — | keep |
| `src\atlas\kamea\base.py` | general support | PlanetaryKamea | — | keep |
| `src\atlas\kamea\path.py` | general support | KameaPath | — | keep |
| `src\atlas\kamea\path_views.py` | general support | build_kamea_path_views | — | keep |
| `src\atlas\kamea\planetary_transform.py` | general support | transform_values_for_planet, transform_value | — | keep |
| `src\atlas\kamea\projection.py` | general support | get_kamea, project_values_to_kamea, project_values_to_all_kameas | — | keep |
| `src\atlas\kamea\squares.py` | general support | — | — | keep |
| `src\atlas\kamea\validation.py` | general support | ValidationReport | reports | keep |
| `src\atlas\kamea\visit_history.py` | general support | NodeVisit, build_node_visit_history, node_visit_to_dict | graph_topology | keep |
| `src\atlas\library\__init__.py` | corpus/library/storage | — | — | keep |
| `src\atlas\library\profile_library.py` | corpus/library/storage | save_profile_to_library, list_saved_profiles, load_profile_summary, load_profile_interpretation, profile_exists, safe_name | reports | keep |
| `src\atlas\measurement\__init__.py` | general support | — | features | keep |
| `src\atlas\measurement\coverage.py` | general support | CoverageMeasurement, measure_coverage, axis_coverage, boundary_coverage, core_coverage, safe_ratio, clamp | — | keep |
| `src\atlas\measurement\dynamics.py` | general support | DynamicsMeasurement, measure_dynamics, directional_bias, distance, safe_ratio | similarity | keep |
| `src\atlas\measurement\organization.py` | general support | OrganizationMeasurement, measure_organization, density, cluster_count, entropy, axis_strength, reciprocity, compression_ratio, safe_ratio, ... | clustering | keep |
| `src\atlas\measurement\stability.py` | general support | StabilityMeasurement, measure_stability, safe_ratio | — | keep |
| `src\atlas\measurement\structural_roles.py` | general support | StructuralRoleMeasurement, measure_structural_roles, incoming_counts, outgoing_counts, degree_counts, core_score, hub_score, bridge_score, attractor_score, ... | — | keep |
| `src\atlas\motifs\__init__.py` | general support | — | — | keep |
| `src\atlas\motifs\catalog.py` | general support | MotifCounts | — | keep |
| `src\atlas\motifs\detector.py` | general support | detect_motifs, count_chain_nodes, count_hubs, count_self_loops, count_reciprocal_pairs, count_dead_ends, count_isolated_nodes, count_bridge_edges | graph_topology | keep |
| `src\atlas\motifs\identity.py` | identity/profile construction | detect_identity_graph_motifs, detect_chain_motifs, detect_hub_motifs, detect_leaf_motifs, detect_articulation_motifs, detect_bridge_motifs, detect_reciprocal_edge_motifs, build_node_motif, ... | graph_topology, reports | keep |
| `src\atlas\motifs\matcher.py` | general support | — | — | keep |
| `src\atlas\motifs\statistics.py` | general support | total_motifs, motif_density, dominant_motif | — | keep |
| `src\atlas\natal\__init__.py` | general support | — | — | keep |
| `src\atlas\ontology\__init__.py` | general support | — | — | keep |
| `src\atlas\ontology\archetypes.py` | general support | list_archetypes, get_archetype, score_archetype, score_archetypes, rank_archetypes, clamp | — | keep |
| `src\atlas\ontology\identity.py` | identity/profile construction | synthesize_identity_ontology, build_ontology_summary | reports | keep |
| `src\atlas\ontology\motifs.py` | general support | — | — | keep |
| `src\atlas\ontology\planetary_bias.py` | general support | — | — | keep |
| `src\atlas\ontology\structural_roles.py` | general support | explain_structural_role, rank_structural_roles | — | keep |
| `src\atlas\ontology\synthesis.py` | general support | — | — | keep |
| `src\atlas\overlay\__init__.py` | general support | — | — | keep |
| `src\atlas\overlay\composite_overlay.py` | general support | build_composite_overlay, build_composite_nodes, build_composite_edges, normalize_composite_records, calculate_resonance_score, build_overlay_summary, top_by_resonance, format_layer_occurrences, ... | graph_topology, reports | keep |
| `src\atlas\profiles\__init__.py` | general support | — | reports | keep |
| `src\atlas\profiles\composite.py` | general support | build_composite_profile_manifest, write_composite_profile_manifest | — | keep |
| `src\atlas\profiles\summary.py` | general support | build_individual_profile_summary | reports | keep |
| `src\atlas\provenance.py` | general support | build_provenance_report, inspect_module | reports | keep |
| `src\atlas\reports\__init__.py` | general support | — | reports | keep |
| `src\atlas\reports\markdown.py` | general support | build_profile_markdown_report, write_markdown_report, format_metric | reports, features | keep |
| `src\atlas\research\__init__.py` | research matrix/session/validation | — | — | keep |
| `src\atlas\research\attractor_metrics.py` | research matrix/session/validation | build_layer_attractor_metrics, extract_layer_attractor, graph_density, build_attractor_signature, empty_attractor_metrics | graph_topology, features | keep |
| `src\atlas\research\baselines.py` | research matrix/session/validation | build_population_baselines, get_metric_baseline | statistics, features | keep |
| `src\atlas\research\coherence_metrics.py` | research matrix/session/validation | build_layer_coherence_metrics, score_node_coherence, score_edge_coherence, classify_coherence, region_ratio, int_or_self, clamp | graph_topology, reports, features | keep: multi-responsibility candidate |
| `src\atlas\research\comparison.py` | research matrix/session/validation | compare_acf_profiles | — | keep |
| `src\atlas\research\differential.py` | research matrix/session/validation | ranked_differences, summarize_profile_difference | — | keep |
| `src\atlas\research\distributions.py` | research matrix/session/validation | build_metric_distributions, summarize_distribution, percentile | features | keep |
| `src\atlas\research\export_matrix.py` | research matrix/session/validation | export_research_matrix | features | keep |
| `src\atlas\research\feature_correlation.py` | research matrix/session/validation | build_feature_correlation_audit, pearson_correlation, classify_correlation | statistics, features | keep |
| `src\atlas\research\feature_importance.py` | research matrix/session/validation | compare_profile_feature_importance, pair_layers, summarize_feature_importance | features | keep |
| `src\atlas\research\feature_variance.py` | research matrix/session/validation | build_feature_variance_audit, classify_variance | statistics, features | keep |
| `src\atlas\research\graph_metrics.py` | research matrix/session/validation | build_layer_graph_metrics, build_undirected_adjacency, connected_component_sizes, find_bridges, find_articulation_points, safe_ratio | graph_topology, features | keep |
| `src\atlas\research\matrix.py` | research matrix/session/validation | build_research_matrix, build_profile_matrix_rows | features | keep |
| `src\atlas\research\motion.py` | research matrix/session/validation | build_dynamic_motion_profile, summarize_motion_features, summarize_motion_by_planet, classify_motion_role, build_motion_summary, compare_motion_profiles | reports, features | keep |
| `src\atlas\research\planetary_vectors.py` | research matrix/session/validation | build_planetary_vectors, calculate_consensus_strength | features | keep |
| `src\atlas\research\population.py` | research matrix/session/validation | build_population_statistics, summarize_metrics | statistics, features | keep |
| `src\atlas\research\population_topology.py` | research matrix/session/validation | cosine_similarity_matrix, euclidean_similarity_matrix, pairwise_similarity_matrix, build_population_topology_graph, compute_degrees, compute_weighted_degrees, adjacency, connected_components, ... | similarity, graph_topology, reports, features | keep: multi-responsibility candidate |
| `src\atlas\research\reduction_metrics.py` | research matrix/session/validation | build_layer_reduction_metrics, build_layer_reduction_graph, estimate_node_scores, reduce_graph_iteratively, dedupe_iteration_history, graph_state, graph_state_from_parts, adjacency_from_edges, ... | graph_topology, features | keep |
| `src\atlas\research\schema.py` | research matrix/session/validation | classify_column, audit_research_row, audit_research_rows, clean_research_row, clean_research_rows | — | keep |
| `src\atlas\research\session.py` | research matrix/session/validation | ResearchSession, build_research_session, research_session_to_dict, export_research_session_json, export_research_session_markdown | — | keep |
| `src\atlas\research\similarity.py` | research matrix/session/validation | cosine_similarity, absolute_distance, mean_absolute_distance, similarity_from_distance, extract_subtype_vector, extract_planetary_vector, extract_essence_function_vector | similarity, features | keep |
| `src\atlas\research\statistical.py` | research matrix/session/validation | principal_components, kmeans_clusters, cluster_summary, silhouette_scores, cohort_separation, build_statistical_intelligence_report, statistical_report_to_json | clustering, graph_topology, reports, features | keep: multi-responsibility candidate |
| `src\atlas\research\validation.py` | research matrix/session/validation | load_research_matrix, load_cohort_index, numeric_columns, corpus_summary, data_quality_checks, feature_variance, build_profile_feature_matrix, normalize_profile_features, ... | similarity, statistics, reports, features | keep: multi-responsibility candidate |
| `src\atlas\research\vectors.py` | research matrix/session/validation | build_layer_vector, build_profile_vectors | features | keep |
| `src\atlas\research\zscores.py` | research matrix/session/validation | compute_layer_zscores, compute_profile_zscores | statistics | keep |
| `src\atlas\resonance\__init__.py` | general support | — | — | keep |
| `src\atlas\resonance\alignment.py` | general support | hub_alignment, pattern_alignment, motif_alignment, directional_alignment, structural_alignment | graph_topology | keep |
| `src\atlas\resonance\clustering.py` | general support | GraphCluster, cluster_by_resonance | clustering, graph_topology | keep |
| `src\atlas\resonance\field.py` | general support | build_resonance_field, enrich_resonance_record, classify_field_region, build_resonance_summary, count_region, top_resonant | graph_topology, reports | keep |
| `src\atlas\resonance\resonance.py` | general support | ResonanceResult, calculate_resonance | — | keep |
| `src\atlas\resonance\similarity.py` | general support | node_jaccard_similarity, edge_jaccard_similarity, node_weight_similarity, edge_weight_similarity, topology_vector_similarity | similarity, graph_topology, features | keep: multi-responsibility candidate |
| `src\atlas\resonance\vector.py` | general support | TopologyVector, build_topology_vector, vector_to_tuple | graph_topology, features | keep |
| `src\atlas\signatures\__init__.py` | general support | — | graph_topology | keep |
| `src\atlas\signatures\compatibility.py` | general support | — | — | keep |
| `src\atlas\signatures\fingerprint.py` | identity/profile construction | build_topology_signature | graph_topology | keep |
| `src\atlas\signatures\graph_entropy.py` | graph/topology algorithms | node_weight_entropy | graph_topology | keep |
| `src\atlas\signatures\motif_detection.py` | general support | dominant_pattern, branching_level, reciprocity_level, compression_level | graph_topology | keep |
| `src\atlas\signatures\resonance.py` | general support | — | — | keep |
| `src\atlas\signatures\topology_signature.py` | general support | TopologySignature | graph_topology | keep |
| `src\atlas\temporal\__init__.py` | temporal calculations | — | temporal | keep |
| `src\atlas\temporal\aspects.py` | temporal calculations | Aspect, AspectChart, house_distance, build_aspect_chart, outgoing_aspects, incoming_aspects, aspect_chart_to_dict | similarity, temporal | keep |
| `src\atlas\temporal\atlas_overlay.py` | temporal calculations | — | temporal | keep |
| `src\atlas\temporal\birth.py` | identity/profile construction | build_birth_data_from_intake, load_birth_data_from_profile, normalize_text, normalize_birth_time, is_birth_time_known, normalize_optional_float | temporal | keep |
| `src\atlas\temporal\config.py` | temporal calculations | — | temporal | keep |
| `src\atlas\temporal\dasha.py` | temporal calculations | — | temporal | keep |
| `src\atlas\temporal\dignity.py` | temporal calculations | PlanetDignity, DignityChart, planetary_relationship, dignity_strength, build_dignity_chart, dignity_chart_to_dict | temporal | keep |
| `src\atlas\temporal\ephemeris.py` | temporal calculations | EphemerisResult, build_ephemeris, configure_ephemeris_path, birth_data_to_julian_day, parse_birth_date, parse_birth_time_to_decimal_hours, calculate_planets, calculate_body, build_planet_position, ... | temporal | keep |
| `src\atlas\temporal\geocoder.py` | temporal calculations | — | temporal | keep |
| `src\atlas\temporal\houses.py` | temporal calculations | HouseCusp, HousePlacement, HouseChart, build_house_chart, calculate_asc_mc, build_house_cusp, build_whole_sign_cusps, assign_planets_to_whole_sign_houses, whole_sign_house_for_sign, resolve_latitude, resolve_longitude, ... | temporal | keep |
| `src\atlas\temporal\models.py` | temporal calculations | BirthData, PlanetPosition, NatalChart, NakshatraPosition, TemporalOverlay, birth_data_to_dict, planet_position_to_dict, natal_chart_to_dict, nakshatra_position_to_dict, temporal_overlay_to_dict | temporal | keep |
| `src\atlas\temporal\nakshatra.py` | temporal calculations | NakshatraMetadata, NakshatraChart, longitude_to_nakshatra, build_nakshatra_chart, get_nakshatra_metadata, get_nakshatra_metadata_by_index, nakshatra_position_to_dict, nakshatra_metadata_to_dict, nakshatra_chart_to_dict | temporal | keep |
| `src\atlas\temporal\natal_chart.py` | temporal calculations | build_natal_chart, build_natal_chart_payload, natal_chart_to_dict | temporal | keep |
| `src\atlas\temporal\navamsa.py` | temporal calculations | navamsa_strategy, build_navamsa_chart, longitude_to_navamsa, navamsa_chart_to_dict | temporal | keep |
| `src\atlas\temporal\sidereal.py` | temporal calculations | SiderealChart, convert_ephemeris_to_sidereal, get_ayanamsa_degrees, resolve_ayanamsa_mode, convert_position_to_sidereal, sidereal_chart_to_dict | temporal | keep |
| `src\atlas\temporal\transits.py` | temporal calculations | TransitContact, TransitChart, build_transit_chart, build_transit_contacts, sign_distance, same_sign_contacts, opposition_contacts, count_same_sign_contacts, count_opposition_contacts, transit_contact_to_dict, ... | similarity, temporal | keep |
| `src\atlas\temporal\vargas.py` | temporal calculations | VargaPosition, VargaChart, register_varga_strategy, build_varga_chart, varga_chart_to_dict | temporal | keep |
| `src\atlas\temporal\vimshottari_dasha.py` | temporal calculations | DashaPeriod, VimshottariDasha, build_vimshottari_dasha, compute_nakshatra_fraction_remaining, build_mahadasha_periods, rotate_sequence_to_lord, total_period_years, parse_birth_date, dasha_period_to_dict, vimshottari_dasha_to_dict | temporal | keep |
| `src\atlas\temporal\yoga_engine.py` | temporal calculations | YogaMatch, YogaEvaluation, evaluate_all_yogas, evaluate_yoga, evaluate_condition, evaluate_conjunction, evaluate_minimum_strength, evaluate_debilitated, evaluate_placeholder, yoga_evaluation_to_dict | temporal | keep |
| `src\atlas\temporal\yoga_rules.py` | temporal calculations | YogaCondition, YogaRule, get_yoga, all_yogas | temporal | keep |
| `src\atlas\temporal\yogas.py` | temporal calculations | — | temporal | keep |
| `src\atlas\topology\__init__.py` | general support | — | graph_topology | keep |
| `src\atlas\topology\branch_pruning.py` | general support | prune_graph, prune_isolated_nodes, prune_edges_below_weight | graph_topology | keep |
| `src\atlas\topology\differential.py` | general support | GraphDifferential, compare_graphs | graph_topology | keep |
| `src\atlas\topology\graph.py` | graph/topology algorithms | TopologyGraph | graph_topology | keep |
| `src\atlas\topology\graph_builder.py` | graph/topology algorithms | build_graph_from_kamea_path | graph_topology | keep |
| `src\atlas\topology\node_weights.py` | general support | get_node_weight, get_edge_weight, repeated_nodes, repeated_edges, node_depth, edge_reinforcement, max_node_weight, max_edge_weight, ... | graph_topology | keep |
| `src\atlas\topology\overlay.py` | general support | overlay_graphs, overlay_pair, shared_nodes, shared_edges, unique_nodes, unique_edges | graph_topology | keep |
| `src\atlas\topology\structural_similarity.py` | general support | StructuralSimilarity, compare_structural_similarity | similarity, graph_topology, features | keep: multi-responsibility candidate |
| `src\atlas\topology\topology_signature.py` | general support | TopologySignature, TopologySignatureSimilarity, build_topology_signature, compare_topology_signatures, topology_signature_to_dict, topology_signature_similarity_to_dict | similarity, graph_topology | keep |
| `src\atlas\transits\__init__.py` | general support | — | temporal | keep |
| `src\atlas\visualization\__init__.py` | export/rendering | — | — | keep |
| `src\atlas\visualization\canonical_graph_plot.py` | graph/topology algorithms | build_canonical_graph_figure | graph_topology | keep |
| `src\atlas\visualization\genome_plot.py` | export/rendering | — | — | keep |
| `src\atlas\visualization\graph_export.py` | graph/topology algorithms | — | graph_topology | keep |
| `src\atlas\visualization\graph_layout.py` | graph/topology algorithms | circular_layout, layered_layout | graph_topology | keep |
| `src\atlas\visualization\graph_styles.py` | graph/topology algorithms | — | graph_topology | keep |
| `src\atlas\visualization\morphology_plot.py` | export/rendering | — | — | keep |
| `src\atlas\visualization\planetary_composite.py` | export/rendering | render_planetary_composite_svg, export_planetary_composite_svg, render_layer_path, render_grid, render_legend, coordinate_to_svg_point, node_from_coordinate, svg_header, ... | graph_topology | keep |
| `src\atlas\visualization\render_options.py` | export/rendering | RenderOptions | — | keep |
| `src\atlas\visualization\topology_3d.py` | export/rendering | build_3d_topology_points, build_3d_topology_edges, resolve_z_value | graph_topology | keep |
| `src\atlas\visualization\topology_plot.py` | export/rendering | — | graph_topology | keep |
| `src\atlas\visualization\truth_graph_plot.py` | graph/topology algorithms | — | graph_topology | keep |
| `tests\run_name_pipeline.py` | tests | run_name_pipeline | — | keep |
| `tests\test_ablation.py` | tests | test_apply_ablation_removes_prefix_columns, test_build_default_experiments, test_run_ablation_experiment | — | keep |
| `tests\test_acf.py` | tests | test_build_acf_profile, test_export_acf_profile | — | keep |
| `tests\test_attractor_metrics_expansion.py` | tests | test_research_matrix_contains_attractor_metrics, test_attractor_metric_ranges_are_valid, test_attractor_signature_is_stable | features | keep |
| `tests\test_baselines.py` | tests | test_population_baselines | statistics | keep |
| `tests\test_birth_data.py` | tests | test_birth_data_to_dict_empty, test_birth_data_to_dict_populated, test_acf_profile_accepts_birth_data | temporal | keep |
| `tests\test_branch_pruning.py` | tests | test_prune_graph_by_node_weight, test_prune_graph_by_edge_weight, test_prune_isolated_nodes, test_prune_edges_below_weight | graph_topology | keep |
| `tests\test_canonical_identity_graph.py` | tests | test_build_canonical_identity_graph_from_minimal_acf | graph_topology | keep |
| `tests\test_ciphers.py` | tests | test_english_ordinal_sequence, test_hebrew_literal_sequence_is_letter_for_letter, test_hebrew_phonetic_sequence_combines_sound_groups, test_hebrew_literal_and_phonetic_differ_for_michael, test_run_all_ciphers | — | keep |
| `tests\test_classification.py` | tests | test_classify_signature_returns_layered_classification, test_classification_to_dict | — | keep |
| `tests\test_classification_meanings.py` | tests | test_functional_role_meanings, test_hybrid_functional_role_meaning, test_expression_meaning, test_structural_state_meaning, test_planetary_topology_meaning | graph_topology | keep |
| `tests\test_cluster_interpretation.py` | tests | test_parse_feature_name_planet, test_parse_feature_name_global, test_describe_feature, test_interpret_cluster, test_interpret_cluster_report | clustering, reports, features | keep: multi-responsibility candidate |
| `tests\test_clustering.py` | tests | test_cluster_corpus, test_cluster_result_to_dict | clustering | keep |
| `tests\test_coherence_metrics_expansion.py` | tests | test_research_matrix_contains_coherence_metrics, test_coherence_metric_ranges_are_valid, test_coherence_region_ratios_sum_to_one_when_present | features | keep |
| `tests\test_coherence_summary.py` | tests | — | reports | keep |
| `tests\test_comparison.py` | tests | test_compare_profiles, test_identity_comparison_to_dict | — | keep |
| `tests\test_composite_overlay.py` | tests | test_build_composite_overlay, test_composite_overlay_has_cross_layer_fields | — | keep |
| `tests\test_composite_svg.py` | tests | test_export_composite_svg | — | keep |
| `tests\test_corpus.py` | tests | test_build_research_corpus | — | keep |
| `tests\test_corpus_diagnostics.py` | tests | test_numeric_feature_columns_excludes_metadata, test_build_feature_diagnostics, test_diagnostics_to_dict | features | keep |
| `tests\test_corpus_duplicates.py` | tests | test_canonicalize_name, test_detect_duplicate_names, test_detect_possible_aliases | — | keep |
| `tests\test_corpus_search.py` | tests | test_load_search, test_contains, test_profile_names, test_search | — | keep |
| `tests\test_corpus_similarity.py` | tests | test_numeric_similarity_columns_excludes_constant_and_metadata, test_find_nearest_profiles_euclidean, test_find_nearest_profiles_manhattan, test_pearson_similarity_bounds, test_explain_profile_difference | similarity | keep |
| `tests\test_corpus_validation.py` | tests | test_validate_profile_acfs_valid, test_validate_profile_library_missing, test_validate_profile_library_detects_missing_acf | — | keep |
| `tests\test_database_index.py` | tests | test_load_database_index, test_upsert_entity, test_list_entities | — | keep |
| `tests\test_dataset_manager.py` | tests | test_load_missing_file, test_load_unsupported_file_type, test_load_txt_dataset, test_load_csv_dataset, test_load_csv_missing_required_name_column, test_load_csv_empty_name_row_is_invalid, test_load_csv_unknown_birth_time_info_issue, test_dataset_load_result_to_dict | temporal | keep |
| `tests\test_differential.py` | tests | test_compare_graphs_shared_and_unique_structure, test_compare_graphs_overlap_ratios, test_compare_empty_graphs | graph_topology | keep |
| `tests\test_distributions.py` | tests | test_metric_distributions | features | keep |
| `tests\test_essence.py` | tests | test_build_essence_graph, test_build_essence_profile | graph_topology | keep |
| `tests\test_explanation.py` | tests | test_explain_metric, test_explain_metric_value, test_explain_identity_vector | features | keep |
| `tests\test_explanation_extended.py` | tests | test_explain_planet, test_explain_role, test_explain_archetype, test_explain_relationship | — | keep |
| `tests\test_export_csv.py` | tests | test_export_nodes_csv, test_export_edges_csv, test_export_scores_csv | graph_topology | keep |
| `tests\test_export_differential_json.py` | tests | test_differential_to_dict_is_json_safe, test_export_differential_json | — | keep |
| `tests\test_export_json.py` | tests | test_graph_to_dict_is_json_safe, test_scores_to_dict, test_export_graph_json, test_export_scores_json, test_export_graph_with_scores_json | graph_topology | keep |
| `tests\test_export_matrix.py` | tests | test_export_research_matrix | features | keep |
| `tests\test_export_resonance_json.py` | tests | test_resonance_to_dict_is_json_safe, test_export_resonance_json, test_export_comparison_json | — | keep |
| `tests\test_export_signature_csv.py` | tests | test_export_signature_csv | — | keep |
| `tests\test_export_signature_json.py` | tests | test_signature_to_dict_is_json_safe, test_export_signature_json, test_export_graph_with_signature_json | graph_topology | keep |
| `tests\test_export_svg.py` | tests | test_graph_to_svg_contains_svg_elements, test_export_graph_svg, test_graph_to_svg_rejects_invalid_grid_size | graph_topology | keep |
| `tests\test_export_svg_3d.py` | tests | test_graph_to_svg_3d_contains_depth_elements, test_export_graph_svg_3d, test_graph_to_svg_3d_rejects_invalid_grid_size | graph_topology | keep |
| `tests\test_feature_correlation.py` | tests | test_build_feature_correlation_audit | statistics, features | keep |
| `tests\test_feature_importance.py` | tests | test_compare_profile_feature_importance, test_summarize_feature_importance | features | keep |
| `tests\test_feature_variance.py` | tests | test_build_feature_variance_audit | statistics, features | keep |
| `tests\test_functional_role_v2.py` | tests | test_functional_role_v2_scores_are_normalized, test_functional_role_v2_raw_scores_are_bounded, test_functional_role_v2_modifier_scores_are_bounded, test_profile_functional_role_v2_classification, test_normalize_scores_handles_zero_scores | — | keep |
| `tests\test_global_ablation.py` | tests | test_run_global_ablation_experiment, test_global_ablation_result_to_dict | — | keep |
| `tests\test_graph_metrics_expansion.py` | tests | test_research_matrix_contains_graph_metrics, test_graph_metric_ranges_are_valid | graph_topology, features | keep |
| `tests\test_identity_bridge.py` | tests | test_build_atlas_identity, test_atlas_identity_to_dict, test_export_atlas_identity | — | keep |
| `tests\test_identity_fingerprint.py` | tests | test_build_identity_fingerprint, test_identity_fingerprint_pipeline_counts_are_coherent, test_identity_fingerprint_structural_attractor, test_identity_fingerprint_classification_is_individual_only, test_identity_fingerprint_is_deterministic | — | keep |
| `tests\test_identity_graph.py` | tests | test_build_identity_layers, test_build_identity_graph | graph_topology | keep |
| `tests\test_identity_graph_analysis.py` | tests | test_analyze_identity_graph, test_analyze_identity_graph_edges, test_identity_graph_analysis_counts | graph_topology | keep |
| `tests\test_identity_graph_coherence.py` | tests | test_classify_coherence, test_compute_coherence_field, test_coherence_summary_has_regions | graph_topology, reports | keep |
| `tests\test_identity_graph_motifs.py` | tests | test_detect_identity_graph_motifs, test_identity_motif_records_have_structure | graph_topology | keep |
| `tests\test_identity_graph_reduction.py` | tests | test_reduce_identity_graph, test_reduction_does_not_mutate_original_graph, test_reduction_converges_or_stops_safely | graph_topology | keep |
| `tests\test_identity_graph_stack.py` | tests | test_build_identity_graph_stack_from_minimal_acf | graph_topology | keep |
| `tests\test_identity_graph_v2.py` | tests | test_build_identity_graph_v2, test_identity_graph_v2_merges_nodes, test_identity_graph_v2_merges_edges | graph_topology | keep |
| `tests\test_identity_interpretation.py` | tests | test_interpret_identity_vector, test_identity_interpretation_to_dict | reports, features | keep |
| `tests\test_identity_morphology.py` | tests | test_compare_identity_morphology_between_two_stacks, test_identical_stacks_are_near_isomorphic | — | keep |
| `tests\test_identity_persistence.py` | tests | test_build_identity_persistence, test_persistent_nodes_include_trajectory_metrics | graph_topology, features | keep |
| `tests\test_identity_resonance.py` | tests | test_build_identity_resonance_from_topology, test_low_topology_classifies_as_low_resonance | graph_topology | keep |
| `tests\test_identity_topology.py` | tests | test_build_identity_topology_from_structural_genome, test_sparse_genome_classifies_as_distributed_sparse | graph_topology | keep |
| `tests\test_importance.py` | tests | test_build_importance_from_global_ablation, test_importance_rows_to_dicts | — | keep |
| `tests\test_intelligence_interpreter.py` | tests | test_interpret_identity, test_atlas_interpretation_to_dict | reports | keep |
| `tests\test_intelligence_report.py` | tests | test_build_atlas_report, test_atlas_report_to_dict, test_export_markdown, test_export_json | reports | keep |
| `tests\test_interpretation.py` | tests | test_interpret_signature_returns_lines, test_interpret_profile_summary, test_profile_interpretation_to_dict | reports | keep |
| `tests\test_invariant_features.py` | tests | test_extract_invariant_features_basic, test_extract_invariant_features_self_loop, test_invariant_features_to_dict | features | keep |
| `tests\test_invariant_pipeline.py` | tests | test_normalize_input, test_build_sequence_summary, test_run_invariant_pipeline | reports | keep |
| `tests\test_invariant_rotations.py` | tests | test_rotate_90, test_rotate_180, test_rotate_270, test_mirror_x, test_mirror_y, test_transform_path_identity, test_all_invariant_orientations | — | keep |
| `tests\test_invariant_subtype.py` | tests | test_score_invariant_subtypes, test_classify_invariant_subtype, test_invariant_subtype_to_dict | — | keep |
| `tests\test_ive_composite.py` | tests | build_normalized_vectors, test_build_composite_planet_vector, test_build_composite_planet_vectors_all_planets, test_composite_planet_vector_to_dict, test_composite_vectors_to_feature_table | features | keep |
| `tests\test_ive_feature_vector.py` | tests | test_build_planet_feature_vector, test_planet_feature_vector_to_dict, test_all_21_layers_build_valid_vectors | features | keep |
| `tests\test_ive_identity_vector.py` | tests | test_build_identity_vector, test_identity_vector_to_dict, test_identity_vector_with_calibration_acfs, test_identity_vector_diagnostics_have_expected_keys | features | keep |
| `tests\test_ive_normalizer.py` | tests | build_vectors, test_normalize_planet_vector_percentile, test_normalize_planet_vectors_all_layers, test_minmax_scale, test_percentile_rank, test_zscore_to_unit | statistics, features | keep |
| `tests\test_ive_relationship_matrix.py` | tests | test_build_planet_relationship_matrix, test_relationship_matrix_to_dict | features | keep |
| `tests\test_ive_similarity.py` | tests | test_compare_identity_vectors, test_identity_similarity_to_dict | similarity, features | keep |
| `tests\test_kamea_engine.py` | tests | test_all_kameas_validate_on_import, test_saturn_projection, test_projection_path, test_moon_is_valid | — | keep |
| `tests\test_kamea_path.py` | tests | test_kamea_path_edges_and_repeats | graph_topology | keep |
| `tests\test_kamea_path_views.py` | tests | test_build_kamea_path_views_preserves_analysis_and_dedupes_render | — | keep |
| `tests\test_kamea_validation.py` | tests | test_all_kameas_have_valid_reports | reports | keep |
| `tests\test_kamea_visit_history.py` | tests | test_build_node_visit_history_tracks_depth | graph_topology | keep |
| `tests\test_metrics.py` | tests | test_basic_graph_metrics, test_repeated_node_and_edge_metrics, test_edge_density, test_degree_metrics, test_connected_components, test_graph_symmetry | graph_topology, features | keep |
| `tests\test_motifs.py` | tests | test_detect_chain_and_dead_end, test_detect_hub, test_detect_self_loop_and_reciprocal_pair, test_detect_isolated_node, test_detect_motifs_bundle, test_motif_statistics | graph_topology | keep |
| `tests\test_nearest_neighbor.py` | tests | test_collect_identities, test_find_nearest_neighbors, test_find_nearest_neighbors_limit, test_find_nearest_neighbors_missing_identity, test_find_all_nearest_neighbors, test_neighbor_result_to_dict | similarity | keep |
| `tests\test_node_weights.py` | tests | test_node_weight_utilities, test_edge_weight_utilities, test_normalized_weights | graph_topology | keep |
| `tests\test_ontology.py` | tests | test_rank_archetypes, test_explain_structural_role, test_synthesize_identity_ontology | — | keep |
| `tests\test_overlay.py` | tests | test_overlay_graphs_sums_shared_weights, test_overlay_pair, test_shared_and_unique_nodes, test_shared_and_unique_edges | graph_topology | keep |
| `tests\test_planet_matrix.py` | tests | test_identical_fingerprints_have_high_similarity, test_planet_matrix_returns_all_planets, test_missing_planet_features_do_not_crash, test_confidence_is_averaged_per_planet, test_rows_include_feature_explanations | similarity, confidence, features | keep: multi-responsibility candidate |
| `tests\test_planetary_composite_svg.py` | tests | test_render_planetary_composite_svg | — | keep |
| `tests\test_planetary_transform.py` | tests | test_planetary_transform_changes_values_by_planet, test_projected_reduced_values_differ_across_large_kameas, test_projected_coordinates_differ_across_large_kameas | — | keep |
| `tests\test_planetary_vectors.py` | tests | test_planetary_vectors | features | keep |
| `tests\test_population.py` | tests | test_population_statistics | statistics | keep |
| `tests\test_population_graph.py` | tests | test_build_edge_id_is_stable, test_graph_density_empty_or_singleton, test_graph_density_regular_graph, test_build_population_graph, test_build_population_graph_threshold_filters_edges, test_compute_degrees, test_population_graph_to_dict, test_export_population_graph_json | graph_topology | keep |
| `tests\test_population_statistics.py` | tests | test_safe_ratio_handles_zero_denominator, test_safe_ratio_clamps_to_one, test_safe_ratio_returns_fraction, test_graph_density_handles_small_graph, test_graph_density_computes_density, test_graph_average_degree_handles_empty_graph, test_graph_average_degree_computes_average_degree, test_percentile_empty_values, ... | graph_topology, statistics, features | keep: multi-responsibility candidate |
| `tests\test_population_topology.py` | tests | sample_matrix, sample_features, test_cosine_similarity_matrix_is_square, test_build_population_topology_graph_keeps_top_k_edges, test_nodes_and_edges_dataframe_available, test_connected_components_detects_isolates, test_deterministic_communities_assigns_all_nodes | similarity, graph_topology, features | keep: multi-responsibility candidate |
| `tests\test_population_validation.py` | tests | sample_matrix, test_data_quality_checks_passes_complete_matrix, test_profile_feature_matrix_aggregates_to_one_row_per_profile, test_nearest_neighbors_returns_beta_for_alpha, test_outlier_scores_ranks_gamma_highest, test_correlated_feature_pairs_and_report_are_available | similarity, reports, features | keep: multi-responsibility candidate |
| `tests\test_profile_library.py` | tests | test_safe_name | — | keep |
| `tests\test_profile_summary.py` | tests | test_build_individual_profile_summary | reports | keep |
| `tests\test_provenance.py` | tests | test_build_provenance_report | reports | keep |
| `tests\test_reduction_metrics_expansion.py` | tests | test_research_matrix_contains_reduction_metrics, test_reduction_metric_ranges_are_valid | features | keep |
| `tests\test_reports.py` | tests | test_build_profile_markdown_report | reports | keep |
| `tests\test_research_comparison.py` | tests | test_compare_acf_profiles, test_summarize_profile_difference | — | keep |
| `tests\test_research_diagnostics.py` | tests | test_numeric_columns_excludes_metadata, test_audit_metric_returns_expected_fields, test_audit_research_matrix_returns_metrics, test_constant_metric_receives_low_grade | features | keep |
| `tests\test_research_matrix.py` | tests | test_build_profile_matrix_rows, test_build_research_matrix | features | keep |
| `tests\test_research_motion.py` | tests | test_classify_motion_role, test_build_dynamic_motion_profile, test_summarize_motion_features, test_summarize_motion_by_planet, test_build_motion_summary, test_compare_motion_profiles | reports, features | keep |
| `tests\test_research_schema.py` | tests | test_research_schema_classifies_known_columns, test_research_matrix_has_no_deprecated_columns, test_research_matrix_columns_are_known | features | keep |
| `tests\test_research_session.py` | tests | test_build_research_session, test_research_session_to_dict, test_export_research_session_json, test_export_research_session_markdown | — | keep |
| `tests\test_research_similarity.py` | tests | test_cosine_similarity_identical, test_absolute_distance, test_mean_absolute_distance, test_similarity_from_distance | similarity | keep |
| `tests\test_resonance.py` | tests | test_jaccard_similarity, test_weight_similarity, test_topology_vector, test_topology_vector_similarity_identical_graphs, test_structural_alignment_identical_graphs, test_calculate_resonance_identical_graphs, test_cluster_by_resonance | similarity, clustering, graph_topology, features | keep: multi-responsibility candidate |
| `tests\test_role_calibration.py` | tests | test_role_calibration_builds_report, test_metric_separation_has_expected_fields, test_learned_weights_are_normalized_per_role, test_role_drift_detection_statuses, test_calibration_metrics_list_is_not_empty | reports, features | keep |
| `tests\test_role_diagnostics.py` | tests | test_role_diagnostics_audits_research_rows, test_role_distribution_ratios_sum_to_one, test_profile_consensus_bounds_are_valid, test_group_rows_by_profile | — | keep |
| `tests\test_scoring.py` | tests | test_empty_graph_scores_zero, test_driver_score_detects_outward_force, test_amplifier_score_uses_repetition_and_density, test_regulator_score_rewards_balance_and_symmetry, test_scores_are_clamped_between_zero_and_one | graph_topology | keep |
| `tests\test_signatures.py` | tests | test_node_weight_entropy_zero_for_empty_graph, test_node_weight_entropy_detects_distribution, test_motif_detection_reciprocal, test_motif_detection_radiating, test_compression_level_high, test_build_topology_signature | graph_topology | keep |
| `tests\test_similarity_engine.py` | tests | test_metric_similarity_identical_values, test_metric_similarity_different_values, test_metric_similarity_zero_safe, test_compare_profile_metrics_identical_profiles, test_compare_profile_metrics_different_profiles, test_similarity_result_to_dict | similarity, features | keep |
| `tests\test_similarity_matrix.py` | tests | test_build_similarity_matrix_without_self, test_build_similarity_matrix_with_self, test_similarity_matrix_to_dict, test_export_similarity_matrix_json, test_export_similarity_matrix_csv | similarity, features | keep |
| `tests\test_stack_audit.py` | tests | test_audit_identity_stack_returns_valid_audit, test_audit_detects_visit_imbalance, test_audit_detects_high_hub_ratio | — | keep |
| `tests\test_statistical_intelligence.py` | tests | sample_matrix, sample_profile_features, test_principal_components_available, test_kmeans_clusters_assigns_every_profile, test_cluster_summary_counts_profiles, test_silhouette_scores_available, test_cohort_separation_available_with_index, test_statistical_report_contains_core_sections | clustering, graph_topology, reports, features | keep: multi-responsibility candidate |
| `tests\test_structural_attractor.py` | tests | test_structural_attractor_exists_from_fingerprint, test_structural_attractor_is_subset_of_reduced_graph, test_structural_attractor_edges_only_use_attractor_nodes, test_structural_attractor_summary_metrics_are_coherent, test_structural_attractor_is_deterministic, test_structural_attractor_empty_graph_does_not_crash | graph_topology, reports, features | keep: multi-responsibility candidate |
| `tests\test_structural_clustering.py` | tests | test_build_adjacency, test_connected_components, test_build_structural_clusters, test_structural_clustering_result_to_dict, test_export_structural_clusters_json | clustering, graph_topology | keep |
| `tests\test_structural_genome.py` | tests | test_build_structural_genome_from_truth_graph | graph_topology | keep |
| `tests\test_structural_motifs.py` | tests | test_extract_structural_motifs_from_triangle_graph, test_extract_structural_motifs_from_star_graph | graph_topology | keep |
| `tests\test_structural_roles.py` | tests | test_measure_structural_roles_returns_all_roles, test_oscillator_detects_aba_pattern | — | keep |
| `tests\test_structural_similarity.py` | tests | test_identical_graphs_have_full_structural_similarity, test_different_graphs_have_partial_similarity, test_weight_similarity_detects_weight_drift | similarity, graph_topology | keep |
| `tests\test_structural_truth_graph.py` | tests | test_build_structural_truth_graph_from_cig | graph_topology | keep |
| `tests\test_temporal_aspects.py` | tests | test_house_distance_same, test_house_distance_forward, test_house_distance_wrap, test_default_planets_only_aspect_seventh, test_mars_rules, test_jupiter_rules, test_saturn_rules, test_build_chart, ... | similarity, temporal | keep |
| `tests\test_temporal_birth.py` | tests | test_normalize_birth_time_unknown_values, test_normalize_birth_time_known_value, test_is_birth_time_known, test_normalize_optional_float, test_build_birth_data_from_intake, test_load_birth_data_from_profile, test_load_birth_data_missing_intake | temporal | keep |
| `tests\test_temporal_ephemeris.py` | tests | test_parse_birth_date, test_parse_negative_birth_date, test_parse_birth_time_to_decimal_hours, test_parse_birth_time_unknown_defaults_to_noon, test_normalize_degrees, test_build_planet_position, test_build_ephemeris, test_ephemeris_result_to_dict, ... | temporal | keep |
| `tests\test_temporal_houses.py` | tests | test_build_house_cusp, test_whole_sign_house_for_sign, test_build_whole_sign_cusps, test_assign_planets_to_whole_sign_houses, test_build_house_chart, test_build_house_chart_rejects_unsupported_house_system, test_house_chart_to_dict | temporal | keep |
| `tests\test_temporal_nakshatra.py` | tests | test_longitude_lookup, test_metadata_lookup, test_metadata_lookup_by_index, test_build_chart, test_chart_to_dict | temporal | keep |
| `tests\test_temporal_natal_chart.py` | tests | test_temporal_config_defaults, test_build_sidereal_natal_chart, test_build_tropical_natal_chart, test_build_natal_chart_rejects_bad_zodiac, test_build_natal_chart_payload | temporal | keep |
| `tests\test_temporal_navamsa.py` | tests | test_single_conversion, test_chart, test_serializer | temporal | keep |
| `tests\test_temporal_sidereal.py` | tests | test_resolve_ayanamsa_mode_supported, test_resolve_ayanamsa_mode_unsupported, test_get_ayanamsa_degrees, test_convert_position_to_sidereal, test_convert_ephemeris_to_sidereal, test_sidereal_chart_to_dict | temporal | keep |
| `tests\test_temporal_transits.py` | tests | test_sign_distance, test_build_transit_chart, test_contact_filters, test_transit_chart_to_dict | similarity, temporal | keep |
| `tests\test_temporal_vimshottari_dasha.py` | tests | test_rotate_sequence_to_lord, test_fraction_remaining_bounds, test_build_vimshottari_dasha, test_vimshottari_dasha_to_dict | temporal | keep |
| `tests\test_temporal_yoga_engine.py` | tests | test_evaluate_all_yogas, test_serialization | temporal | keep |
| `tests\test_topology_graph_builder.py` | tests | test_build_graph_from_kamea_path, test_graph_incoming_and_outgoing_edges | graph_topology | keep |
| `tests\test_topology_signature.py` | tests | test_identical_graph_signatures_are_fully_similar, test_different_graph_signatures_detect_structural_difference | graph_topology | keep |
| `tests\test_translation_fusion.py` | tests | test_build_translation_fusion_report, test_translation_fusion_report_to_dict | reports | keep |
| `tests\test_vectors.py` | tests | test_profile_vectors | features | keep |
| `tests\test_zscore_engine.py` | tests | test_compute_zscore_zero_standard_deviation, test_compute_zscore_regular_value, test_compute_profile_zscores, test_zscore_report_to_dict | statistics, reports | keep |
| `tests\test_zscores.py` | tests | test_layer_zscores, test_profile_zscores | statistics | keep |