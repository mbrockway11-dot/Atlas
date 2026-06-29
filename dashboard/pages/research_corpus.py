"""Research Corpus / Atlas Database page."""

import pandas as pd
import streamlit as st

from atlas.database import list_entities
from atlas.library.profile_library import load_profile_interpretation

from utils.classification import load_or_build_acf_classification


def render_research_corpus_page() -> None:
    """Render Research Corpus page."""
    st.header("Research Corpus")
    st.caption("Atlas Database browser powered by atlas_library/index.json")

    entities = list_entities()

    st.metric("Indexed entities", len(entities))

    if not entities:
        st.info("No indexed entities yet. Build a profile first.")
        return

    rows = []

    for entity in entities:
        entity_id = entity["id"]
        name = entity["name"]

        try:
            interpretation = load_profile_interpretation(entity_id)
            classification = load_or_build_acf_classification(entity_id, name)

            rows.append(
                {
                    "entity_id": entity_id,
                    "name": name,
                    "entity_type": entity.get("entity_type", "unknown"),
                    "tags": ", ".join(entity.get("tags", [])),
                    "birth_confidence": entity.get("birth_confidence", "unknown"),
                    "function": classification["function"]["role"],
                    "expression": classification["expression"]["type"],
                    "state": classification["state"]["type"],
                    "scale": classification["scale"],
                    "analysis_count": interpretation["analysis_count"],
                    "strongest_driver_planet": interpretation["strongest_driver"]["planet"],
                    "strongest_driver_score": interpretation["strongest_driver"]["score"],
                    "strongest_amplifier_planet": interpretation["strongest_amplifier"]["planet"],
                    "strongest_amplifier_score": interpretation["strongest_amplifier"]["score"],
                    "strongest_regulator_planet": interpretation["strongest_regulator"]["planet"],
                    "strongest_regulator_score": interpretation["strongest_regulator"]["score"],
                    "notes": entity.get("notes") or "",
                }
            )

        except Exception as error:
            rows.append(
                {
                    "entity_id": entity_id,
                    "name": name,
                    "entity_type": entity.get("entity_type", "unknown"),
                    "tags": ", ".join(entity.get("tags", [])),
                    "birth_confidence": entity.get("birth_confidence", "unknown"),
                    "function": "missing profile",
                    "expression": "missing profile",
                    "state": "missing profile",
                    "scale": "unknown",
                    "analysis_count": None,
                    "strongest_driver_planet": "",
                    "strongest_driver_score": None,
                    "strongest_amplifier_planet": "",
                    "strongest_amplifier_score": None,
                    "strongest_regulator_planet": "",
                    "strongest_regulator_score": None,
                    "notes": f"{entity.get('notes') or ''} | Load error: {error}",
                }
            )

    df = pd.DataFrame(rows)

    st.markdown("### Filters")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        entity_types = sorted(df["entity_type"].dropna().unique().tolist())
        selected_type = st.selectbox("Entity Type", ["All"] + entity_types)

    with c2:
        functions = sorted(df["function"].dropna().unique().tolist())
        selected_function = st.selectbox("Function", ["All"] + functions)

    with c3:
        expressions = sorted(df["expression"].dropna().unique().tolist())
        selected_expression = st.selectbox("Expression", ["All"] + expressions)

    with c4:
        states = sorted(df["state"].dropna().unique().tolist())
        selected_state = st.selectbox("State", ["All"] + states)

    search = st.text_input("Search name, tag, notes, or entity ID")

    filtered = df.copy()

    if selected_type != "All":
        filtered = filtered[filtered["entity_type"] == selected_type]

    if selected_function != "All":
        filtered = filtered[filtered["function"] == selected_function]

    if selected_expression != "All":
        filtered = filtered[filtered["expression"] == selected_expression]

    if selected_state != "All":
        filtered = filtered[filtered["state"] == selected_state]

    if search.strip():
        query = search.strip().lower()
        filtered = filtered[
            filtered.apply(
                lambda row: query in " ".join(
                    [
                        str(row.get("entity_id", "")),
                        str(row.get("name", "")),
                        str(row.get("tags", "")),
                        str(row.get("notes", "")),
                    ]
                ).lower(),
                axis=1,
            )
        ]

    st.markdown("### Results")
    st.dataframe(filtered, use_container_width=True)

    st.markdown("### Raw Database View")
    with st.expander("Show full index-derived table"):
        st.dataframe(df, use_container_width=True)