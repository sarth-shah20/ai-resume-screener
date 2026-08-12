"""Streamlit session-state helpers."""

from __future__ import annotations

from typing import Any

import streamlit as st

_DEFAULTS: dict[str, Any] = {
    "current_page": "dashboard",
    "selected_job_id": None,
    "selected_candidate_id": None,
    "latest_analysis": None,
}


def init_session_state() -> None:
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def navigate(page: str, job_id: str | None = None, candidate_id: str | None = None) -> None:
    st.session_state["current_page"] = page
    if job_id is not None:
        st.session_state["selected_job_id"] = job_id
    if candidate_id is not None:
        st.session_state["selected_candidate_id"] = candidate_id


def reset_session() -> None:
    for key in _DEFAULTS:
        st.session_state.pop(key, None)
    init_session_state()
