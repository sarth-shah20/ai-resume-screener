"""Session-state schema and helpers for the recruiter screening workflow.

This module defines the single source of truth for what the UI holds in
``st.session_state`` across the wizard-style flow (job setup -> candidate
intake -> screening -> results). Views read/write through the helpers here
rather than touching ``st.session_state`` keys directly, so the shape can
change in one place as later modules land.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

STEPS: list[dict[str, str]] = [
    {"key": "job_setup", "label": "Job Setup", "icon": "1"},
    {"key": "candidates", "label": "Candidates", "icon": "2"},
    {"key": "screening", "label": "Screening", "icon": "3"},
    {"key": "report", "label": "Results", "icon": "4"},
    {"key": "gaps", "label": "Interview Prep", "icon": "5"},
    {"key": "compare", "label": "Compare", "icon": "6"},
]

_DEFAULTS: dict[str, Any] = {
    "current_step": "job_setup",
    "job": None,
    "job_requirements": None,
    "candidates": [],
    "screening_results": [],
    "blind_review": False,
}


def init_session_state() -> None:
    """Populate any missing session-state keys with their defaults.

    Safe to call on every rerun; only fills in keys that are absent so it
    never clobbers state a view has already set.
    """
    for key, value in _DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_step(step_key: str) -> None:
    st.session_state["current_step"] = step_key


def step_status(step_key: str) -> str:
    """Return 'current', 'done', or 'upcoming' for a stepper entry.

    A step is 'done' once the data it produces exists in session state;
    this keeps the sidebar progress indicator honest even if the recruiter
    jumps around instead of following the steps in order.
    """
    completion = {
        "job_setup": bool(st.session_state.get("job_requirements")),
        "candidates": bool(st.session_state.get("candidates")),
        "screening": bool(st.session_state.get("screening_results")),
        "report": bool(st.session_state.get("screening_results")),
        "gaps": bool(st.session_state.get("screening_results")),
        "compare": len(st.session_state.get("screening_results", [])) > 1,
    }
    if st.session_state.get("current_step") == step_key:
        return "current"
    if completion.get(step_key, False):
        return "done"
    return "upcoming"


def reset_session() -> None:
    for key in list(_DEFAULTS.keys()):
        del st.session_state[key]
    init_session_state()
