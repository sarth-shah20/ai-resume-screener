"""Sidebar brand mark and step-progress navigation."""

from __future__ import annotations

import streamlit as st

from app.state import STEPS, go_to_step, reset_session, step_status


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            '<div class="brand">'
            '<div class="brand-mark">AI</div>'
            '<div class="brand-text">'
            '<div class="brand-title">Resume Screener</div>'
            '<div class="brand-subtitle">Evidence-first candidate review</div>'
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        for step in STEPS:
            status = step_status(step["key"])
            marker = "✓" if status == "done" else step["icon"]
            clicked = st.button(
                f"{marker}  {step['label']}",
                key=f"nav_{step['key']}",
                use_container_width=True,
                type="primary" if status == "current" else "secondary",
            )
            if clicked:
                go_to_step(step["key"])
                st.rerun()

        st.divider()

        if st.session_state.get("blind_review"):
            st.markdown(
                '<span class="badge badge-primary">&#128065; Blind Review ON</span>',
                unsafe_allow_html=True,
            )

        if st.button("Reset session", use_container_width=True):
            reset_session()
            st.rerun()
