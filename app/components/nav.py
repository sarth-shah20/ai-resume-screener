"""Sidebar navigation and backend status."""

from __future__ import annotations

import streamlit as st

from app.services.screening_client import BackendUnavailable, get_client
from app.state import navigate, reset_session


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">AI</div>'
            '<div class="brand-text"><div class="brand-title">Resume Screener</div>'
            '<div class="brand-subtitle">Evidence-first review</div></div></div>',
            unsafe_allow_html=True,
        )

        current = st.session_state["current_page"]
        if st.button(
            "▦  Dashboard",
            use_container_width=True,
            type="primary" if current == "dashboard" else "secondary",
        ):
            navigate("dashboard")
            st.rerun()
        if st.button(
            "＋  New analysis",
            use_container_width=True,
            type="primary" if current == "new_analysis" else "secondary",
        ):
            navigate("new_analysis")
            st.rerun()

        st.divider()
        try:
            health = get_client().health()
            st.success(f"Backend connected · {health['model']}", icon="✅")
        except BackendUnavailable:
            st.error("Backend unavailable", icon="🚫")
            st.caption("Start Uvicorn on the configured API URL.")

        if st.button("Reset UI session", use_container_width=True):
            reset_session()
            st.rerun()
