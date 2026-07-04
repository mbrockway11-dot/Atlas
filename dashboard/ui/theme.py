"""Atlas dashboard theme helpers."""

from __future__ import annotations

import streamlit as st


def apply_atlas_theme() -> None:
    """Apply shared Atlas dashboard styling."""
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 4rem;
            max-width: 1200px;
        }

        [data-testid="stMetric"] {
            background: rgba(250, 250, 250, 0.04);
            border: 1px solid rgba(128, 128, 128, 0.18);
            padding: 0.85rem;
            border-radius: 0.85rem;
        }

        [data-testid="stExpander"] {
            border-radius: 0.85rem;
        }

        h1, h2, h3 {
            letter-spacing: -0.03em;
        }

        .atlas-muted {
            opacity: 0.72;
            font-size: 0.95rem;
        }

        .atlas-small {
            opacity: 0.65;
            font-size: 0.85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def atlas_caption(text: str) -> None:
    """Render muted Atlas caption."""
    st.markdown(f'<div class="atlas-muted">{text}</div>', unsafe_allow_html=True)


def atlas_small(text: str) -> None:
    """Render small muted text."""
    st.markdown(f'<div class="atlas-small">{text}</div>', unsafe_allow_html=True)
