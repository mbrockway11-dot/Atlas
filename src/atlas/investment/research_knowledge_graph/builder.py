"""Atlas Research Knowledge Graph construction."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.research_knowledge_graph.config import (
    SCHEMA_VERSION,
    SOURCE,
)
from atlas.investment.research_knowledge_graph.identity import (
    boolean,
    edge_id,
    node_id,
    text,
)


NODE_COLUMNS = [
    "node_id",
    "node_type",
    "natural_key",
    "label",
    "description",
    "status",
    "engine_id",
    "experiment_id",
    "hypothesis_id",
    "variant_id",
    "state_hash",
    "source_name",
    "production_eligible",
    "execution_instruction",
    "schema_version",
    "source",
]


EDGE_COLUMNS = [
    "edge_id",
    "source_node_id",
    "relationship_type",
    "target_node_id",
    "source_name",
    "experiment_id",
    "state_hash",
    "evidence",
    "execution_instruction",
    "schema_version",
    "source",
]


def build_knowledge_graph(
    sources: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    """Build canonical nodes and typed lineage edges."""
    experiments = sources.get(
        "experiments",
        pd.DataFrame(),
    )

    relationships = sources.get(
        "relationships",
        pd.DataFrame(),
    )

    variant_decisions = sources.get(
        "variant_decisions",
        pd.DataFrame(),
    )

    plans = sources.get(
        "implementation_plans",
        pd.DataFrame(),
    )

    compiler_report = sources.get(
        "compiler_report",
        {},
    )

    state_hash = text(
        compiler_report.get(
            "state_hash",
            "",
        )
    )

    nodes: list[dict] = []
    edges: list[dict] = []

    experiment_node_map: dict[str, str] = {}
    hypothesis_node_map: dict[str, str] = {}
    variant_node_map: dict[str, str] = {}
    engine_node_map: dict[str, str] = {}

    if (
        experiments is not None
        and not experiments.empty
    ):
        for _, row in (
            experiments.iterrows()
        ):
            data = row.to_dict()

            experiment_id = text(
                data.get(
                    "experiment_id"
                )
            )

            experiment_type = text(
                data.get(
                    "experiment_type"
                )
            ).upper()

            graph_type = map_experiment_type(
                experiment_type
            )

            natural_key = text(
                data.get(
                    "natural_key"
                )
            ) or experiment_id

            current_node_id = node_id(
                graph_type,
                natural_key,
            )

            experiment_node_map[
                experiment_id
            ] = current_node_id

            add_node(
                nodes=nodes,
                node_id_value=current_node_id,
                node_type=graph_type,
                natural_key=natural_key,
                label=text(
                    data.get(
                        "title"
                    )
                ) or natural_key,
                description=text(
                    data.get(
                        "description"
                    )
                ),
                status=text(
                    data.get(
                        "current_status"
                    )
                ),
                engine_id=text(
                    data.get(
                        "parent_engine_id"
                    )
                ),
                experiment_id=experiment_id,
                hypothesis_id=text(
                    data.get(
                        "hypothesis_id"
                    )
                ),
                variant_id=text(
                    data.get(
                        "variant_id"
                    )
                ),
                state_hash=text(
                    data.get(
                        "latest_state_hash"
                    )
                ) or state_hash,
                source_name=text(
                    data.get(
                        "latest_source"
                    )
                ),
                production_eligible=boolean(
                    data.get(
                        "production_eligible"
                    )
                ),
            )

            engine_id = text(
                data.get(
                    "parent_engine_id"
                )
            )

            if engine_id:
                engine_node = ensure_engine_node(
                    nodes=nodes,
                    engine_node_map=(
                        engine_node_map
                    ),
                    engine_id=engine_id,
                    state_hash=state_hash,
                )

                relationship_type = (
                    "GENERATED_HYPOTHESIS"
                    if graph_type
                    == "HYPOTHESIS"
                    else "DERIVED_FROM"
                )

                add_edge(
                    edges=edges,
                    source_node_id=engine_node,
                    relationship_type=(
                        relationship_type
                    ),
                    target_node_id=(
                        current_node_id
                    ),
                    source_name=(
                        "experiment_registry"
                    ),
                    experiment_id=(
                        experiment_id
                    ),
                    state_hash=state_hash,
                    evidence=engine_id,
                )

            hypothesis_id = text(
                data.get(
                    "hypothesis_id"
                )
            )

            if (
                graph_type == "HYPOTHESIS"
                and hypothesis_id
            ):
                hypothesis_node_map[
                    hypothesis_id
                ] = current_node_id

            variant_id = text(
                data.get(
                    "variant_id"
                )
            )

            if (
                graph_type == "VARIANT"
                and variant_id
            ):
                variant_node_map[
                    variant_id
                ] = current_node_id

    add_registry_relationships(
        relationships=relationships,
        edges=edges,
        experiment_node_map=(
            experiment_node_map
        ),
        state_hash=state_hash,
    )

    add_hypothesis_variant_edges(
        experiments=experiments,
        nodes=nodes,
        edges=edges,
        hypothesis_node_map=(
            hypothesis_node_map
        ),
        variant_node_map=(
            variant_node_map
        ),
        state_hash=state_hash,
    )

    add_decision_nodes(
        frame=variant_decisions,
        nodes=nodes,
        edges=edges,
        variant_node_map=(
            variant_node_map
        ),
        state_hash=state_hash,
    )

    add_plan_nodes(
        frame=plans,
        nodes=nodes,
        edges=edges,
        variant_node_map=(
            variant_node_map
        ),
        state_hash=state_hash,
    )

    add_state_node_and_edges(
        nodes=nodes,
        edges=edges,
        experiments=experiments,
        state_hash=state_hash,
    )

    node_frame = pd.DataFrame(
        nodes
    )

    edge_frame = pd.DataFrame(
        edges
    )

    if node_frame.empty:
        node_frame = pd.DataFrame(
            columns=NODE_COLUMNS
        )
    else:
        node_frame = (
            node_frame[
                NODE_COLUMNS
            ]
            .drop_duplicates(
                subset=["node_id"],
                keep="first",
            )
            .sort_values(
                [
                    "node_type",
                    "natural_key",
                ],
                kind="stable",
            )
            .reset_index(drop=True)
        )

    if edge_frame.empty:
        edge_frame = pd.DataFrame(
            columns=EDGE_COLUMNS
        )
    else:
        edge_frame = (
            edge_frame[
                EDGE_COLUMNS
            ]
            .drop_duplicates(
                subset=["edge_id"],
                keep="first",
            )
            .sort_values(
                [
                    "relationship_type",
                    "source_node_id",
                    "target_node_id",
                ],
                kind="stable",
            )
            .reset_index(drop=True)
        )

    return {
        "nodes": node_frame,
        "edges": edge_frame,
    }


def map_experiment_type(
    experiment_type: str,
) -> str:
    mapping = {
        "HYPOTHESIS": "HYPOTHESIS",
        "VALIDATED_VARIANT": "VARIANT",
        "PORTFOLIO_EXPERIMENT": (
            "PORTFOLIO_EXPERIMENT"
        ),
        "RESEARCH_CYCLE": (
            "RESEARCH_CYCLE"
        ),
    }

    return mapping.get(
        experiment_type,
        "HYPOTHESIS",
    )


def ensure_engine_node(
    *,
    nodes: list,
    engine_node_map: dict,
    engine_id: str,
    state_hash: str,
) -> str:
    if engine_id in engine_node_map:
        return engine_node_map[
            engine_id
        ]

    current_id = node_id(
        "ENGINE",
        engine_id,
    )

    engine_node_map[
        engine_id
    ] = current_id

    add_node(
        nodes=nodes,
        node_id_value=current_id,
        node_type="ENGINE",
        natural_key=engine_id,
        label=engine_id,
        description=(
            "Atlas alpha or research engine."
        ),
        status="REGISTERED",
        engine_id=engine_id,
        experiment_id="",
        hypothesis_id="",
        variant_id="",
        state_hash=state_hash,
        source_name=(
            "experiment_registry"
        ),
        production_eligible=False,
    )

    return current_id


def add_registry_relationships(
    *,
    relationships: pd.DataFrame,
    edges: list,
    experiment_node_map: dict,
    state_hash: str,
) -> None:
    if (
        relationships is None
        or relationships.empty
    ):
        return

    for _, row in relationships.iterrows():
        source_experiment = text(
            row.get(
                "from_experiment_id"
            )
        )

        target_experiment = text(
            row.get(
                "to_experiment_id"
            )
        )

        source_node = (
            experiment_node_map.get(
                source_experiment
            )
        )

        target_node = (
            experiment_node_map.get(
                target_experiment
            )
        )

        if not source_node or not target_node:
            continue

        raw_type = text(
            row.get(
                "relationship_type"
            )
        ).upper()

        relationship_type = {
            "GENERATED_VARIANT": (
                "PRODUCED_VARIANT"
            ),
        }.get(
            raw_type,
            "DERIVED_FROM",
        )

        add_edge(
            edges=edges,
            source_node_id=source_node,
            relationship_type=(
                relationship_type
            ),
            target_node_id=target_node,
            source_name=text(
                row.get(
                    "source_name"
                )
            ),
            experiment_id=(
                source_experiment
            ),
            state_hash=state_hash,
            evidence=text(
                row.get(
                    "evidence_hash"
                )
            ),
        )


def add_hypothesis_variant_edges(
    *,
    experiments: pd.DataFrame,
    nodes: list,
    edges: list,
    hypothesis_node_map: dict,
    variant_node_map: dict,
    state_hash: str,
) -> None:
    if (
        experiments is None
        or experiments.empty
    ):
        return

    for _, row in experiments.iterrows():
        variant_id = text(
            row.get(
                "variant_id"
            )
        )

        hypothesis_id = text(
            row.get(
                "hypothesis_id"
            )
        )

        if (
            not variant_id
            or not hypothesis_id
        ):
            continue

        source_node = (
            hypothesis_node_map.get(
                hypothesis_id
            )
        )

        target_node = (
            variant_node_map.get(
                variant_id
            )
        )

        if source_node and target_node:
            add_edge(
                edges=edges,
                source_node_id=source_node,
                relationship_type=(
                    "PRODUCED_VARIANT"
                ),
                target_node_id=target_node,
                source_name=(
                    "experiment_registry"
                ),
                experiment_id=text(
                    row.get(
                        "experiment_id"
                    )
                ),
                state_hash=state_hash,
                evidence=hypothesis_id,
            )


def add_decision_nodes(
    *,
    frame: pd.DataFrame,
    nodes: list,
    edges: list,
    variant_node_map: dict,
    state_hash: str,
) -> None:
    if frame is None or frame.empty:
        return

    for _, row in frame.iterrows():
        variant_id = text(
            row.get("variant_id")
        )

        decision = text(
            row.get(
                "manual_decision"
            )
        )

        if not variant_id or not decision:
            continue

        natural_key = (
            f"{variant_id}|{decision}|"
            f"{text(row.get('approval_version'))}"
        )

        decision_node = node_id(
            "DECISION",
            natural_key,
        )

        add_node(
            nodes=nodes,
            node_id_value=decision_node,
            node_type="DECISION",
            natural_key=natural_key,
            label=decision,
            description=text(
                row.get(
                    "manual_rationale"
                )
            ),
            status=decision,
            engine_id=text(
                row.get(
                    "parent_engine_id"
                )
            ),
            experiment_id="",
            hypothesis_id=text(
                row.get(
                    "hypothesis_id"
                )
            ),
            variant_id=variant_id,
            state_hash=state_hash,
            source_name=(
                "variant_decision_ledger"
            ),
            production_eligible=False,
        )

        variant_node = (
            variant_node_map.get(
                variant_id
            )
        )

        if variant_node:
            add_edge(
                edges=edges,
                source_node_id=variant_node,
                relationship_type=(
                    "RECEIVED_DECISION"
                ),
                target_node_id=decision_node,
                source_name=(
                    "variant_decision_ledger"
                ),
                experiment_id="",
                state_hash=state_hash,
                evidence=text(
                    row.get(
                        "manual_reviewer"
                    )
                ),
            )


def add_plan_nodes(
    *,
    frame: pd.DataFrame,
    nodes: list,
    edges: list,
    variant_node_map: dict,
    state_hash: str,
) -> None:
    if frame is None or frame.empty:
        return

    for _, row in frame.iterrows():
        plan_id = text(
            row.get("plan_id")
        )

        variant_id = text(
            row.get("variant_id")
        )

        if not plan_id:
            continue

        plan_node = node_id(
            "IMPLEMENTATION_PLAN",
            plan_id,
        )

        add_node(
            nodes=nodes,
            node_id_value=plan_node,
            node_type=(
                "IMPLEMENTATION_PLAN"
            ),
            natural_key=plan_id,
            label=text(
                row.get(
                    "variant_name"
                )
            ) or plan_id,
            description=text(
                row.get(
                    "gate_expression"
                )
            ),
            status=text(
                row.get(
                    "plan_status"
                )
            ),
            engine_id=text(
                row.get(
                    "parent_engine_id"
                )
            ),
            experiment_id="",
            hypothesis_id=text(
                row.get(
                    "hypothesis_id"
                )
            ),
            variant_id=variant_id,
            state_hash=state_hash,
            source_name=(
                "variant_implementation_planner"
            ),
            production_eligible=False,
        )

        variant_node = (
            variant_node_map.get(
                variant_id
            )
        )

        if variant_node:
            add_edge(
                edges=edges,
                source_node_id=variant_node,
                relationship_type=(
                    "AUTHORIZED_PLAN"
                ),
                target_node_id=plan_node,
                source_name=(
                    "variant_implementation_planner"
                ),
                experiment_id="",
                state_hash=state_hash,
                evidence=plan_id,
            )


def add_state_node_and_edges(
    *,
    nodes: list,
    edges: list,
    experiments: pd.DataFrame,
    state_hash: str,
) -> None:
    if not state_hash:
        return

    state_node = node_id(
        "ATLAS_STATE",
        state_hash,
    )

    add_node(
        nodes=nodes,
        node_id_value=state_node,
        node_type="ATLAS_STATE",
        natural_key=state_hash,
        label=(
            f"Atlas state {state_hash[:12]}"
        ),
        description=(
            "Canonical compiled Atlas state."
        ),
        status="COMPILED",
        engine_id="",
        experiment_id="",
        hypothesis_id="",
        variant_id="",
        state_hash=state_hash,
        source_name="atlas_compiler",
        production_eligible=False,
    )

    if (
        experiments is None
        or experiments.empty
    ):
        return

    for _, row in experiments.iterrows():
        if (
            text(
                row.get(
                    "experiment_type"
                )
            ).upper()
            != "RESEARCH_CYCLE"
        ):
            continue

        experiment_id = text(
            row.get(
                "experiment_id"
            )
        )

        cycle_node = node_id(
            "RESEARCH_CYCLE",
            text(
                row.get(
                    "natural_key"
                )
            ) or experiment_id,
        )

        add_edge(
            edges=edges,
            source_node_id=cycle_node,
            relationship_type=(
                "COMPILED_AGAINST"
            ),
            target_node_id=state_node,
            source_name=(
                "atlas_compiler"
            ),
            experiment_id=experiment_id,
            state_hash=state_hash,
            evidence=state_hash,
        )


def add_node(
    *,
    nodes: list,
    node_id_value: str,
    node_type: str,
    natural_key: str,
    label: str,
    description: str,
    status: str,
    engine_id: str,
    experiment_id: str,
    hypothesis_id: str,
    variant_id: str,
    state_hash: str,
    source_name: str,
    production_eligible: bool,
) -> None:
    nodes.append({
        "node_id": node_id_value,
        "node_type": node_type,
        "natural_key": natural_key,
        "label": label,
        "description": description,
        "status": status,
        "engine_id": engine_id,
        "experiment_id": experiment_id,
        "hypothesis_id": hypothesis_id,
        "variant_id": variant_id,
        "state_hash": state_hash,
        "source_name": source_name,
        "production_eligible": bool(
            production_eligible
        ),
        "execution_instruction": False,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
    })


def add_edge(
    *,
    edges: list,
    source_node_id: str,
    relationship_type: str,
    target_node_id: str,
    source_name: str,
    experiment_id: str,
    state_hash: str,
    evidence: str,
) -> None:
    edges.append({
        "edge_id": edge_id(
            source_node_id,
            relationship_type,
            target_node_id,
        ),
        "source_node_id": (
            source_node_id
        ),
        "relationship_type": (
            relationship_type
        ),
        "target_node_id": (
            target_node_id
        ),
        "source_name": source_name,
        "experiment_id": experiment_id,
        "state_hash": state_hash,
        "evidence": evidence,
        "execution_instruction": False,
        "schema_version": SCHEMA_VERSION,
        "source": SOURCE,
    })
