"""Shared inline state panels: empty, error, and success.

Loading states are intentionally not a component here -- ``st.spinner`` /
``st.status`` are already the right primitive for that and don't benefit
from a wrapper.
"""

from __future__ import annotations

import streamlit as st


def empty_state(icon: str, title: str, description: str) -> None:
    st.markdown(
        f'<div class="state-panel">'
        f'<div class="state-icon">{icon}</div>'
        f'<div class="state-title">{title}</div>'
        f'<div class="state-desc">{description}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def error_state(message: str, details: str | None = None) -> None:
    st.error(message, icon="🚫")
    if details:
        with st.expander("Details"):
            st.code(details, language=None)


def success_state(message: str) -> None:
    st.success(message, icon="✅")
